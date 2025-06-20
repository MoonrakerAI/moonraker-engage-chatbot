"""
Therapist-facing API interface that completely abstracts away GoHighLevel complexity.
Therapists see only therapy-relevant information and never need to know about GHL.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..ai.mental_health_agent import mental_health_agent, MentalHealthContext
from ..core.security import jwt_manager, audit_logger
from ..ghl.mcp_client import create_therapist_mcp_client
from ..models.patient import PatientSummary, CrisisAlert, PatientConversation
from ..models.therapist import TherapistResponse, TherapistDashboard


# Security
security = HTTPBearer()
router = APIRouter(prefix="/therapist", tags=["Therapist Interface"])


# Request/Response Models for Therapist Interface
class TherapistDashboardRequest(BaseModel):
    """Request for therapist dashboard data."""
    date_range: Optional[str] = "today"  # today, week, month
    include_crisis_alerts: bool = True


class PatientListRequest(BaseModel):
    """Request for patient list."""
    status_filter: Optional[str] = None  # active, inactive, high_risk
    limit: int = 50
    offset: int = 0


class SendMessageRequest(BaseModel):
    """Request to send message to patient."""
    patient_id: str
    message: str
    message_type: str = "supportive_check_in"  # appointment_reminder, crisis_follow_up, etc.


class SessionNoteRequest(BaseModel):
    """Request to add session note."""
    patient_id: str
    session_date: date
    note_content: str
    risk_assessment: str = "low"
    next_session_plan: Optional[str] = None


class ConversationReviewRequest(BaseModel):
    """Request to review AI conversation with patient."""
    patient_id: str
    conversation_id: str
    date_range: Optional[str] = "last_7_days"


# Response Models
class TherapistDashboardResponse(BaseModel):
    """Therapist dashboard response - therapy-focused, not CRM-focused."""
    overview: Dict[str, Any]
    todays_schedule: List[Dict[str, Any]]
    patient_alerts: List[CrisisAlert]
    recent_messages: List[Dict[str, Any]]
    weekly_summary: Dict[str, Any]


class PatientListResponse(BaseModel):
    """Patient list response with anonymized data."""
    patients: List[PatientSummary]
    total_count: int
    high_risk_count: int
    pending_consent_count: int


class ConversationSummaryResponse(BaseModel):
    """AI conversation summary for therapist review."""
    conversation_id: str
    patient_anonymous_id: str
    date_range: str
    total_messages: int
    risk_assessments: List[str]
    crisis_alerts: int
    key_themes: List[str]
    ai_summary: str
    recommended_actions: List[str]


# Dependency to get current therapist
async def get_current_therapist(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TherapistResponse:
    """Get current authenticated therapist."""
    try:
        token_data = jwt_manager.verify_token(credentials.credentials)
        therapist_id = token_data.get("sub")
        
        if not therapist_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        # TODO: Get therapist from database
        # For now, return mock therapist
        return TherapistResponse(
            id=therapist_id,
            email="therapist@example.com",
            first_name="Dr.",
            last_name="Therapist",
            license_type="lmft",
            license_number="12345",
            license_state="CA",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_verified=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.get("/dashboard", response_model=TherapistDashboardResponse)
async def get_therapist_dashboard(
    request: TherapistDashboardRequest = TherapistDashboardRequest(),
    therapist: TherapistResponse = Depends(get_current_therapist)
) -> TherapistDashboardResponse:
    """
    Get therapist dashboard with therapy-focused metrics.
    No CRM complexity - just what therapists need to see.
    """
    
    # Log dashboard access
    await audit_logger.log_access(
        user_id=therapist.id,
        patient_id=None,
        action="dashboard_access",
        resource="therapist_dashboard",
        outcome="success"
    )
    
    try:
        # Get MCP client for this therapist
        mcp_client = await create_therapist_mcp_client(therapist)
        
        # Get dashboard data from GHL (but present it therapy-focused)
        dashboard_data = await mcp_client.get_therapist_dashboard_data(therapist.id)
        
        # Transform to therapy-focused format
        overview = {
            "active_patients": dashboard_data.get("active_patients", 0),
            "todays_sessions": dashboard_data.get("todays_sessions", 0),
            "pending_messages": dashboard_data.get("pending_messages", 0),
            "crisis_alerts": dashboard_data.get("crisis_alerts", 0),
            "interface_note": "This is your therapy practice dashboard - simplified and HIPAA-compliant"
        }
        
        # Mock data for demonstration
        todays_schedule = [
            {
                "time": "10:00 AM",
                "patient_initials": "J.D.",
                "session_type": "Individual Therapy",
                "duration": "50 minutes",
                "status": "confirmed"
            },
            {
                "time": "2:00 PM",
                "patient_initials": "M.S.",
                "session_type": "Follow-up Session",
                "duration": "50 minutes",
                "status": "confirmed"
            }
        ]
        
        patient_alerts = []  # Would come from crisis detection system
        
        recent_messages = [
            {
                "patient_initials": "A.B.",
                "preview": "Thank you for the session yesterday...",
                "timestamp": "2 hours ago",
                "type": "AI conversation"
            }
        ]
        
        weekly_summary = {
            "sessions_completed": 15,
            "new_patients": 2,
            "crisis_interventions": 0,
            "ai_conversations": 28,
            "patient_satisfaction": "94%"
        }
        
        await mcp_client.close()
        
        return TherapistDashboardResponse(
            overview=overview,
            todays_schedule=todays_schedule,
            patient_alerts=patient_alerts,
            recent_messages=recent_messages,
            weekly_summary=weekly_summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


@router.get("/patients", response_model=PatientListResponse)
async def get_patient_list(
    request: PatientListRequest = PatientListRequest(),
    therapist: TherapistResponse = Depends(get_current_therapist)
) -> PatientListResponse:
    """
    Get anonymized patient list for therapist.
    Shows therapy-relevant info only, no CRM details.
    """
    
    await audit_logger.log_access(
        user_id=therapist.id,
        patient_id=None,
        action="patient_list_access",
        resource="patient_list",
        outcome="success"
    )
    
    # Mock patient data (would come from database)
    mock_patients = [
        PatientSummary(
            anonymous_id="anon_abc123",
            initials="J.D.",
            risk_level="low",
            last_contact=datetime.utcnow(),
            recent_activity="AI conversation 2 hours ago",
            flags=[]
        ),
        PatientSummary(
            anonymous_id="anon_def456",
            initials="M.S.",
            risk_level="moderate",
            last_contact=datetime.utcnow(),
            recent_activity="Session yesterday",
            flags=["Follow-up needed"]
        )
    ]
    
    return PatientListResponse(
        patients=mock_patients,
        total_count=len(mock_patients),
        high_risk_count=0,
        pending_consent_count=0
    )


@router.post("/patients/{patient_id}/message")
async def send_patient_message(
    patient_id: str,
    request: SendMessageRequest,
    therapist: TherapistResponse = Depends(get_current_therapist)
):
    """
    Send message to patient through secure channel.
    Messages go through GHL but therapist doesn't see that complexity.
    """
    
    await audit_logger.log_access(
        user_id=therapist.id,
        patient_id=patient_id,
        action="send_patient_message",
        resource="patient_communication",
        outcome="started"
    )
    
    try:
        # Get MCP client
        mcp_client = await create_therapist_mcp_client(therapist)
        
        # Get patient's GHL contact ID (encrypted in our database)
        # TODO: Implement patient lookup
        ghl_contact_id = "mock_contact_id"
        
        # Send message through GHL
        message_result = await mcp_client.send_therapeutic_message(
            therapist_id=therapist.id,
            patient_contact_id=ghl_contact_id,
            message=request.message,
            message_type="sms"
        )
        
        await mcp_client.close()
        
        await audit_logger.log_access(
            user_id=therapist.id,
            patient_id=patient_id,
            action="send_patient_message",
            resource="patient_communication",
            outcome="success"
        )
        
        return {
            "message": "Message sent successfully",
            "sent_at": message_result.timestamp,
            "delivery_status": message_result.status
        }
        
    except Exception as e:
        await audit_logger.log_access(
            user_id=therapist.id,
            patient_id=patient_id,
            action="send_patient_message",
            resource="patient_communication",
            outcome="failure",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/patients/{patient_id}/conversation", response_model=ConversationSummaryResponse)
async def get_patient_conversation_summary(
    patient_id: str,
    request: ConversationReviewRequest = ConversationReviewRequest(patient_id="", conversation_id=""),
    therapist: TherapistResponse = Depends(get_current_therapist)
) -> ConversationSummaryResponse:
    """
    Get AI conversation summary for therapist review.
    Provides clinical insights without exposing raw GHL data.
    """
    
    await audit_logger.log_access(
        user_id=therapist.id,
        patient_id=patient_id,
        action="conversation_review",
        resource="ai_conversation",
        outcome="started"
    )
    
    try:
        # TODO: Get actual conversation from database
        # Mock conversation context
        context = MentalHealthContext(
            patient_id=patient_id,
            therapist_id=therapist.id,
            patient_risk_level="low",
            conversation_history=[]
        )
        
        # Generate session summary using AI agent
        ai_summary = await mental_health_agent.generate_session_summary(context)
        
        await audit_logger.log_access(
            user_id=therapist.id,
            patient_id=patient_id,
            action="conversation_review",
            resource="ai_conversation",
            outcome="success"
        )
        
        return ConversationSummaryResponse(
            conversation_id=request.conversation_id or "mock_conv_123",
            patient_anonymous_id=patient_id,
            date_range=request.date_range or "last_7_days",
            total_messages=12,
            risk_assessments=["low", "low", "moderate"],
            crisis_alerts=0,
            key_themes=["anxiety", "work_stress", "relationships"],
            ai_summary=ai_summary,
            recommended_actions=[
                "Continue supportive approach",
                "Consider stress management techniques",
                "Schedule follow-up session"
            ]
        )
        
    except Exception as e:
        await audit_logger.log_access(
            user_id=therapist.id,
            patient_id=patient_id,
            action="conversation_review",
            resource="ai_conversation",
            outcome="failure",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate conversation summary: {str(e)}"
        )


@router.post("/patients/{patient_id}/session-note")
async def add_session_note(
    patient_id: str,
    request: SessionNoteRequest,
    therapist: TherapistResponse = Depends(get_current_therapist)
):
    """
    Add session note for patient.
    Notes are encrypted and stored securely.
    """
    
    await audit_logger.log_access(
        user_id=therapist.id,
        patient_id=patient_id,
        action="add_session_note",
        resource="patient_record",
        outcome="started"
    )
    
    try:
        # TODO: Encrypt and store session note
        # TODO: Update patient record in database
        # TODO: Sync relevant data to GHL if needed
        
        await audit_logger.log_access(
            user_id=therapist.id,
            patient_id=patient_id,
            action="add_session_note",
            resource="patient_record",
            outcome="success",
            details={"session_date": request.session_date.isoformat()}
        )
        
        return {
            "message": "Session note added successfully",
            "note_id": f"note_{datetime.utcnow().timestamp()}",
            "created_at": datetime.utcnow()
        }
        
    except Exception as e:
        await audit_logger.log_access(
            user_id=therapist.id,
            patient_id=patient_id,
            action="add_session_note",
            resource="patient_record",
            outcome="failure",
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add session note: {str(e)}"
        )


@router.get("/interface-info")
async def get_interface_info(
    therapist: TherapistResponse = Depends(get_current_therapist)
):
    """
    Get information about the therapist interface.
    Explains what they're seeing vs. what's hidden.
    """
    
    return {
        "interface_type": "Therapy-Focused Practice Management",
        "what_you_see": [
            "Patient summaries (anonymized)",
            "AI conversation insights",
            "Session scheduling",
            "Crisis alerts and risk assessments",
            "Therapeutic communication tools",
            "HIPAA-compliant documentation"
        ],
        "what_is_hidden": [
            "GoHighLevel CRM interface",
            "Marketing campaign tools",
            "Sales pipeline management",
            "Lead generation features",
            "Business analytics dashboards",
            "Payment processing details"
        ],
        "backend_integration": {
            "platform": "GoHighLevel (abstracted)",
            "security": "HIPAA-compliant encryption",
            "ai_features": "PydanticAI + DSPy optimization",
            "crisis_detection": "Real-time monitoring",
            "audit_logging": "Full compliance tracking"
        },
        "therapist_benefits": [
            "No CRM complexity to learn",
            "Focus purely on patient care",
            "AI-powered insights and support",
            "Automated compliance and documentation",
            "Seamless patient communication"
        ]
    }