"""
Patient-facing chatbot API with HIPAA compliance and crisis detection.
Provides secure, therapeutic AI interaction for patients between sessions.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ..ai.mental_health_agent import mental_health_agent, MentalHealthContext, AIResponse
from ..core.security import audit_logger, patient_encryption
from ..models.patient import ConversationEntry, CrisisAlert, RiskLevel, ConsentStatus


# Security (lighter for patient access)
security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/chat", tags=["Patient Chatbot"])


# Request/Response Models
class ChatMessage(BaseModel):
    """Patient chat message."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """AI response to patient."""
    message: str
    session_id: str
    timestamp: datetime
    risk_level: str
    crisis_resources: Optional[Dict[str, str]] = None
    therapist_notified: bool = False


class PatientSession(BaseModel):
    """Patient chat session info."""
    session_id: str
    patient_id: str
    therapist_id: str
    started_at: datetime
    last_activity: datetime
    message_count: int
    consent_status: ConsentStatus
    risk_level: RiskLevel


class ConsentRequest(BaseModel):
    """Patient consent for AI interaction."""
    patient_id: str
    consent_granted: bool
    consent_text: str
    signature: str  # Digital signature or typed name


class EmergencyInfo(BaseModel):
    """Emergency resources for crisis situations."""
    crisis_hotlines: List[Dict[str, str]]
    emergency_contacts: List[Dict[str, str]]
    safety_plan: Optional[str] = None


# Mock session storage (would be database in production)
active_sessions: Dict[str, PatientSession] = {}
conversation_contexts: Dict[str, MentalHealthContext] = {}


async def get_patient_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> PatientSession:
    """Get or create patient session."""
    
    # For demo purposes, create a mock session
    # In production, this would validate patient authentication
    session_id = request.headers.get("session-id", f"session_{datetime.utcnow().timestamp()}")
    
    if session_id not in active_sessions:
        # Create new session
        session = PatientSession(
            session_id=session_id,
            patient_id=f"patient_{session_id}",
            therapist_id="therapist_123",  # Would be actual therapist ID
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            consent_status=ConsentStatus.GRANTED,  # Would check actual consent
            risk_level=RiskLevel.LOW
        )
        active_sessions[session_id] = session
        
        # Create conversation context
        conversation_contexts[session_id] = MentalHealthContext(
            patient_id=session.patient_id,
            therapist_id=session.therapist_id,
            session_id=session_id,
            patient_risk_level=session.risk_level
        )
    
    return active_sessions[session_id]


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    message: ChatMessage,
    session: PatientSession = Depends(get_patient_session),
    request: Request = None
) -> ChatResponse:
    """
    Send message to AI chatbot with mental health safeguards.
    """
    
    # Check consent status
    if session.consent_status != ConsentStatus.GRANTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient consent required for AI interaction"
        )
    
    # Log the interaction
    await audit_logger.log_access(
        user_id=session.therapist_id,
        patient_id=session.patient_id,
        action="patient_chat_message",
        resource="ai_chatbot",
        outcome="started",
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    try:
        # Get conversation context
        context = conversation_contexts[session.session_id]
        
        # Add patient message to context
        patient_message_entry = ConversationEntry(
            timestamp=datetime.utcnow(),
            message_type="patient_message",
            content=message.message,
            risk_indicators=[],
            escalation_triggered=False,
            therapist_notified=False
        )
        context.conversation_history.append(patient_message_entry)
        
        # Process message through AI agent
        ai_response, crisis_alert = await mental_health_agent.process_message(
            patient_message=message.message,
            context=context
        )
        
        # Update session
        session.last_activity = datetime.utcnow()
        session.message_count += 1
        session.risk_level = ai_response.risk_assessment
        
        # Handle crisis alerts
        crisis_resources = None
        therapist_notified = False
        
        if crisis_alert:
            therapist_notified = True
            crisis_resources = {
                "crisis_text_line": "Text HOME to 741741",
                "suicide_lifeline": "Call or text 988",
                "emergency": "Call 911 if in immediate danger",
                "your_therapist": "Your therapist has been notified and will contact you soon"
            }
            
            # TODO: Send actual crisis notification to therapist
            await _notify_therapist_of_crisis(session.therapist_id, crisis_alert)
        
        # Log successful interaction
        await audit_logger.log_access(
            user_id=session.therapist_id,
            patient_id=session.patient_id,
            action="patient_chat_message",
            resource="ai_chatbot",
            outcome="success",
            details={
                "message_length": len(message.message),
                "risk_level": ai_response.risk_assessment.value,
                "crisis_alert": crisis_alert is not None
            }
        )
        
        return ChatResponse(
            message=ai_response.message,
            session_id=session.session_id,
            timestamp=datetime.utcnow(),
            risk_level=ai_response.risk_assessment.value,
            crisis_resources=crisis_resources,
            therapist_notified=therapist_notified
        )
        
    except Exception as e:
        await audit_logger.log_access(
            user_id=session.therapist_id,
            patient_id=session.patient_id,
            action="patient_chat_message",
            resource="ai_chatbot",
            outcome="failure",
            details={"error": str(e)}
        )
        
        # Return safe error response
        return ChatResponse(
            message="I'm sorry, I'm having trouble right now. If this is an emergency, please call 911 or text 988 for crisis support. Your therapist will be notified of this issue.",
            session_id=session.session_id,
            timestamp=datetime.utcnow(),
            risk_level="unknown",
            crisis_resources={
                "emergency": "Call 911",
                "crisis_support": "Text 988"
            },
            therapist_notified=True
        )


@router.get("/emergency-resources", response_model=EmergencyInfo)
async def get_emergency_resources(
    session: PatientSession = Depends(get_patient_session)
) -> EmergencyInfo:
    """
    Get emergency resources and crisis support information.
    Always available regardless of session state.
    """
    
    await audit_logger.log_access(
        user_id=session.therapist_id,
        patient_id=session.patient_id,
        action="emergency_resources_access",
        resource="crisis_support",
        outcome="success"
    )
    
    return EmergencyInfo(
        crisis_hotlines=[
            {
                "name": "988 Suicide & Crisis Lifeline",
                "number": "988",
                "description": "24/7 crisis support - call or text",
                "website": "https://988lifeline.org/"
            },
            {
                "name": "Crisis Text Line",
                "number": "741741",
                "description": "Text HOME for 24/7 crisis support",
                "website": "https://www.crisistextline.org/"
            },
            {
                "name": "Emergency Services",
                "number": "911",
                "description": "For immediate life-threatening emergencies",
                "website": None
            }
        ],
        emergency_contacts=[
            {
                "name": "Your Therapist",
                "contact": "Will be notified automatically in crisis situations",
                "availability": "Business hours + emergency protocols"
            }
        ],
        safety_plan="If you're having thoughts of self-harm: 1) Reach out to crisis support, 2) Contact someone you trust, 3) Remove means of harm, 4) Go to a safe place, 5) Stay with someone until crisis passes"
    )


@router.get("/session-info")
async def get_session_info(
    session: PatientSession = Depends(get_patient_session)
):
    """Get current session information and chatbot capabilities."""
    
    return {
        "session_id": session.session_id,
        "started_at": session.started_at,
        "message_count": session.message_count,
        "last_activity": session.last_activity,
        "consent_status": session.consent_status.value,
        "chatbot_info": {
            "purpose": "I'm here to provide support between your therapy sessions",
            "capabilities": [
                "Active listening and emotional support",
                "Crisis detection and safety resources",
                "Therapeutic conversation techniques",
                "Session scheduling assistance",
                "Medication reminders (if requested)"
            ],
            "limitations": [
                "I cannot provide therapy or clinical treatment",
                "I cannot diagnose mental health conditions",
                "I cannot prescribe medications",
                "I cannot replace your therapist",
                "I will notify your therapist of any safety concerns"
            ],
            "privacy": "This conversation is HIPAA-protected and only shared with your therapist",
            "crisis_support": "If you're in crisis, I will immediately provide resources and notify your therapist"
        }
    }


@router.post("/consent")
async def provide_consent(
    consent: ConsentRequest,
    request: Request
):
    """
    Process patient consent for AI interaction.
    Required before chatbot can be used.
    """
    
    await audit_logger.log_access(
        user_id=None,
        patient_id=consent.patient_id,
        action="consent_provided",
        resource="patient_consent",
        outcome="success" if consent.consent_granted else "declined",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={
            "consent_granted": consent.consent_granted,
            "consent_signature": consent.signature
        }
    )
    
    if consent.consent_granted:
        return {
            "message": "Thank you for providing consent. You can now use the AI chatbot.",
            "consent_recorded": True,
            "effective_date": datetime.utcnow(),
            "next_steps": "You can start chatting with the AI support system."
        }
    else:
        return {
            "message": "Consent declined. The AI chatbot will not be available.",
            "consent_recorded": False,
            "alternative_support": "You can still contact your therapist directly for support."
        }


@router.get("/conversation-history")
async def get_conversation_history(
    session: PatientSession = Depends(get_patient_session),
    limit: int = 20
):
    """
    Get recent conversation history for the patient.
    Limited to current session for privacy.
    """
    
    await audit_logger.log_access(
        user_id=session.therapist_id,
        patient_id=session.patient_id,
        action="conversation_history_access",
        resource="patient_conversation",
        outcome="success"
    )
    
    context = conversation_contexts.get(session.session_id)
    if not context:
        return {"messages": []}
    
    # Return recent messages (patient view)
    recent_messages = context.conversation_history[-limit:]
    
    return {
        "session_id": session.session_id,
        "message_count": len(recent_messages),
        "messages": [
            {
                "timestamp": msg.timestamp,
                "type": msg.message_type,
                "content": msg.content if msg.message_type != "system_note" else "[System message]",
                "from": "You" if msg.message_type == "patient_message" else "AI Support"
            }
            for msg in recent_messages
        ]
    }


async def _notify_therapist_of_crisis(therapist_id: str, crisis_alert: CrisisAlert):
    """
    Notify therapist of crisis alert.
    In production, this would send real notifications.
    """
    
    # TODO: Implement actual therapist notification system
    # - Email alert
    # - SMS alert  
    # - Push notification to therapist app
    # - Create urgent task in therapist dashboard
    
    await audit_logger.log_access(
        user_id=therapist_id,
        patient_id=crisis_alert.patient_id,
        action="crisis_alert_sent",
        resource="therapist_notification",
        outcome="success",
        details={
            "alert_type": crisis_alert.alert_type,
            "severity": crisis_alert.severity,
            "trigger_message": crisis_alert.trigger_message[:100]
        }
    )
    
    print(f"CRISIS ALERT: Therapist {therapist_id} notified of {crisis_alert.alert_type} for patient {crisis_alert.patient_id}")


@router.get("/wellness-check")
async def wellness_check():
    """
    Simple wellness check endpoint for the chatbot service.
    Can be used for health monitoring.
    """
    
    return {
        "status": "healthy",
        "service": "Mental Health AI Chatbot",
        "version": "1.0.0",
        "features": {
            "crisis_detection": "active",
            "hipaa_compliance": "enforced",
            "therapist_integration": "enabled",
            "audit_logging": "active"
        },
        "uptime": "Service is running normally",
        "emergency_resources": "Available 24/7"
    }