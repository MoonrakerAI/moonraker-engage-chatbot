"""
GoHighLevel MCP client with security abstraction layer.
Therapists never see GHL interface - only therapy-focused data.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel

from ..core.config import settings
from ..core.security import audit_logger, patient_encryption
from ..models.patient import PatientResponse, SessionStatus
from ..models.therapist import GHLCredentials, TherapistResponse


class MCPError(Exception):
    """Custom exception for MCP operations."""
    pass


class GHLContact(BaseModel):
    """GoHighLevel contact abstracted for therapy use."""
    ghl_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class GHLAppointment(BaseModel):
    """GoHighLevel appointment abstracted for therapy use."""
    ghl_id: str
    contact_id: str
    calendar_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: SessionStatus
    location: Optional[str] = None
    notes: Optional[str] = None


class GHLMessage(BaseModel):
    """GoHighLevel message abstracted for therapy use."""
    ghl_id: str
    contact_id: str
    conversation_id: str
    message_type: str  # sms, email, call
    body: str
    direction: str  # inbound, outbound
    timestamp: datetime
    status: str  # delivered, read, failed


class TherapyFocusedMCPClient:
    """MCP client that abstracts GHL complexity for therapists."""
    
    def __init__(self, credentials: Optional[GHLCredentials] = None):
        """Initialize MCP client with optional credentials."""
        self.base_url = settings.ghl_mcp_server_url
        self.credentials = credentials
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Therapy-focused field mappings (hide CRM complexity)
        self.therapy_field_mapping = {
            "patient_preferred_name": "customField.preferred_name",
            "emergency_contact": "customField.emergency_contact",
            "diagnosis": "customField.primary_diagnosis",
            "medication_list": "customField.current_medications",
            "therapy_goals": "customField.therapy_goals",
            "session_frequency": "customField.session_frequency",
            "insurance_info": "customField.insurance_provider",
            "consent_status": "customField.hipaa_consent_status",
            "risk_level": "customField.risk_assessment",
            "therapist_notes": "customField.private_notes"
        }
    
    async def _make_mcp_request(
        self, 
        method: str, 
        tool_name: str, 
        arguments: Dict[str, Any],
        therapist_id: str,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make authenticated MCP request with audit logging."""
        
        # Log the request
        await audit_logger.log_access(
            user_id=therapist_id,
            patient_id=patient_id,
            action=f"ghl_mcp_{tool_name}",
            resource="ghl_api",
            outcome="started"
        )
        
        try:
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": f"req_{datetime.utcnow().timestamp()}",
                "method": method,
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Add authentication if credentials provided
            if self.credentials:
                mcp_request["params"]["arguments"]["authorization"] = f"Bearer {self.credentials.api_key}"
                mcp_request["params"]["arguments"]["locationId"] = self.credentials.location_id
            
            # Make request to MCP server
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise MCPError(f"MCP request failed: {response.status_code}")
            
            result = response.json()
            
            if "error" in result:
                raise MCPError(f"MCP error: {result['error']}")
            
            # Log successful request
            await audit_logger.log_access(
                user_id=therapist_id,
                patient_id=patient_id,
                action=f"ghl_mcp_{tool_name}",
                resource="ghl_api",
                outcome="success"
            )
            
            return result.get("result", {})
            
        except Exception as e:
            # Log failed request
            await audit_logger.log_access(
                user_id=therapist_id,
                patient_id=patient_id,
                action=f"ghl_mcp_{tool_name}",
                resource="ghl_api",
                outcome="failure",
                details={"error": str(e)}
            )
            raise MCPError(f"MCP request failed: {str(e)}")
    
    async def create_patient_contact(
        self, 
        therapist_id: str,
        patient_data: Dict[str, Any]
    ) -> GHLContact:
        """Create new patient contact in GHL (therapy-focused interface)."""
        
        # Transform therapy data to GHL format
        ghl_contact_data = {
            "firstName": patient_data.get("first_name", ""),
            "lastName": patient_data.get("last_name", ""),
            "email": patient_data.get("email"),
            "phone": patient_data.get("phone"),
            "tags": ["therapy_patient", "hipaa_compliant"],
            "customFields": {}
        }
        
        # Map therapy-specific fields
        for therapy_field, ghl_field in self.therapy_field_mapping.items():
            if therapy_field in patient_data:
                if ghl_field.startswith("customField."):
                    field_name = ghl_field.replace("customField.", "")
                    ghl_contact_data["customFields"][field_name] = patient_data[therapy_field]
        
        # Create contact via MCP
        result = await self._make_mcp_request(
            method="tools/call",
            tool_name="contacts_create",
            arguments=ghl_contact_data,
            therapist_id=therapist_id
        )
        
        # Transform result back to therapy-focused format
        contact_data = result.get("contact", {})
        return GHLContact(
            ghl_id=contact_data["id"],
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            first_name=contact_data.get("firstName"),
            last_name=contact_data.get("lastName"),
            tags=contact_data.get("tags", []),
            custom_fields=contact_data.get("customFields", {}),
            created_at=datetime.fromisoformat(contact_data["dateAdded"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(contact_data["dateUpdated"].replace("Z", "+00:00"))
        )
    
    async def get_patient_contact(
        self, 
        therapist_id: str, 
        ghl_contact_id: str
    ) -> Optional[GHLContact]:
        """Get patient contact from GHL."""
        
        try:
            result = await self._make_mcp_request(
                method="tools/call",
                tool_name="contacts_get",
                arguments={"contactId": ghl_contact_id},
                therapist_id=therapist_id,
                patient_id=ghl_contact_id
            )
            
            contact_data = result.get("contact", {})
            if not contact_data:
                return None
            
            return GHLContact(
                ghl_id=contact_data["id"],
                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                first_name=contact_data.get("firstName"),
                last_name=contact_data.get("lastName"),
                tags=contact_data.get("tags", []),
                custom_fields=contact_data.get("customFields", {}),
                created_at=datetime.fromisoformat(contact_data["dateAdded"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(contact_data["dateUpdated"].replace("Z", "+00:00"))
            )
            
        except MCPError:
            return None
    
    async def schedule_therapy_session(
        self,
        therapist_id: str,
        patient_contact_id: str,
        session_data: Dict[str, Any]
    ) -> GHLAppointment:
        """Schedule therapy session (abstracted from GHL calendar complexity)."""
        
        # Find or create therapy calendar
        calendar_id = await self._ensure_therapy_calendar(therapist_id)
        
        # Create appointment via MCP
        appointment_data = {
            "calendarId": calendar_id,
            "contactId": patient_contact_id,
            "title": session_data.get("title", "Therapy Session"),
            "description": session_data.get("description", "Individual therapy session"),
            "startTime": session_data["start_time"].isoformat(),
            "endTime": session_data["end_time"].isoformat(),
            "appointmentStatus": "confirmed"
        }
        
        result = await self._make_mcp_request(
            method="tools/call",
            tool_name="calendars_create_appointment",
            arguments=appointment_data,
            therapist_id=therapist_id,
            patient_id=patient_contact_id
        )
        
        # Transform to therapy-focused format
        appointment = result.get("appointment", {})
        return GHLAppointment(
            ghl_id=appointment["id"],
            contact_id=patient_contact_id,
            calendar_id=calendar_id,
            title=appointment["title"],
            description=appointment.get("description"),
            start_time=datetime.fromisoformat(appointment["startTime"].replace("Z", "+00:00")),
            end_time=datetime.fromisoformat(appointment["endTime"].replace("Z", "+00:00")),
            status=SessionStatus.SCHEDULED,
            location=appointment.get("location"),
            notes=appointment.get("notes")
        )
    
    async def send_therapeutic_message(
        self,
        therapist_id: str,
        patient_contact_id: str,
        message: str,
        message_type: str = "sms"
    ) -> GHLMessage:
        """Send message to patient (therapy-focused, not marketing)."""
        
        # Prepare message data
        message_data = {
            "contactId": patient_contact_id,
            "message": message,
            "type": message_type
        }
        
        # Add therapy-specific metadata
        if message_type == "sms":
            tool_name = "conversations_send_sms"
        elif message_type == "email":
            tool_name = "conversations_send_email"
            message_data["subject"] = "Message from your therapist"
        else:
            raise MCPError(f"Unsupported message type: {message_type}")
        
        result = await self._make_mcp_request(
            method="tools/call",
            tool_name=tool_name,
            arguments=message_data,
            therapist_id=therapist_id,
            patient_id=patient_contact_id
        )
        
        # Transform result
        message_result = result.get("message", {})
        return GHLMessage(
            ghl_id=message_result["id"],
            contact_id=patient_contact_id,
            conversation_id=message_result.get("conversationId", ""),
            message_type=message_type,
            body=message,
            direction="outbound",
            timestamp=datetime.utcnow(),
            status=message_result.get("status", "sent")
        )
    
    async def get_patient_messages(
        self,
        therapist_id: str,
        patient_contact_id: str,
        limit: int = 50
    ) -> List[GHLMessage]:
        """Get patient message history (therapy-focused view)."""
        
        result = await self._make_mcp_request(
            method="tools/call",
            tool_name="conversations_get_messages",
            arguments={
                "contactId": patient_contact_id,
                "limit": limit
            },
            therapist_id=therapist_id,
            patient_id=patient_contact_id
        )
        
        messages = []
        for msg_data in result.get("messages", []):
            messages.append(GHLMessage(
                ghl_id=msg_data["id"],
                contact_id=patient_contact_id,
                conversation_id=msg_data.get("conversationId", ""),
                message_type=msg_data.get("type", "sms"),
                body=msg_data.get("body", ""),
                direction=msg_data.get("direction", "inbound"),
                timestamp=datetime.fromisoformat(msg_data["dateAdded"].replace("Z", "+00:00")),
                status=msg_data.get("status", "delivered")
            ))
        
        return messages
    
    async def update_patient_therapy_data(
        self,
        therapist_id: str,
        patient_contact_id: str,
        therapy_updates: Dict[str, Any]
    ) -> GHLContact:
        """Update patient therapy-specific data."""
        
        # Transform therapy updates to GHL format
        ghl_updates = {
            "contactId": patient_contact_id,
            "customFields": {}
        }
        
        # Map therapy fields to GHL custom fields
        for therapy_field, value in therapy_updates.items():
            if therapy_field in self.therapy_field_mapping:
                ghl_field = self.therapy_field_mapping[therapy_field]
                if ghl_field.startswith("customField."):
                    field_name = ghl_field.replace("customField.", "")
                    ghl_updates["customFields"][field_name] = value
        
        result = await self._make_mcp_request(
            method="tools/call",
            tool_name="contacts_update",
            arguments=ghl_updates,
            therapist_id=therapist_id,
            patient_id=patient_contact_id
        )
        
        # Return updated contact
        return await self.get_patient_contact(therapist_id, patient_contact_id)
    
    async def _ensure_therapy_calendar(self, therapist_id: str) -> str:
        """Ensure therapy calendar exists for therapist."""
        
        # Get existing calendars
        result = await self._make_mcp_request(
            method="tools/call",
            tool_name="calendars_list",
            arguments={},
            therapist_id=therapist_id
        )
        
        # Look for existing therapy calendar
        calendars = result.get("calendars", [])
        for calendar in calendars:
            if calendar.get("name") == "Therapy Sessions":
                return calendar["id"]
        
        # Create therapy calendar if it doesn't exist
        calendar_data = {
            "name": "Therapy Sessions",
            "description": "Calendar for individual therapy sessions",
            "eventTitle": "Therapy Session",
            "eventColor": "#2196F3",
            "slotDuration": 50,  # Standard therapy session length
            "slotInterval": 60,  # 1-hour slots
            "slotBuffer": 10    # 10-minute buffer
        }
        
        create_result = await self._make_mcp_request(
            method="tools/call",
            tool_name="calendars_create",
            arguments=calendar_data,
            therapist_id=therapist_id
        )
        
        return create_result.get("calendar", {}).get("id")
    
    async def get_therapist_dashboard_data(self, therapist_id: str) -> Dict[str, Any]:
        """Get therapy-focused dashboard data (not CRM metrics)."""
        
        # This would aggregate data from multiple MCP calls
        # but present it in therapy-focused format
        
        try:
            # Get patient contacts
            contacts_result = await self._make_mcp_request(
                method="tools/call",
                tool_name="contacts_search",
                arguments={
                    "query": "",
                    "tags": ["therapy_patient"],
                    "limit": 100
                },
                therapist_id=therapist_id
            )
            
            # Get today's appointments
            today = datetime.now().date()
            appointments_result = await self._make_mcp_request(
                method="tools/call",
                tool_name="calendars_get_events",
                arguments={
                    "startDate": today.isoformat(),
                    "endDate": today.isoformat()
                },
                therapist_id=therapist_id
            )
            
            # Process data for therapy dashboard
            active_patients = len(contacts_result.get("contacts", []))
            today_sessions = len(appointments_result.get("events", []))
            
            return {
                "active_patients": active_patients,
                "todays_sessions": today_sessions,
                "pending_messages": 0,  # Would calculate from conversations
                "crisis_alerts": 0,     # Would come from our internal system
                "dashboard_type": "therapy_focused",  # Not "crm_focused"
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Return safe defaults on error
            return {
                "active_patients": 0,
                "todays_sessions": 0,
                "pending_messages": 0,
                "crisis_alerts": 0,
                "dashboard_type": "therapy_focused",
                "last_updated": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Factory function to create MCP client with therapist credentials
async def create_therapist_mcp_client(therapist: TherapistResponse) -> TherapyFocusedMCPClient:
    """Create MCP client with therapist's encrypted GHL credentials."""
    
    # This would decrypt the therapist's stored GHL credentials
    # For now, we'll use the global settings
    credentials = GHLCredentials(
        api_key=settings.ghl_api_key,
        location_id=settings.ghl_location_id
    )
    
    return TherapyFocusedMCPClient(credentials)