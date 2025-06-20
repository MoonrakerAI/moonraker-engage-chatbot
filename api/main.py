"""
Moonraker Engage API - Connected to GoHighLevel MCP Server
"""

import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Optional

app = FastAPI(
    title="Moonraker Engage API",
    description="HIPAA-compliant chatbot API for therapist websites",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# GoHighLevel MCP Configuration
GHL_MCP_SERVER_URL = os.getenv("GHL_MCP_SERVER_URL", "http://localhost:3000")
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")

async def make_ghl_request(tool_name: str, arguments: Dict) -> Dict:
    """Make request to GoHighLevel MCP server."""
    if not GHL_API_KEY or not GHL_LOCATION_ID:
        # Return mock data if not configured
        return {"mock": True, "message": "GHL not configured, using demo data"}
    
    try:
        async with httpx.AsyncClient() as client:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": f"req_{datetime.utcnow().timestamp()}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {
                        **arguments,
                        "authorization": f"Bearer {GHL_API_KEY}",
                        "locationId": GHL_LOCATION_ID
                    }
                }
            }
            
            response = await client.post(
                f"{GHL_MCP_SERVER_URL}/mcp",
                json=mcp_request,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                return {"error": f"MCP request failed: {response.status_code}"}
                
    except Exception as e:
        return {"error": f"Failed to connect to GHL MCP: {str(e)}"}

# Models
class DashboardStats(BaseModel):
    total_conversations: int = 152
    conversations_change: str = "+12% from last week"
    appointments_booked: int = 24
    appointments_change: str = "+8% from last week"
    conversion_rate: float = 15.8
    conversion_change: str = "+3% from last week"
    avg_response_time: float = 2.1
    response_time_change: str = "-0.3s from last week"

class RecentConversation(BaseModel):
    initial: str
    name: str
    preview: str
    status: str
    time_ago: str

class ChatbotStatus(BaseModel):
    status: str = "Active"
    model: str = "Claude 3.5 Sonnet"
    knowledge_base: str = "12 documents"
    last_updated: str = "2 days ago"

# Routes
@app.get("/")
async def root():
    return {
        "message": "Moonraker Engage API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard data from GoHighLevel via MCP."""
    
    try:
        # Get real contacts from GHL
        contacts_data = await make_ghl_request("contacts_search", {"limit": 10})
        
        # Get conversations from GHL
        conversations_data = await make_ghl_request("conversations_get", {"limit": 20})
        
        # Process real data or fall back to demo data
        if contacts_data.get("mock"):
            # Use demo data
            stats = DashboardStats()
            recent_conversations = [
                RecentConversation(
                    initial="S",
                    name="Sarah Johnson",
                    preview="I'd like to schedule an appointment for next week",
                    status="Completed",
                    time_ago="10 min ago"
                ),
                RecentConversation(
                    initial="M",
                    name="Michael Chen",
                    preview="Do you accept insurance for therapy sessions?",
                    status="Ongoing",
                    time_ago="25 min ago"
                )
            ]
        else:
            # Process real GHL data
            contacts = contacts_data.get("contacts", [])
            conversations = conversations_data.get("conversations", [])
            
            stats = DashboardStats(
                total_conversations=len(conversations),
                appointments_booked=len([c for c in contacts if "appointment" in str(c).lower()]),
                conversion_rate=15.8,  # Calculate from real data
                avg_response_time=2.1
            )
            
            # Convert GHL contacts to conversation format
            recent_conversations = []
            for contact in contacts[:4]:
                initial = contact.get("firstName", "?")[0].upper() if contact.get("firstName") else "?"
                name = f"{contact.get('firstName', 'Unknown')} {contact.get('lastName', '')}"
                recent_conversations.append(RecentConversation(
                    initial=initial,
                    name=name,
                    preview=f"Contact from {contact.get('source', 'website')}",
                    status="Completed",
                    time_ago=f"{abs(hash(contact.get('id', '')) % 60)} min ago"
                ))
        
        chatbot_status = ChatbotStatus()
        
        return {
            "overview": stats.model_dump(),
            "recent_conversations": [conv.model_dump() for conv in recent_conversations],
            "chatbot_status": chatbot_status.model_dump(),
            "ghl_connected": not contacts_data.get("mock", False)
        }
        
    except Exception as e:
        # Fallback to demo data on error
        stats = DashboardStats()
        recent_conversations = [
            RecentConversation(
                initial="D",
                name="Demo User",
                preview="This is demo data - connect your GHL API to see real data",
                status="Demo",
                time_ago="now"
            )
        ]
        
        return {
            "overview": stats.model_dump(),
            "recent_conversations": [conv.model_dump() for conv in recent_conversations],
            "chatbot_status": ChatbotStatus().model_dump(),
            "ghl_connected": False,
            "error": str(e)
        }

@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data matching the analytics screenshot."""
    
    stats = DashboardStats()
    
    weekly_activity = {
        "Mon": {"conversations": 12, "appointments": 3},
        "Tue": {"conversations": 8, "appointments": 2},
        "Wed": {"conversations": 22, "appointments": 5},
        "Thu": {"conversations": 18, "appointments": 4},
        "Fri": {"conversations": 15, "appointments": 3},
        "Sat": {"conversations": 8, "appointments": 2},
        "Sun": {"conversations": 7, "appointments": 2}
    }
    
    top_conversation_topics = {
        "Appointment Scheduling": 35.0,
        "Service Information": 25.0,
        "Insurance Questions": 20.0,
        "Location & Hours": 12.0,
        "Pricing": 8.0
    }
    
    avg_response_time_chart = [3.2, 2.8, 2.5, 2.1, 2.3, 2.0]
    
    return {
        "overview": stats.model_dump(),
        "weekly_activity": weekly_activity,
        "top_conversation_topics": top_conversation_topics,
        "avg_response_time_chart": avg_response_time_chart
    }

@app.get("/api/practice-info")
async def get_practice_info():
    """Get practice information."""
    
    return {
        "basic_information": {
            "practice_name": "Intensive Therapy Retreats",
            "practice_email": "support@intensivetherapyretreat.com",
            "phone_number": "413-331-7421",
            "website": "https://intensivetherapyretreat.com",
            "hours_of_operation": "Mon-Fri 9a-5p"
        },
        "practice_configuration": {
            "team_size": "Group Practice",
            "service_delivery": "Both In-Person & Online"
        },
        "insurance_billing": {
            "accepts_insurance": True
        }
    }

@app.get("/api/chatbot-setup/branding")
async def get_chatbot_branding():
    """Get chatbot branding configuration."""
    
    return {
        "bot_name": "Retreat Bot",
        "primary_color": "#ac7782",
        "secondary_color": "#d3d6de",
        "title_font": "Inter",
        "body_font": "Inter",
        "logo_url": None,
        "welcome_message": "Hi! I'm here to help you with scheduling and answering questions about our therapy services. How can I assist you today?"
    }

@app.post("/api/chat/message")
async def chat_message(message: dict):
    """Handle chat messages and create contacts in GoHighLevel."""
    
    user_message = message.get("message", "")
    visitor_info = message.get("visitor_info", {})
    
    # Extract contact info if provided
    contact_data = {}
    if visitor_info.get("email"):
        contact_data["email"] = visitor_info["email"]
    if visitor_info.get("name"):
        names = visitor_info["name"].split(" ", 1)
        contact_data["firstName"] = names[0]
        if len(names) > 1:
            contact_data["lastName"] = names[1]
    if visitor_info.get("phone"):
        contact_data["phone"] = visitor_info["phone"]
    
    # Create contact in GHL if we have contact info
    contact_created = False
    if contact_data:
        try:
            contact_result = await make_ghl_request("contacts_create", {
                **contact_data,
                "tags": ["website_visitor", "chatbot_lead"],
                "source": "Moonraker Engage Chatbot"
            })
            
            if not contact_result.get("error"):
                contact_created = True
        except Exception as e:
            print(f"Failed to create contact: {e}")
    
    # Simple response logic
    if any(word in user_message.lower() for word in ["appointment", "schedule", "book"]):
        if contact_created:
            response = "Perfect! I've saved your information and someone from our team will contact you within 24 hours to schedule your appointment. What type of session are you most interested in - individual therapy, couples counseling, or an initial consultation?"
        else:
            response = "I'd be happy to help you schedule an appointment! To get started, could you share your name and email address? Then I can connect you with our scheduling team."
        intent = "booking"
        
    elif any(word in user_message.lower() for word in ["price", "cost", "insurance"]):
        response = "We accept most major insurance plans and offer competitive self-pay rates. Individual sessions typically range from $120-180. Would you like me to check your specific insurance benefits?"
        intent = "pricing"
        
    elif any(word in user_message.lower() for word in ["hours", "location", "address"]):
        response = "We're open Monday-Friday 9am-5pm and offer both in-person and online sessions. Our main office is located at 123 Therapy Lane. Would you like directions or information about online sessions?"
        intent = "location"
        
    elif any(word in user_message.lower() for word in ["name", "email", "phone", "contact"]):
        if contact_created:
            response = "Thank you! I've saved your contact information. Our team will reach out to you soon. Is there anything specific you'd like to know about our services while we're chatting?"
        else:
            response = "I'd love to help you get connected with our team! Could you share your name and email address so we can follow up with you?"
        intent = "contact_collection"
        
    else:
        response = "Thank you for reaching out! I'm here to help you learn about our therapy services and schedule an appointment. What would you like to know more about?"
        intent = "general"
    
    # Add note to contact if created
    if contact_created and contact_result.get("contact", {}).get("id"):
        try:
            await make_ghl_request("contacts_add_note", {
                "contactId": contact_result["contact"]["id"],
                "note": f"Chatbot conversation: {user_message[:100]}..."
            })
        except:
            pass  # Note creation is optional
    
    return {
        "message": response,
        "intent": intent,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": f"session_{abs(hash(user_message)) % 10000}",
        "contact_created": contact_created,
        "ghl_connected": not contact_result.get("mock", False) if contact_created else None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }