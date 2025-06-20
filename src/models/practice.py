"""
Practice management models for therapist chatbot platform.
Simplified for sales/booking bot - not complex patient management.
"""

from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Time
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ServiceDelivery(str, Enum):
    """Service delivery options."""
    IN_PERSON = "in_person"
    ONLINE = "online"
    BOTH = "both"


class TeamSize(str, Enum):
    """Practice team size options."""
    SOLO = "solo"
    SMALL_GROUP = "small_group"
    GROUP_PRACTICE = "group_practice"


class PracticeStatus(str, Enum):
    """Practice account status."""
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class ChatbotBranding(BaseModel):
    """Chatbot branding configuration."""
    bot_name: str = "Therapy Bot"
    primary_color: str = "#ac7782"
    secondary_color: str = "#d3d6de"
    title_font: str = "Inter"
    body_font: str = "Inter"
    logo_url: Optional[str] = None
    welcome_message: str = "Hi! I'm here to help you with scheduling and answering questions about our therapy services. How can I assist you today?"


class AppointmentConfig(BaseModel):
    """Appointment booking configuration."""
    enabled: bool = True
    google_calendar_id: Optional[str] = None
    booking_hours_start: time = time(9, 0)
    booking_hours_end: time = time(17, 0)
    available_days: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    appointment_types: List[str] = ["Initial Consultation", "Individual Therapy", "Couples Therapy"]
    buffer_time_minutes: int = 15
    advance_booking_days: int = 30


class BotInstructions(BaseModel):
    """Bot behavior instructions."""
    what_bot_should_say: str = "Be warm, professional, and helpful. Focus on scheduling appointments and providing basic practice information."
    what_bot_should_never_say: str = "Never provide therapy advice, diagnose conditions, or discuss specific treatment details."
    emergency_instructions: str = "For mental health emergencies, direct users to call 988 (Suicide & Crisis Lifeline) or 911."
    max_messages_per_conversation: int = 20


class PracticeDB(Base):
    """Database model for practice information."""
    __tablename__ = "practices"
    
    id = Column(String, primary_key=True)
    ghl_location_id = Column(String, unique=True, nullable=False)
    
    # Basic Information
    practice_name = Column(String, nullable=False)
    practice_email = Column(String, nullable=False)
    phone_number = Column(String)
    website = Column(String)
    hours_of_operation = Column(String)
    
    # Configuration
    team_size = Column(String, default=TeamSize.SOLO)
    service_delivery = Column(String, default=ServiceDelivery.BOTH)
    accepts_insurance = Column(Boolean, default=True)
    
    # Chatbot Configuration (JSON)
    branding_config = Column(JSON)
    appointment_config = Column(JSON)
    bot_instructions = Column(JSON)
    
    # Status and Metadata
    status = Column(String, default=PracticeStatus.TRIAL)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    onboarding_completed = Column(Boolean, default=False)


class PracticeBase(BaseModel):
    """Base practice model."""
    practice_name: str = Field(..., min_length=1, max_length=100)
    practice_email: EmailStr
    phone_number: Optional[str] = None
    website: Optional[str] = None
    hours_of_operation: str = "Mon-Fri 9a-5p"
    team_size: TeamSize = TeamSize.SOLO
    service_delivery: ServiceDelivery = ServiceDelivery.BOTH
    accepts_insurance: bool = True


class PracticeCreate(PracticeBase):
    """Model for creating new practice."""
    ghl_location_id: str
    auto_analyze_website: bool = True


class PracticeUpdate(BaseModel):
    """Model for updating practice information."""
    practice_name: Optional[str] = None
    practice_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    hours_of_operation: Optional[str] = None
    team_size: Optional[TeamSize] = None
    service_delivery: Optional[ServiceDelivery] = None
    accepts_insurance: Optional[bool] = None


class PracticeResponse(PracticeBase):
    """Practice API response."""
    id: str
    ghl_location_id: str
    status: PracticeStatus
    created_at: datetime
    updated_at: datetime
    onboarding_completed: bool
    
    # Configuration objects
    branding: ChatbotBranding
    appointments: AppointmentConfig
    bot_settings: BotInstructions
    
    class Config:
        from_attributes = True


class Location(BaseModel):
    """Practice location information."""
    id: Optional[str] = None
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False
    online_sessions_available: bool = True


class ServiceCategory(BaseModel):
    """Service category model."""
    category: str  # "What We Treat" or "How We Treat"
    services: List[str]
    description: Optional[str] = None


class FAQ(BaseModel):
    """Frequently asked question."""
    id: Optional[str] = None
    question: str
    answer: str
    category: Optional[str] = None
    created_at: Optional[datetime] = None


class ConversationMetrics(BaseModel):
    """Conversation analytics data."""
    total_conversations: int = 0
    appointments_booked: int = 0
    conversion_rate: float = 0.0
    avg_response_time: float = 0.0
    weekly_activity: Dict[str, int] = Field(default_factory=dict)
    top_topics: Dict[str, int] = Field(default_factory=dict)


class ChatbotConversation(BaseModel):
    """Individual chatbot conversation."""
    id: str
    visitor_name: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_phone: Optional[str] = None
    status: str  # "ongoing", "completed", "abandoned"
    started_at: datetime
    last_message_at: datetime
    message_count: int = 0
    appointment_booked: bool = False
    topics: List[str] = Field(default_factory=list)
    ghl_contact_id: Optional[str] = None


class ChatMessage(BaseModel):
    """Individual chat message."""
    id: str
    conversation_id: str
    sender: str  # "visitor" or "bot"
    message: str
    timestamp: datetime
    intent: Optional[str] = None  # "booking", "question", "pricing", etc.


class WebsiteAnalysis(BaseModel):
    """Website analysis results for auto-setup."""
    url: str
    practice_name: Optional[str] = None
    services_offered: List[str] = Field(default_factory=list)
    contact_info: Dict[str, str] = Field(default_factory=dict)
    color_scheme: Dict[str, str] = Field(default_factory=dict)
    existing_faqs: List[FAQ] = Field(default_factory=list)
    analysis_completed: bool = False
    analysis_date: Optional[datetime] = None


# Utility functions
def create_default_branding() -> ChatbotBranding:
    """Create default branding configuration."""
    return ChatbotBranding()


def create_default_appointment_config() -> AppointmentConfig:
    """Create default appointment configuration."""
    return AppointmentConfig()


def create_default_bot_instructions() -> BotInstructions:
    """Create default bot instructions."""
    return BotInstructions()


def get_conversation_topics_analysis(conversations: List[ChatbotConversation]) -> Dict[str, float]:
    """Analyze conversation topics and return percentages."""
    topic_counts = {}
    total_conversations = len(conversations)
    
    if total_conversations == 0:
        return {}
    
    for conversation in conversations:
        for topic in conversation.topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Convert to percentages
    topic_percentages = {
        topic: (count / total_conversations) * 100
        for topic, count in topic_counts.items()
    }
    
    return dict(sorted(topic_percentages.items(), key=lambda x: x[1], reverse=True))


def calculate_conversion_rate(conversations: List[ChatbotConversation]) -> float:
    """Calculate appointment booking conversion rate."""
    if not conversations:
        return 0.0
    
    booked_appointments = sum(1 for conv in conversations if conv.appointment_booked)
    return (booked_appointments / len(conversations)) * 100