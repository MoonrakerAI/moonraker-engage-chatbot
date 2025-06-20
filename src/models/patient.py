"""
Patient model with HIPAA-compliant data handling and anonymization.
All patient data is encrypted and access is fully audited.
"""

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Date, Integer
from sqlalchemy.ext.declarative import declarative_base

from ..core.security import patient_encryption, audit_logger

Base = declarative_base()


class ConsentStatus(str, Enum):
    """Patient consent status for AI interaction."""
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """Patient risk assessment levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRISIS = "crisis"


class SessionStatus(str, Enum):
    """Therapy session status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PatientDB(Base):
    """Database model for patient information (encrypted)."""
    __tablename__ = "patients"
    
    # Use anonymized ID as primary key
    id = Column(String, primary_key=True)  # anonymized_patient_id
    therapist_id = Column(String, nullable=False)
    
    # All PII is encrypted
    encrypted_personal_info = Column(Text)  # name, email, phone, address
    encrypted_medical_info = Column(Text)   # diagnosis, medications, history
    encrypted_session_notes = Column(Text)  # therapy notes and observations
    
    # Non-PII metadata (can be unencrypted for queries)
    risk_level = Column(String, default=RiskLevel.LOW)
    consent_status = Column(String, default=ConsentStatus.PENDING)
    consent_date = Column(DateTime)
    last_session_date = Column(DateTime)
    next_session_date = Column(DateTime)
    session_count = Column(Integer, default=0)
    
    # GHL integration (encrypted)
    encrypted_ghl_contact_id = Column(String)  # encrypted GHL contact reference
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime)
    last_accessed_by = Column(String)


class PersonalInfo(BaseModel):
    """Patient personal information (will be encrypted)."""
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    preferred_pronouns: Optional[str] = None


class MedicalInfo(BaseModel):
    """Patient medical information (will be encrypted)."""
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    medical_history: Optional[str] = None
    family_mental_health_history: Optional[str] = None
    substance_use_history: Optional[str] = None
    trauma_history: Optional[str] = None
    previous_therapy_experience: Optional[str] = None


class SessionNote(BaseModel):
    """Individual therapy session note."""
    session_date: datetime
    session_duration_minutes: int
    session_type: str  # individual, group, family, etc.
    presenting_concerns: Optional[str] = None
    interventions_used: List[str] = Field(default_factory=list)
    patient_mood: Optional[str] = None
    risk_assessment: RiskLevel = RiskLevel.LOW
    homework_assigned: Optional[str] = None
    next_session_plan: Optional[str] = None
    therapist_notes: Optional[str] = None
    crisis_indicators: List[str] = Field(default_factory=list)


class ConversationEntry(BaseModel):
    """AI chatbot conversation entry."""
    timestamp: datetime
    message_type: str  # patient_message, ai_response, system_note
    content: str
    risk_indicators: List[str] = Field(default_factory=list)
    escalation_triggered: bool = False
    therapist_notified: bool = False


class PatientBase(BaseModel):
    """Base patient model for API operations."""
    therapist_id: str
    personal_info: PersonalInfo
    medical_info: Optional[MedicalInfo] = None
    risk_level: RiskLevel = RiskLevel.LOW
    consent_status: ConsentStatus = ConsentStatus.PENDING
    
    @validator("risk_level")
    def validate_risk_level(cls, v, values):
        """Auto-escalate if crisis indicators present."""
        medical_info = values.get("medical_info")
        if medical_info and any(keyword in str(medical_info).lower() 
                               for keyword in ["suicide", "self-harm", "crisis"]):
            return RiskLevel.CRISIS
        return v


class PatientCreate(PatientBase):
    """Model for creating new patient records."""
    initial_consent: bool = Field(..., description="Patient has provided initial consent")
    ghl_contact_id: Optional[str] = None  # Link to GHL contact if exists
    
    @validator("initial_consent")
    def validate_consent_required(cls, v):
        """Ensure consent is provided before creating patient record."""
        if not v:
            raise ValueError("Patient consent is required to create record")
        return v


class PatientUpdate(BaseModel):
    """Model for updating patient information."""
    personal_info: Optional[PersonalInfo] = None
    medical_info: Optional[MedicalInfo] = None
    risk_level: Optional[RiskLevel] = None
    consent_status: Optional[ConsentStatus] = None


class PatientResponse(BaseModel):
    """Patient API response (anonymized and minimal)."""
    id: str  # anonymized ID
    therapist_id: str
    risk_level: RiskLevel
    consent_status: ConsentStatus
    consent_date: Optional[datetime] = None
    last_session_date: Optional[datetime] = None
    next_session_date: Optional[datetime] = None
    session_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    # Only basic info for therapist interface (not full PII)
    display_name: str = "Anonymous Patient"  # Never show real name in responses
    initials: Optional[str] = None  # e.g., "J.D."
    
    class Config:
        from_attributes = True


class PatientConversation(BaseModel):
    """Patient conversation with AI (encrypted storage)."""
    patient_id: str
    conversation_entries: List[ConversationEntry]
    started_at: datetime
    last_message_at: datetime
    session_id: Optional[str] = None
    risk_alerts_count: int = 0
    escalations_triggered: int = 0


class CrisisAlert(BaseModel):
    """Crisis alert for immediate therapist attention."""
    patient_id: str
    alert_type: str  # suicide_ideation, self_harm, psychosis, etc.
    severity: str    # low, medium, high, critical
    trigger_message: str
    ai_assessment: str
    recommended_action: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_by_therapist: bool = False
    acknowledged_at: Optional[datetime] = None


class PatientSummary(BaseModel):
    """Anonymized patient summary for therapist dashboard."""
    anonymous_id: str
    initials: str
    risk_level: RiskLevel
    last_contact: datetime
    upcoming_session: Optional[datetime] = None
    recent_activity: str  # "Active in chat", "Missed appointment", etc.
    flags: List[str] = Field(default_factory=list)  # ["Crisis alert", "Consent expired", etc.]


# Utility functions for patient data handling
async def encrypt_patient_data(patient_data: PatientBase) -> Dict[str, str]:
    """Encrypt patient data for secure storage."""
    encrypted_data = {}
    
    # Encrypt personal information
    if patient_data.personal_info:
        encrypted_data["encrypted_personal_info"] = patient_encryption.encrypt_pii(
            patient_data.personal_info.model_dump()
        )
    
    # Encrypt medical information
    if patient_data.medical_info:
        encrypted_data["encrypted_medical_info"] = patient_encryption.encrypt_pii(
            patient_data.medical_info.model_dump()
        )
    
    # Log the encryption action
    await audit_logger.log_access(
        user_id=patient_data.therapist_id,
        patient_id=None,  # Will be set after creation
        action="encrypt_patient_data",
        resource="patient_record",
        outcome="success"
    )
    
    return encrypted_data


async def decrypt_patient_data(encrypted_data: Dict[str, str], accessing_therapist_id: str) -> Dict[str, Any]:
    """Decrypt patient data with full audit logging."""
    decrypted_data = {}
    
    try:
        # Decrypt personal information
        if "encrypted_personal_info" in encrypted_data:
            personal_info_dict = patient_encryption.decrypt_dict(encrypted_data["encrypted_personal_info"])
            decrypted_data["personal_info"] = PersonalInfo(**personal_info_dict["data"])
        
        # Decrypt medical information
        if "encrypted_medical_info" in encrypted_data:
            medical_info_dict = patient_encryption.decrypt_dict(encrypted_data["encrypted_medical_info"])
            decrypted_data["medical_info"] = MedicalInfo(**medical_info_dict["data"])
        
        # Log the access
        await audit_logger.log_access(
            user_id=accessing_therapist_id,
            patient_id=None,  # Would be actual patient ID
            action="decrypt_patient_data",
            resource="patient_record",
            outcome="success"
        )
        
        return decrypted_data
        
    except Exception as e:
        # Log failed access attempt
        await audit_logger.log_access(
            user_id=accessing_therapist_id,
            patient_id=None,
            action="decrypt_patient_data",
            resource="patient_record",
            outcome="failure",
            details={"error": str(e)}
        )
        raise


def create_patient_anonymized_view(patient: PatientResponse, personal_info: Optional[PersonalInfo] = None) -> PatientSummary:
    """Create anonymized patient view for therapist interface."""
    # Generate initials from personal info if available
    initials = "XX"
    if personal_info:
        first_initial = personal_info.first_name[0].upper() if personal_info.first_name else "X"
        last_initial = personal_info.last_name[0].upper() if personal_info.last_name else "X"
        initials = f"{first_initial}.{last_initial}."
    
    # Determine recent activity
    activity = "No recent activity"
    if patient.last_session_date:
        days_since = (datetime.utcnow() - patient.last_session_date).days
        if days_since == 0:
            activity = "Session today"
        elif days_since == 1:
            activity = "Session yesterday"
        else:
            activity = f"Last session {days_since} days ago"
    
    # Generate flags based on patient status
    flags = []
    if patient.risk_level == RiskLevel.CRISIS:
        flags.append("Crisis alert")
    elif patient.risk_level == RiskLevel.HIGH:
        flags.append("High risk")
    
    if patient.consent_status != ConsentStatus.GRANTED:
        flags.append("Consent required")
    
    return PatientSummary(
        anonymous_id=patient.id,
        initials=initials,
        risk_level=patient.risk_level,
        last_contact=patient.last_session_date or patient.created_at,
        upcoming_session=patient.next_session_date,
        recent_activity=activity,
        flags=flags
    )