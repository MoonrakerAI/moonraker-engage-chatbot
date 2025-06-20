"""
Mental health AI agent using PydanticAI with specialized prompts and safety measures.
Implements crisis detection, therapeutic conversation patterns, and HIPAA compliance.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import dspy
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..core.config import settings
from ..core.security import audit_logger
from ..models.patient import ConversationEntry, CrisisAlert, RiskLevel


class MentalHealthContext(BaseModel):
    """Context for mental health conversations."""
    patient_id: str
    therapist_id: str
    session_id: Optional[str] = None
    conversation_history: List[ConversationEntry] = Field(default_factory=list)
    patient_risk_level: RiskLevel = RiskLevel.LOW
    crisis_keywords_detected: List[str] = Field(default_factory=list)
    therapeutic_goals: List[str] = Field(default_factory=list)
    therapist_preferences: Dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    """Structured AI response with safety checks."""
    message: str
    risk_assessment: RiskLevel
    crisis_indicators: List[str] = Field(default_factory=list)
    therapeutic_techniques_used: List[str] = Field(default_factory=list)
    escalation_required: bool = False
    follow_up_needed: bool = False
    session_notes: Optional[str] = None


class CrisisDetectionSignature(dspy.Signature):
    """DSPy signature for crisis detection optimization."""
    patient_message = dspy.InputField(desc="Patient's message to analyze")
    conversation_history = dspy.InputField(desc="Recent conversation context")
    risk_assessment = dspy.OutputField(desc="Risk level: low, moderate, high, crisis")
    crisis_indicators = dspy.OutputField(desc="List of specific crisis indicators found")
    immediate_response_needed = dspy.OutputField(desc="Boolean: requires immediate intervention")


class TherapeuticResponseSignature(dspy.Signature):
    """DSPy signature for therapeutic response generation."""
    patient_message = dspy.InputField(desc="Patient's message")
    conversation_context = dspy.InputField(desc="Conversation history and context")
    therapist_style = dspy.InputField(desc="Therapist's preferred communication style")
    therapeutic_response = dspy.OutputField(desc="Empathetic, therapeutic response")
    techniques_used = dspy.OutputField(desc="Therapeutic techniques applied")


class MentalHealthAgent:
    """Main mental health AI agent with specialized capabilities."""
    
    def __init__(self):
        """Initialize the mental health agent."""
        self.crisis_keywords = [
            # Suicide-related
            "suicide", "kill myself", "end my life", "want to die", "better off dead",
            "suicide plan", "suicidal", "end it all", "take my own life",
            
            # Self-harm related
            "cut myself", "hurt myself", "self harm", "self-harm", "cutting",
            "burning myself", "punish myself",
            
            # Crisis-related
            "can't go on", "hopeless", "no way out", "give up", "worthless",
            "emergency", "crisis", "breakdown", "losing control",
            
            # Psychosis indicators
            "hearing voices", "voices telling me", "paranoid", "conspiracy",
            "they're watching", "not real", "hallucination"
        ]
        
        # Initialize DSPy modules for optimization
        self.crisis_detector = dspy.ChainOfThought(CrisisDetectionSignature)
        self.therapeutic_responder = dspy.ChainOfThought(TherapeuticResponseSignature)
        
        # Initialize PydanticAI agent
        self.agent = Agent(
            model=settings.default_ai_model,
            result_type=AIResponse,
            system_prompt=self._get_system_prompt(),
            retries=2
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the mental health AI."""
        return """
You are a HIPAA-compliant AI assistant for mental health therapists. Your role is to:

1. SAFETY FIRST: Always prioritize patient safety and crisis detection
2. Support therapeutic goals while maintaining professional boundaries
3. Provide empathetic, non-judgmental responses
4. Document interactions for therapist review
5. Escalate immediately if crisis indicators are detected

CRISIS PROTOCOLS:
- If patient mentions suicide, self-harm, or crisis: IMMEDIATELY escalate
- Provide crisis resources (988 Suicide & Crisis Lifeline)
- Never provide therapy or diagnosis - you support, don't replace therapists
- Stay within your role as a supportive AI assistant

THERAPEUTIC APPROACH:
- Use active listening techniques
- Reflect emotions and validate feelings
- Ask open-ended questions to encourage expression
- Maintain warm, professional tone
- Document significant interactions for therapist review

BOUNDARIES:
- You are NOT a therapist and cannot provide therapy
- You cannot diagnose mental health conditions
- You cannot prescribe medications or treatments
- You support patients between therapy sessions
- Always refer to their therapist for clinical decisions

PRIVACY & COMPLIANCE:
- All conversations are confidential and HIPAA-protected
- Information is shared only with the patient's therapist
- Maintain detailed logs for clinical review
- Never share patient information outside the therapeutic relationship
"""
    
    async def process_message(
        self, 
        patient_message: str, 
        context: MentalHealthContext
    ) -> Tuple[AIResponse, Optional[CrisisAlert]]:
        """Process patient message with crisis detection and therapeutic response."""
        
        # Log the interaction
        await audit_logger.log_access(
            user_id=context.therapist_id,
            patient_id=context.patient_id,
            action="ai_message_processing",
            resource="patient_conversation",
            outcome="started"
        )
        
        try:
            # Step 1: Crisis detection using DSPy
            crisis_result = await self._detect_crisis(patient_message, context)
            
            # Step 2: Generate therapeutic response
            ai_response = await self._generate_therapeutic_response(
                patient_message, context, crisis_result
            )
            
            # Step 3: Create crisis alert if needed
            crisis_alert = None
            if ai_response.escalation_required:
                crisis_alert = await self._create_crisis_alert(
                    patient_message, ai_response, context
                )
            
            # Step 4: Log the conversation entry
            conversation_entry = ConversationEntry(
                timestamp=datetime.utcnow(),
                message_type="ai_response",
                content=ai_response.message,
                risk_indicators=ai_response.crisis_indicators,
                escalation_triggered=ai_response.escalation_required,
                therapist_notified=crisis_alert is not None
            )
            
            # Update context
            context.conversation_history.append(conversation_entry)
            context.patient_risk_level = ai_response.risk_assessment
            
            await audit_logger.log_access(
                user_id=context.therapist_id,
                patient_id=context.patient_id,
                action="ai_message_processing",
                resource="patient_conversation",
                outcome="success",
                details={
                    "risk_level": ai_response.risk_assessment.value,
                    "escalation_required": ai_response.escalation_required,
                    "crisis_indicators": ai_response.crisis_indicators
                }
            )
            
            return ai_response, crisis_alert
            
        except Exception as e:
            await audit_logger.log_access(
                user_id=context.therapist_id,
                patient_id=context.patient_id,
                action="ai_message_processing",
                resource="patient_conversation",
                outcome="failure",
                details={"error": str(e)}
            )
            raise
    
    async def _detect_crisis(self, message: str, context: MentalHealthContext) -> Dict[str, Any]:
        """Detect crisis indicators in patient message."""
        
        # Quick keyword scan for immediate detection
        detected_keywords = [
            keyword for keyword in self.crisis_keywords 
            if keyword.lower() in message.lower()
        ]
        
        # Use DSPy for advanced crisis detection
        conversation_summary = self._summarize_conversation_context(context)
        
        crisis_prediction = self.crisis_detector(
            patient_message=message,
            conversation_history=conversation_summary
        )
        
        return {
            "risk_level": crisis_prediction.risk_assessment,
            "crisis_indicators": list(set(detected_keywords + crisis_prediction.crisis_indicators)),
            "immediate_response": crisis_prediction.immediate_response_needed == "true"
        }
    
    async def _generate_therapeutic_response(
        self, 
        message: str, 
        context: MentalHealthContext, 
        crisis_result: Dict[str, Any]
    ) -> AIResponse:
        """Generate therapeutic response using PydanticAI."""
        
        # Prepare context for AI
        run_context = RunContext(
            patient_id=context.patient_id,
            therapist_id=context.therapist_id,
            conversation_history=context.conversation_history[-10:],  # Last 10 messages
            crisis_detected=crisis_result["immediate_response"],
            therapist_preferences=context.therapist_preferences
        )
        
        # Handle crisis situations with special protocols
        if crisis_result["immediate_response"]:
            crisis_response = await self._handle_crisis_response(message, context)
            return crisis_response
        
        # Generate normal therapeutic response
        response = await self.agent.run(
            user_prompt=f"""
            Patient message: {message}
            
            Context: This is an ongoing conversation with a patient. Provide a supportive,
            therapeutic response that validates their feelings and encourages them to continue
            sharing. Use the therapist's preferred style: {context.therapist_preferences.get('patient_communication_tone', 'warm')}.
            
            Remember: You are supporting them between therapy sessions, not providing therapy.
            """,
            message_history=[],  # Will be populated from context
        )
        
        return response.data
    
    async def _handle_crisis_response(self, message: str, context: MentalHealthContext) -> AIResponse:
        """Handle crisis situations with immediate safety protocols."""
        
        crisis_response = f"""I'm very concerned about what you've shared. Your safety is the most important thing right now.

**Immediate Resources:**
• Crisis Text Line: Text HOME to 741741
• 988 Suicide & Crisis Lifeline: Call or text 988
• Emergency Services: Call 911

I'm notifying your therapist immediately so they can provide the support you need.

You are not alone in this. There are people who want to help you through this difficult time. Please reach out to one of these resources right away.

Is there someone safe you can be with right now?"""

        return AIResponse(
            message=crisis_response,
            risk_assessment=RiskLevel.CRISIS,
            crisis_indicators=["crisis_protocol_activated"],
            therapeutic_techniques_used=["crisis_intervention", "safety_planning"],
            escalation_required=True,
            follow_up_needed=True,
            session_notes=f"CRISIS ALERT: Patient expressed crisis indicators in message: '{message[:100]}...'"
        )
    
    async def _create_crisis_alert(
        self, 
        patient_message: str, 
        ai_response: AIResponse, 
        context: MentalHealthContext
    ) -> CrisisAlert:
        """Create crisis alert for therapist notification."""
        
        # Determine alert type based on indicators
        alert_type = "general_crisis"
        if any(indicator in patient_message.lower() for indicator in ["suicide", "kill myself", "end my life"]):
            alert_type = "suicide_ideation"
        elif any(indicator in patient_message.lower() for indicator in ["cut myself", "hurt myself", "self harm"]):
            alert_type = "self_harm"
        elif any(indicator in patient_message.lower() for indicator in ["voices", "paranoid", "conspiracy"]):
            alert_type = "psychosis_indicators"
        
        # Determine severity
        severity = "critical"
        if ai_response.risk_assessment == RiskLevel.HIGH:
            severity = "high"
        elif ai_response.risk_assessment == RiskLevel.MODERATE:
            severity = "medium"
        
        return CrisisAlert(
            patient_id=context.patient_id,
            alert_type=alert_type,
            severity=severity,
            trigger_message=patient_message,
            ai_assessment=f"Risk Level: {ai_response.risk_assessment.value}. Crisis indicators: {', '.join(ai_response.crisis_indicators)}",
            recommended_action="Immediate therapist contact required. Consider safety planning and crisis intervention.",
            created_at=datetime.utcnow()
        )
    
    def _summarize_conversation_context(self, context: MentalHealthContext) -> str:
        """Summarize conversation context for DSPy processing."""
        if not context.conversation_history:
            return "No previous conversation history."
        
        recent_messages = context.conversation_history[-5:]  # Last 5 messages
        summary = "Recent conversation:\n"
        
        for entry in recent_messages:
            summary += f"- {entry.message_type}: {entry.content[:100]}...\n"
        
        return summary
    
    async def generate_session_summary(self, context: MentalHealthContext) -> str:
        """Generate session summary for therapist review."""
        
        if not context.conversation_history:
            return "No conversation activity to summarize."
        
        # Analyze conversation patterns
        patient_messages = [
            entry for entry in context.conversation_history 
            if entry.message_type == "patient_message"
        ]
        
        ai_responses = [
            entry for entry in context.conversation_history 
            if entry.message_type == "ai_response"
        ]
        
        # Generate structured summary
        summary = f"""
**Session Summary - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}**

**Patient Engagement:**
- Total messages: {len(patient_messages)}
- AI responses: {len(ai_responses)}
- Session duration: {self._calculate_session_duration(context)}

**Risk Assessment:**
- Current risk level: {context.patient_risk_level.value}
- Crisis indicators detected: {len([e for e in context.conversation_history if e.escalation_triggered])}
- Escalations triggered: {sum(1 for e in context.conversation_history if e.escalation_triggered)}

**Key Themes:**
{self._extract_conversation_themes(context)}

**Therapeutic Techniques Used:**
{self._extract_techniques_used(context)}

**Recommendations:**
{self._generate_therapist_recommendations(context)}
"""
        
        return summary
    
    def _calculate_session_duration(self, context: MentalHealthContext) -> str:
        """Calculate session duration from conversation timestamps."""
        if len(context.conversation_history) < 2:
            return "< 5 minutes"
        
        start_time = context.conversation_history[0].timestamp
        end_time = context.conversation_history[-1].timestamp
        duration = end_time - start_time
        
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"
    
    def _extract_conversation_themes(self, context: MentalHealthContext) -> str:
        """Extract main themes from conversation."""
        # This would use more sophisticated NLP in production
        themes = []
        
        all_text = " ".join([
            entry.content for entry in context.conversation_history 
            if entry.message_type == "patient_message"
        ]).lower()
        
        theme_keywords = {
            "anxiety": ["anxious", "worried", "panic", "nervous", "fear"],
            "depression": ["sad", "depressed", "hopeless", "worthless", "empty"],
            "relationships": ["family", "friend", "partner", "relationship", "alone"],
            "work_stress": ["job", "work", "boss", "career", "stress"],
            "trauma": ["trauma", "abuse", "ptsd", "flashback", "trigger"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme.replace("_", " ").title())
        
        return ", ".join(themes) if themes else "General support and check-in"
    
    def _extract_techniques_used(self, context: MentalHealthContext) -> str:
        """Extract therapeutic techniques used during session."""
        techniques = set()
        
        for entry in context.conversation_history:
            if entry.message_type == "ai_response" and hasattr(entry, 'therapeutic_techniques_used'):
                techniques.update(getattr(entry, 'therapeutic_techniques_used', []))
        
        return ", ".join(sorted(techniques)) if techniques else "Active listening, validation"
    
    def _generate_therapist_recommendations(self, context: MentalHealthContext) -> str:
        """Generate recommendations for therapist follow-up."""
        recommendations = []
        
        if context.patient_risk_level in [RiskLevel.HIGH, RiskLevel.CRISIS]:
            recommendations.append("• Immediate follow-up required due to elevated risk level")
        
        crisis_count = sum(1 for e in context.conversation_history if e.escalation_triggered)
        if crisis_count > 0:
            recommendations.append(f"• {crisis_count} crisis alerts triggered - review conversation details")
        
        if len(context.conversation_history) > 20:
            recommendations.append("• Extended conversation - consider scheduling additional session")
        
        if not recommendations:
            recommendations.append("• Regular follow-up per treatment plan")
        
        return "\n".join(recommendations)


# Global instance
mental_health_agent = MentalHealthAgent()