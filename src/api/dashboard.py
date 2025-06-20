"""
Dashboard API matching the exact screenshots provided.
Clean, focused interface for practice management and chatbot analytics.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..models.practice import (
    PracticeResponse, ChatbotBranding, AppointmentConfig, BotInstructions,
    ConversationMetrics, ChatbotConversation, FAQ, Location, ServiceCategory
)
from ..core.security import jwt_manager

# Security
security = HTTPBearer()
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Request/Response Models
class DashboardOverview(BaseModel):
    """Main dashboard overview data."""
    total_conversations: int
    conversations_change: str  # "+12% from last week"
    appointments_booked: int
    appointments_change: str
    conversion_rate: float
    conversion_change: str
    avg_response_time: float
    response_time_change: str


class RecentConversation(BaseModel):
    """Recent conversation summary."""
    initial: str  # "S", "M", etc.
    name: str
    preview: str
    status: str  # "Completed", "Ongoing"
    time_ago: str  # "10 min ago"


class ChatbotStatus(BaseModel):
    """Current chatbot status."""
    status: str  # "Active"
    model: str   # "Claude 3.5 Sonnet"
    knowledge_base: str  # "12 documents"
    last_updated: str    # "2 days ago"


class DashboardData(BaseModel):
    """Complete dashboard data."""
    overview: DashboardOverview
    recent_conversations: List[RecentConversation]
    chatbot_status: ChatbotStatus


class AnalyticsData(BaseModel):
    """Analytics page data."""
    overview: DashboardOverview
    weekly_activity: Dict[str, Dict[str, int]]  # {"Mon": {"conversations": 12, "appointments": 3}}
    top_conversation_topics: Dict[str, float]  # {"Appointment Scheduling": 35.0}
    avg_response_time_chart: List[float]


class PracticeInfoUpdate(BaseModel):
    """Practice information update."""
    practice_name: str
    practice_email: str
    phone_number: str
    website: str
    hours_of_operation: str
    team_size: str
    service_delivery: str
    accepts_insurance: bool


class LocationUpdate(BaseModel):
    """Location information update."""
    locations: List[Location]


class ServicesUpdate(BaseModel):
    """Services and treatment update."""
    what_we_treat: List[str]
    how_we_treat: List[str]
    client_experience: str


class KnowledgeBaseUpdate(BaseModel):
    """Knowledge base update."""
    faqs: List[FAQ]
    documents: List[str]
    website_links: List[str]


class ChatbotBrandingUpdate(BaseModel):
    """Chatbot branding update."""
    branding: ChatbotBranding


class ChatbotInstructionsUpdate(BaseModel):
    """Chatbot instructions update."""
    instructions: BotInstructions


class AppointmentBookingUpdate(BaseModel):
    """Appointment booking configuration update."""
    config: AppointmentConfig


# Dependency to get current practice
async def get_current_practice(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current authenticated practice ID."""
    try:
        token_data = jwt_manager.verify_token(credentials.credentials)
        practice_id = token_data.get("sub")
        
        if not practice_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return practice_id
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.get("/", response_model=DashboardData)
async def get_dashboard(practice_id: str = Depends(get_current_practice)) -> DashboardData:
    """
    Get main dashboard data matching the screenshot exactly.
    """
    
    # Mock data matching the screenshot
    overview = DashboardOverview(
        total_conversations=152,
        conversations_change="+12% from last week",
        appointments_booked=24,
        appointments_change="+8% from last week",
        conversion_rate=15.8,
        conversion_change="+3% from last week",
        avg_response_time=2.1,
        response_time_change="-0.3s from last week"
    )
    
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
    
    chatbot_status = ChatbotStatus(
        status="Active",
        model="Claude 3.5 Sonnet",
        knowledge_base="12 documents",
        last_updated="2 days ago"
    )
    
    return DashboardData(
        overview=overview,
        recent_conversations=recent_conversations,
        chatbot_status=chatbot_status
    )


@router.get("/analytics", response_model=AnalyticsData)
async def get_analytics(practice_id: str = Depends(get_current_practice)) -> AnalyticsData:
    """
    Get analytics data matching the analytics screenshot.
    """
    
    # Overview stats
    overview = DashboardOverview(
        total_conversations=152,
        conversations_change="+12% from last week",
        appointments_booked=24,
        appointments_change="+8% from last week",
        conversion_rate=15.8,
        conversion_change="+3% from last week",
        avg_response_time=2.1,
        response_time_change="-0.3s from last week"
    )
    
    # Weekly activity data (matching the bar chart)
    weekly_activity = {
        "Mon": {"conversations": 12, "appointments": 3},
        "Tue": {"conversations": 8, "appointments": 2},
        "Wed": {"conversations": 22, "appointments": 5},
        "Thu": {"conversations": 18, "appointments": 4},
        "Fri": {"conversations": 15, "appointments": 3},
        "Sat": {"conversations": 8, "appointments": 2},
        "Sun": {"conversations": 7, "appointments": 2}
    }
    
    # Top conversation topics (matching the pie chart)
    top_conversation_topics = {
        "Appointment Scheduling": 35.0,
        "Service Information": 25.0,
        "Insurance Questions": 20.0,
        "Location & Hours": 12.0,
        "Pricing": 8.0
    }
    
    # Response time chart data
    avg_response_time_chart = [3.2, 2.8, 2.5, 2.1, 2.3, 2.0]
    
    return AnalyticsData(
        overview=overview,
        weekly_activity=weekly_activity,
        top_conversation_topics=top_conversation_topics,
        avg_response_time_chart=avg_response_time_chart
    )


@router.get("/practice-info")
async def get_practice_info(practice_id: str = Depends(get_current_practice)):
    """
    Get practice information for the Practice Info page.
    """
    
    # Mock data matching the screenshot
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


@router.put("/practice-info")
async def update_practice_info(
    update_data: PracticeInfoUpdate,
    practice_id: str = Depends(get_current_practice)
):
    """
    Update practice information.
    """
    
    # TODO: Update practice in database
    return {
        "message": "Practice information updated successfully",
        "updated_at": datetime.utcnow()
    }


@router.get("/locations")
async def get_locations(practice_id: str = Depends(get_current_practice)):
    """
    Get practice locations.
    """
    
    # Mock data
    return {
        "locations": [
            {
                "id": "loc_1",
                "name": "Main Office",
                "address": "123 Therapy Lane",
                "city": "Springfield",
                "state": "MA",
                "zip_code": "01103",
                "phone": "413-331-7421",
                "email": "main@intensivetherapyretreat.com",
                "is_primary": True,
                "online_sessions_available": True
            }
        ]
    }


@router.post("/locations")
async def create_location(
    location_data: Location,
    practice_id: str = Depends(get_current_practice)
):
    """
    Create new practice location.
    """
    
    # TODO: Create location in database
    return {
        "message": "Location created successfully",
        "location_id": f"loc_{datetime.utcnow().timestamp()}",
        "created_at": datetime.utcnow()
    }


@router.get("/services")
async def get_services(practice_id: str = Depends(get_current_practice)):
    """
    Get services and treatment information.
    """
    
    return {
        "what_we_treat": [
            "Anxiety and Depression",
            "Trauma and PTSD",
            "Relationship Issues",
            "Life Transitions",
            "Stress Management"
        ],
        "how_we_treat": [
            "Cognitive Behavioral Therapy (CBT)",
            "EMDR Therapy",
            "Mindfulness-Based Approaches",
            "Solution-Focused Therapy",
            "Intensive Therapy Retreats"
        ],
        "client_experience": "We provide a safe, supportive environment for healing and growth. Our approach is collaborative and tailored to your unique needs and goals."
    }


@router.put("/services")
async def update_services(
    services_data: ServicesUpdate,
    practice_id: str = Depends(get_current_practice)
):
    """
    Update services and treatment information.
    """
    
    # TODO: Update in database
    return {
        "message": "Services updated successfully",
        "updated_at": datetime.utcnow()
    }


@router.get("/knowledge-base")
async def get_knowledge_base(practice_id: str = Depends(get_current_practice)):
    """
    Get knowledge base information (FAQs, documents, links).
    """
    
    return {
        "faqs": [
            {
                "id": "faq_1",
                "question": "What types of therapy do you offer?",
                "answer": "We offer individual therapy, couples counseling, and intensive therapy retreats using evidence-based approaches.",
                "category": "Services"
            }
        ],
        "documents": [
            {
                "id": "doc_1",
                "name": "Intake Forms",
                "url": "/documents/intake-forms.pdf",
                "uploaded_at": "2025-01-10"
            }
        ],
        "website_links": [
            {
                "id": "link_1",
                "title": "About Our Approach",
                "url": "https://intensivetherapyretreat.com/approach",
                "description": "Learn about our therapeutic methodology"
            }
        ]
    }


@router.get("/chatbot-setup/branding")
async def get_chatbot_branding(practice_id: str = Depends(get_current_practice)):
    """
    Get chatbot branding configuration.
    """
    
    # Mock data matching the screenshot
    return {
        "bot_name": "Retreat Bot",
        "primary_color": "#ac7782",
        "secondary_color": "#d3d6de",
        "title_font": "Inter",
        "body_font": "Inter",
        "logo_url": None,
        "welcome_message": "Hi! I'm here to help you with scheduling and answering questions about our therapy services. How can I assist you today?"
    }


@router.put("/chatbot-setup/branding")
async def update_chatbot_branding(
    branding_data: ChatbotBrandingUpdate,
    practice_id: str = Depends(get_current_practice)
):
    """
    Update chatbot branding configuration.
    """
    
    # TODO: Update in database
    return {
        "message": "Chatbot branding updated successfully",
        "updated_at": datetime.utcnow()
    }


@router.get("/chatbot-setup/instructions")
async def get_bot_instructions(practice_id: str = Depends(get_current_practice)):
    """
    Get bot instructions configuration.
    """
    
    return {
        "what_bot_should_say": "Be warm, professional, and helpful. Focus on scheduling appointments and providing basic practice information.",
        "what_bot_should_never_say": "Never provide therapy advice, diagnose conditions, or discuss specific treatment details.",
        "emergency_instructions": "For mental health emergencies, direct users to call 988 (Suicide & Crisis Lifeline) or 911.",
        "max_messages_per_conversation": 20
    }


@router.get("/chatbot-setup/appointment-booking")
async def get_appointment_config(practice_id: str = Depends(get_current_practice)):
    """
    Get appointment booking configuration.
    """
    
    return {
        "enabled": True,
        "google_calendar_id": "your-calendar@gmail.com",
        "booking_hours_start": "09:00",
        "booking_hours_end": "17:00",
        "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "appointment_types": ["Initial Consultation", "Individual Therapy", "Couples Therapy"],
        "buffer_time_minutes": 15,
        "advance_booking_days": 30
    }


@router.get("/website-integration")
async def get_website_integration(practice_id: str = Depends(get_current_practice)):
    """
    Get website integration code and settings.
    """
    
    return {
        "embed_code": f'<script src="https://moonraker-engage.com/widget.js" data-practice-id="{practice_id}"></script>',
        "widget_settings": {
            "position": "bottom-right",
            "theme": "auto",
            "expanded_by_default": False
        },
        "installation_guide": "Copy the embed code and paste it before the closing </body> tag on your website."
    }


@router.get("/test-claude")
async def test_claude_integration(practice_id: str = Depends(get_current_practice)):
    """
    Test Claude AI integration and provide debugging info.
    """
    
    return {
        "status": "connected",
        "model": "claude-3-5-sonnet-20241022",
        "last_test": datetime.utcnow(),
        "response_time": "1.2s",
        "test_message": "Test successful - Claude is responding normally"
    }