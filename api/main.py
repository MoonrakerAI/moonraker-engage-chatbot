"""
Simplified FastAPI app for Vercel deployment.
"""

from fastapi import FastAPI
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
    """Get dashboard data matching the screenshots."""
    
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
        ),
        RecentConversation(
            initial="E",
            name="Emma Wilson",
            preview="What are your hours of operation?",
            status="Completed",
            time_ago="1 hour ago"
        ),
        RecentConversation(
            initial="J",
            name="James Rodriguez",
            preview="I need information about couples therapy",
            status="Completed",
            time_ago="2 hours ago"
        )
    ]
    
    chatbot_status = ChatbotStatus()
    
    return {
        "overview": stats.model_dump(),
        "recent_conversations": [conv.model_dump() for conv in recent_conversations],
        "chatbot_status": chatbot_status.model_dump()
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
    """Handle chat messages - simplified for demo."""
    
    user_message = message.get("message", "")
    
    # Simple response logic
    if any(word in user_message.lower() for word in ["appointment", "schedule", "book"]):
        response = "I'd be happy to help you schedule an appointment! What type of session are you looking for - individual therapy, couples counseling, or an initial consultation?"
        intent = "booking"
    elif any(word in user_message.lower() for word in ["price", "cost", "insurance"]):
        response = "We accept most major insurance plans and offer competitive self-pay rates. Individual sessions typically range from $120-180. Would you like me to check your specific insurance benefits?"
        intent = "pricing"
    elif any(word in user_message.lower() for word in ["hours", "location", "address"]):
        response = "We're open Monday-Friday 9am-5pm and offer both in-person and online sessions. Our main office is located at 123 Therapy Lane. Would you like directions or information about online sessions?"
        intent = "location"
    else:
        response = "Thank you for reaching out! I'm here to help you learn about our therapy services and schedule an appointment. What would you like to know more about?"
        intent = "general"
    
    return {
        "message": response,
        "intent": intent,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": "demo_session_123"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }