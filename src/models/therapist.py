"""
Therapist model with HIPAA-compliant data handling.
Therapists never need direct GHL access - all interactions go through our secure layer.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

from ..core.security import patient_encryption

Base = declarative_base()


class TherapistLicenseType(str, Enum):
    """Valid therapist license types."""
    LCSW = "lcsw"  # Licensed Clinical Social Worker
    LMFT = "lmft"  # Licensed Marriage and Family Therapist
    LPC = "lpc"    # Licensed Professional Counselor
    LPCC = "lpcc"  # Licensed Professional Clinical Counselor
    LMHC = "lmhc"  # Licensed Mental Health Counselor
    PsyD = "psyd"  # Doctor of Psychology
    PhD = "phd"    # Doctor of Philosophy in Psychology
    MD = "md"      # Medical Doctor (Psychiatrist)


class TherapistStatus(str, Enum):
    """Therapist account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class TherapistPreferences(BaseModel):
    """Therapist preferences for chatbot behavior."""
    crisis_protocol: str = "standard"
    session_style: str = "supportive"  # supportive, directive, non-directive
    documentation_style: str = "detailed"  # brief, detailed, structured
    patient_communication_tone: str = "warm"  # warm, professional, casual
    auto_schedule_followups: bool = True
    crisis_escalation_immediate: bool = True
    session_reminders_enabled: bool = True
    progress_notes_auto_generate: bool = False
    
    class Config:
        extra = "allow"


class TherapistDB(Base):
    """Database model for therapist information."""
    __tablename__ = "therapists"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    license_type = Column(String, nullable=False)
    license_number = Column(String, nullable=False)
    license_state = Column(String, nullable=False)
    encrypted_credentials = Column(Text)  # Encrypted GHL credentials
    preferences = Column(JSON)
    status = Column(String, default=TherapistStatus.PENDING_VERIFICATION)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    supervision_required = Column(Boolean, default=False)


class TherapistBase(BaseModel):
    """Base therapist model for API operations."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    license_type: TherapistLicenseType
    license_number: str = Field(..., min_length=1, max_length=50)
    license_state: str = Field(..., min_length=2, max_length=2)
    preferences: TherapistPreferences = Field(default_factory=TherapistPreferences)
    supervision_required: bool = False
    
    @validator("license_state")
    def validate_license_state(cls, v):
        """Validate US state code."""
        valid_states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
        if v.upper() not in valid_states:
            raise ValueError("Invalid US state code")
        return v.upper()


class TherapistCreate(TherapistBase):
    """Model for creating new therapist accounts."""
    password: str = Field(..., min_length=12)
    ghl_api_key: Optional[str] = None  # Optional GHL integration
    ghl_location_id: Optional[str] = None
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength for HIPAA compliance."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )
        
        return v


class TherapistUpdate(BaseModel):
    """Model for updating therapist information."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    preferences: Optional[TherapistPreferences] = None
    supervision_required: Optional[bool] = None


class TherapistResponse(TherapistBase):
    """Model for therapist API responses (excludes sensitive data)."""
    id: str
    status: TherapistStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_verified: bool
    has_ghl_integration: bool = False  # Whether GHL is connected
    
    class Config:
        from_attributes = True


class TherapistLogin(BaseModel):
    """Model for therapist login."""
    email: EmailStr
    password: str


class TherapistDashboard(BaseModel):
    """Therapist dashboard data (aggregated from GHL without exposing raw data)."""
    active_patients: int = 0
    pending_messages: int = 0
    scheduled_sessions: int = 0
    crisis_alerts: int = 0
    weekly_session_count: int = 0
    monthly_session_count: int = 0
    recent_activity: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class GHLCredentials(BaseModel):
    """Encrypted GHL credentials model."""
    api_key: str
    location_id: str
    webhook_url: Optional[str] = None
    
    def encrypt(self) -> str:
        """Encrypt credentials for secure storage."""
        return patient_encryption.encrypt_dict(self.model_dump())
    
    @classmethod
    def decrypt(cls, encrypted_data: str) -> "GHLCredentials":
        """Decrypt credentials from storage."""
        decrypted_data = patient_encryption.decrypt_dict(encrypted_data)
        return cls(**decrypted_data)


# Utility functions for therapist management
def create_therapist_abstraction_layer(therapist: TherapistResponse) -> dict:
    """
    Create abstraction layer that hides GHL complexity from therapists.
    They only see patient-focused, therapy-relevant information.
    """
    return {
        "therapist_id": therapist.id,
        "name": f"{therapist.first_name} {therapist.last_name}",
        "license": f"{therapist.license_type.value.upper()} - {therapist.license_state}",
        "interface_type": "therapy_focused",  # Not "crm_focused"
        "available_features": [
            "patient_conversations",
            "session_scheduling",
            "progress_tracking",
            "crisis_management",
            "documentation_assistance",
            "appointment_reminders"
        ],
        "hidden_features": [  # GHL features hidden from therapist view
            "marketing_campaigns",
            "sales_pipeline",
            "lead_management",
            "business_analytics",
            "payment_processing"
        ]
    }