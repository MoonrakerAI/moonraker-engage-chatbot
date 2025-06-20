"""
Sales and booking chatbot for therapist websites.
Focused on appointment booking and lead generation - not therapy.
"""

import asyncio
import re
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import dspy
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..core.config import settings
from ..models.practice import ChatMessage, ConversationMetrics, AppointmentConfig


class ChatbotContext(BaseModel):
    """Context for sales chatbot conversations."""
    practice_id: str
    conversation_id: str
    visitor_info: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    appointment_config: AppointmentConfig
    practice_info: Dict[str, Any] = Field(default_factory=dict)
    current_intent: Optional[str] = None
    collected_info: Dict[str, Any] = Field(default_factory=dict)


class ChatbotResponse(BaseModel):
    """Structured chatbot response."""
    message: str
    intent: str  # booking, question, pricing, services, emergency
    requires_followup: bool = False
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    next_action: Optional[str] = None  # "collect_contact", "show_calendar", "provide_info"
    booking_ready: bool = False


class IntentClassificationSignature(dspy.Signature):
    """DSPy signature for intent classification."""
    visitor_message = dspy.InputField(desc="Visitor's message to the chatbot")
    conversation_context = dspy.InputField(desc="Previous conversation context")
    practice_info = dspy.InputField(desc="Practice information and services")
    intent = dspy.OutputField(desc="Intent: booking, question, pricing, services, emergency, general")
    confidence = dspy.OutputField(desc="Confidence level: high, medium, low")


class BookingAssistantSignature(dspy.Signature):
    """DSPy signature for booking assistance."""
    visitor_message = dspy.InputField(desc="Visitor's booking-related message")
    available_appointment_types = dspy.InputField(desc="Available appointment types")
    practice_hours = dspy.InputField(desc="Practice hours and availability")
    booking_response = dspy.OutputField(desc="Helpful response to guide booking process")
    info_needed = dspy.OutputField(desc="Information still needed: name, email, phone, preferred_time, appointment_type")


class SalesChatbot:
    """Sales and booking chatbot for therapist websites."""
    
    def __init__(self):
        """Initialize the sales chatbot."""
        # Common booking keywords
        self.booking_keywords = [
            "appointment", "schedule", "book", "available", "session",
            "consultation", "meeting", "time", "calendar", "availability"
        ]
        
        # Service inquiry keywords
        self.service_keywords = [
            "therapy", "counseling", "treatment", "help", "services",
            "what do you do", "specialize", "approach", "methods"
        ]
        
        # Pricing keywords
        self.pricing_keywords = [
            "cost", "price", "fee", "insurance", "payment", "charge",
            "how much", "affordable", "billing", "copay"
        ]
        
        # Emergency keywords (redirect appropriately)
        self.emergency_keywords = [
            "emergency", "crisis", "suicide", "harm", "urgent", "help me"
        ]
        
        # Initialize DSPy modules
        self.intent_classifier = dspy.ChainOfThought(IntentClassificationSignature)
        self.booking_assistant = dspy.ChainOfThought(BookingAssistantSignature)
        
        # Initialize PydanticAI agent
        self.agent = Agent(
            model=settings.default_ai_model,
            result_type=ChatbotResponse,
            system_prompt=self._get_system_prompt(),
            retries=2
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the sales chatbot."""
        return """
You are a helpful sales and booking assistant for a therapy practice. Your role is to:

1. HELP VISITORS BOOK APPOINTMENTS: Guide them through the scheduling process
2. ANSWER BASIC QUESTIONS: About services, location, hours, and general practice info
3. COLLECT CONTACT INFORMATION: For lead generation and follow-up
4. MAINTAIN PROFESSIONAL TONE: Warm, welcoming, and non-clinical

BOOKING PROCESS:
- Ask for preferred appointment type (initial consultation, individual therapy, etc.)
- Collect name, email, and phone number
- Help them find available times
- Confirm appointment details
- Provide next steps and confirmation

WHAT YOU CAN DISCUSS:
- Practice services and specializations
- Appointment types and scheduling
- Location and hours
- General pricing and insurance info
- Contact information and next steps

WHAT YOU CANNOT DO:
- Provide therapy or clinical advice
- Diagnose mental health conditions
- Give specific treatment recommendations
- Handle complex insurance questions (refer to staff)
- Schedule without proper contact information

EMERGENCY PROTOCOL:
If someone mentions crisis/emergency/suicide:
"I'm concerned about your safety. For immediate help:
• Call 988 (Suicide & Crisis Lifeline)
• Call 911 for emergencies
• Contact your local crisis center
Our staff can also help connect you with immediate resources."

TONE: Professional but warm, helpful, and focused on getting them scheduled or connected with the right person.
"""
    
    async def process_message(
        self, 
        visitor_message: str, 
        context: ChatbotContext
    ) -> Tuple[ChatbotResponse, ChatbotContext]:
        """Process visitor message and generate appropriate response."""
        
        try:
            # Step 1: Classify intent
            intent_result = await self._classify_intent(visitor_message, context)
            
            # Step 2: Handle emergency situations first
            if intent_result["intent"] == "emergency":
                response = await self._handle_emergency(visitor_message, context)
                return response, context
            
            # Step 3: Generate appropriate response based on intent
            if intent_result["intent"] == "booking":
                response = await self._handle_booking_intent(visitor_message, context)
            elif intent_result["intent"] == "services":
                response = await self._handle_services_inquiry(visitor_message, context)
            elif intent_result["intent"] == "pricing":
                response = await self._handle_pricing_inquiry(visitor_message, context)
            else:
                response = await self._handle_general_inquiry(visitor_message, context)
            
            # Step 4: Update context
            context.current_intent = intent_result["intent"]
            context.collected_info.update(response.collected_data)
            
            # Step 5: Add to conversation history
            visitor_msg = ChatMessage(
                id=f"msg_{datetime.utcnow().timestamp()}",
                conversation_id=context.conversation_id,
                sender="visitor",
                message=visitor_message,
                timestamp=datetime.utcnow(),
                intent=intent_result["intent"]
            )
            
            bot_msg = ChatMessage(
                id=f"msg_{datetime.utcnow().timestamp()}_bot",
                conversation_id=context.conversation_id,
                sender="bot",
                message=response.message,
                timestamp=datetime.utcnow(),
                intent=response.intent
            )
            
            context.conversation_history.extend([visitor_msg, bot_msg])
            
            return response, context
            
        except Exception as e:
            # Fallback response for errors
            fallback_response = ChatbotResponse(
                message="I apologize, but I'm having some technical difficulties. Please feel free to call us directly or try again in a moment. For urgent matters, you can reach us at our main number.",
                intent="error",
                requires_followup=True
            )
            return fallback_response, context
    
    async def _classify_intent(self, message: str, context: ChatbotContext) -> Dict[str, str]:
        """Classify visitor message intent."""
        
        # Quick keyword-based classification first
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in self.emergency_keywords):
            return {"intent": "emergency", "confidence": "high"}
        
        if any(keyword in message_lower for keyword in self.booking_keywords):
            return {"intent": "booking", "confidence": "high"}
        
        if any(keyword in message_lower for keyword in self.pricing_keywords):
            return {"intent": "pricing", "confidence": "medium"}
        
        if any(keyword in message_lower for keyword in self.service_keywords):
            return {"intent": "services", "confidence": "medium"}
        
        # Use DSPy for more nuanced classification
        conversation_summary = self._get_conversation_summary(context)
        practice_summary = self._get_practice_summary(context)
        
        classification = self.intent_classifier(
            visitor_message=message,
            conversation_context=conversation_summary,
            practice_info=practice_summary
        )
        
        return {
            "intent": classification.intent,
            "confidence": classification.confidence
        }
    
    async def _handle_emergency(self, message: str, context: ChatbotContext) -> ChatbotResponse:
        """Handle emergency situations."""
        emergency_response = """I'm concerned about your safety and want to make sure you get immediate help.

**For immediate support:**
• **Crisis Text Line**: Text HOME to 741741
• **988 Suicide & Crisis Lifeline**: Call or text 988
• **Emergency Services**: Call 911 if you're in immediate danger

Our practice staff can also help connect you with crisis resources. Would you like me to have someone call you today?"""

        return ChatbotResponse(
            message=emergency_response,
            intent="emergency",
            requires_followup=True,
            next_action="notify_staff"
        )
    
    async def _handle_booking_intent(self, message: str, context: ChatbotContext) -> ChatbotResponse:
        """Handle appointment booking requests."""
        
        # Check what information we already have
        collected = context.collected_info
        appointment_config = context.appointment_config
        
        # Use DSPy to determine what we need
        booking_result = self.booking_assistant(
            visitor_message=message,
            available_appointment_types=", ".join(appointment_config.appointment_types),
            practice_hours=f"Available {', '.join(appointment_config.available_days)} from {appointment_config.booking_hours_start} to {appointment_config.booking_hours_end}"
        )
        
        # Extract any contact info from the message
        new_info = self._extract_contact_info(message)
        
        # Determine response based on what we have
        if not collected.get("name") and not new_info.get("name"):
            response_message = f"I'd be happy to help you schedule an appointment! We offer {', '.join(appointment_config.appointment_types)}. May I start by getting your name?"
            next_action = "collect_name"
            
        elif not collected.get("email") and not new_info.get("email"):
            response_message = f"Thanks {collected.get('name', 'for your interest')}! What's the best email address to send your appointment confirmation?"
            next_action = "collect_email"
            
        elif not collected.get("phone") and not new_info.get("phone"):
            response_message = "Great! And what's a good phone number where we can reach you?"
            next_action = "collect_phone"
            
        elif not collected.get("appointment_type"):
            response_message = f"Perfect! What type of appointment are you looking for?\n\n{self._format_appointment_types(appointment_config.appointment_types)}"
            next_action = "collect_appointment_type"
            
        else:
            # Ready to show calendar
            response_message = f"Excellent! I have all your information. Let me show you our available times for {collected.get('appointment_type', 'your appointment')}. What day works best for you this week or next?"
            next_action = "show_calendar"
            
        return ChatbotResponse(
            message=response_message,
            intent="booking",
            collected_data=new_info,
            next_action=next_action,
            booking_ready=(next_action == "show_calendar"),
            requires_followup=True
        )
    
    async def _handle_services_inquiry(self, message: str, context: ChatbotContext) -> ChatbotResponse:
        """Handle questions about services."""
        practice_info = context.practice_info
        
        services_response = f"""We offer a range of mental health services including:

{self._format_services_list(practice_info.get('services', []))}

Our approach focuses on {practice_info.get('approach', 'evidence-based therapy tailored to your individual needs')}.

We provide both in-person and online sessions, and we accept most major insurance plans.

Would you like to schedule a consultation to discuss how we can help you?"""

        return ChatbotResponse(
            message=services_response,
            intent="services",
            requires_followup=True,
            next_action="encourage_booking"
        )
    
    async def _handle_pricing_inquiry(self, message: str, context: ChatbotContext) -> ChatbotResponse:
        """Handle pricing and insurance questions."""
        practice_info = context.practice_info
        
        pricing_response = f"""Here's information about our fees and insurance:

**Insurance**: We accept most major insurance plans including {practice_info.get('insurance_accepted', 'most major providers')}.

**Session Fees**: Individual therapy sessions typically range from $120-180, depending on the type of session and your therapist's credentials.

**Payment Options**: We accept insurance, HSA/FSA, and self-pay options.

I'd recommend scheduling a brief consultation where we can:
• Verify your specific insurance benefits
• Discuss your needs and goals
• Provide exact pricing for your situation

Would you like me to help you schedule that consultation?"""

        return ChatbotResponse(
            message=pricing_response,
            intent="pricing",
            requires_followup=True,
            next_action="encourage_booking"
        )
    
    async def _handle_general_inquiry(self, message: str, context: ChatbotContext) -> ChatbotResponse:
        """Handle general questions and inquiries."""
        practice_info = context.practice_info
        
        # Generate contextual response
        general_response = f"""Thanks for reaching out! I'm here to help you learn about our practice and schedule an appointment.

**About Us**: {practice_info.get('practice_name', 'Our practice')} provides {practice_info.get('service_delivery', 'in-person and online')} therapy services.

**Location**: {practice_info.get('address', 'Contact us for location details')}
**Hours**: {practice_info.get('hours_of_operation', 'Mon-Fri 9a-5p')}

I can help you with:
• Scheduling appointments
• Information about our services
• Insurance and pricing questions
• Connecting you with the right therapist

What would be most helpful for you today?"""

        return ChatbotResponse(
            message=general_response,
            intent="general",
            requires_followup=True
        )
    
    def _extract_contact_info(self, message: str) -> Dict[str, str]:
        """Extract contact information from visitor message."""
        info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            info["email"] = email_match.group()
        
        # Extract phone (basic patterns)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}\b'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, message)
            if phone_match:
                info["phone"] = phone_match.group()
                break
        
        # Extract name (if they say "My name is..." or "I'm...")
        name_patterns = [
            r'my name is ([A-Za-z\s]+)',
            r'i\'m ([A-Za-z\s]+)',
            r'this is ([A-Za-z\s]+)'
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, message.lower())
            if name_match:
                info["name"] = name_match.group(1).strip().title()
                break
        
        return info
    
    def _format_appointment_types(self, types: List[str]) -> str:
        """Format appointment types for display."""
        return "\n".join([f"• {apt_type}" for apt_type in types])
    
    def _format_services_list(self, services: List[str]) -> str:
        """Format services list for display."""
        if not services:
            return "• Individual therapy\n• Couples counseling\n• Family therapy"
        return "\n".join([f"• {service}" for service in services])
    
    def _get_conversation_summary(self, context: ChatbotContext) -> str:
        """Get conversation summary for context."""
        if not context.conversation_history:
            return "This is the start of the conversation."
        
        recent_messages = context.conversation_history[-6:]  # Last 3 exchanges
        summary = "Recent conversation:\n"
        
        for msg in recent_messages:
            sender = "Visitor" if msg.sender == "visitor" else "Bot"
            summary += f"{sender}: {msg.message[:100]}...\n"
        
        return summary
    
    def _get_practice_summary(self, context: ChatbotContext) -> str:
        """Get practice information summary."""
        practice_info = context.practice_info
        return f"""
Practice: {practice_info.get('practice_name', 'Therapy Practice')}
Services: {practice_info.get('service_delivery', 'In-person and online therapy')}
Hours: {practice_info.get('hours_of_operation', 'Mon-Fri 9a-5p')}
Insurance: {'Accepted' if practice_info.get('accepts_insurance') else 'Contact for details'}
"""

    async def generate_conversation_summary(self, context: ChatbotContext) -> str:
        """Generate conversation summary for analytics."""
        if not context.conversation_history:
            return "No conversation activity."
        
        visitor_messages = [msg for msg in context.conversation_history if msg.sender == "visitor"]
        
        summary = f"""
**Conversation Summary**
- Total messages: {len(context.conversation_history)}
- Visitor messages: {len(visitor_messages)}
- Primary intent: {context.current_intent or 'general'}
- Information collected: {', '.join(context.collected_info.keys()) if context.collected_info else 'None'}
- Booking status: {'Ready to book' if context.collected_info.get('name') and context.collected_info.get('email') else 'In progress'}
"""
        
        return summary


# Global instance
sales_chatbot = SalesChatbot()