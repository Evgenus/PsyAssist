"""
Greeter agent for PsyAssist AI.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .base_agent import BasePsyAssistAgent
from ..schemas.session import Session, SessionState, ConsentStatus
from ..schemas.events import EventType, EventPriority
from ..config.prompts import GreeterPrompt
from ..config.settings import settings


class GreeterAgent(BasePsyAssistAgent):
    """Greeter agent for welcoming users and obtaining consent."""
    
    def __init__(self, **kwargs):
        prompt_config = GreeterPrompt()
        super().__init__(
            name="Greeter",
            prompt_config=prompt_config,
            **kwargs
        )
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and return a response."""
        context = context or {}
        
        # Validate session
        if not self.validate_session(session):
            return self.format_response(
                "I'm sorry, but this session has expired or reached its limit. Please start a new session.",
                {'error': 'session_invalid'}
            )
        
        # Assess risk first
        risk_assessment = await self.assess_risk(message, session)
        
        # Handle emergency situations immediately
        if risk_assessment['is_emergency']:
            return await self._handle_emergency(session, message, risk_assessment)
        
        # Process based on session state
        if session.state == SessionState.INIT:
            return await self._handle_initial_greeting(session, message, context)
        elif session.state == SessionState.CONSENTED:
            return await self._handle_consent_granted(session, message, context)
        else:
            return await self._handle_general_greeting(session, message, context)
    
    async def _handle_initial_greeting(self, session: Session, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the initial greeting and consent request."""
        # Check if user has already given consent
        if self._is_consent_granted(message):
            session.consent_status = ConsentStatus.GRANTED
            session.state = SessionState.CONSENTED
            session = self.update_session(session)
            
            return self.format_response(
                "Thank you for your consent. I'm here to provide emotional support and coping strategies. "
                "What brings you here today?",
                {
                    'consent_granted': True,
                    'next_state': SessionState.TRIAGE.value
                }
            )
        
        # Check if user has denied consent
        if self._is_consent_denied(message):
            session.consent_status = ConsentStatus.DENIED
            session.state = SessionState.CLOSE
            session = self.update_session(session)
            
            return self.format_response(
                "I understand and respect your decision. If you change your mind, you're welcome to return anytime. "
                "Take care.",
                {
                    'consent_denied': True,
                    'session_closed': True
                }
            )
        
        # Present consent information
        consent_message = self.prompt_config.consent_template
        
        return self.format_response(
            consent_message,
            {
                'consent_pending': True,
                'state': SessionState.INIT.value
            }
        )
    
    async def _handle_consent_granted(self, session: Session, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle messages after consent has been granted."""
        # Conduct initial triage
        triage_info = await self._conduct_triage(session, message)
        
        # Update session with triage information
        session.metadata['triage_info'] = triage_info
        session.state = SessionState.TRIAGE
        session = self.update_session(session)
        
        # Create triage response
        triage_response = await self._create_triage_response(triage_info)
        
        return self.format_response(
            triage_response,
            {
                'triage_completed': True,
                'next_state': SessionState.SUPPORT_LOOP.value,
                'triage_info': triage_info
            }
        )
    
    async def _handle_general_greeting(self, session: Session, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general greeting messages."""
        # Simple acknowledgment and redirection
        return self.format_response(
            "I'm here to help. What would you like to talk about?",
            {
                'greeting_acknowledged': True,
                'state': session.state.value
            }
        )
    
    async def _handle_emergency(self, session: Session, message: str, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situations."""
        # Update session state
        session.state = SessionState.ESCALATE
        session.metadata['emergency_triggered'] = True
        session = self.update_session(session)
        
        # Get emergency number
        location = session.metadata.get('location', 'US')
        emergency_number = await self._get_emergency_number(location)
        
        # Create emergency response
        emergency_response = self.prompt_config.crisis_response_template.format(
            emergency_number=emergency_number
        )
        
        return self.format_response(
            emergency_response,
            {
                'emergency_escalation': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value,
                'emergency_number': emergency_number,
                'next_state': SessionState.ESCALATE.value
            }
        )
    
    def _is_consent_granted(self, message: str) -> bool:
        """Check if user has granted consent."""
        consent_indicators = [
            'yes', 'i consent', 'i agree', 'okay', 'ok', 'sure', 'proceed',
            'continue', 'start', 'begin', 'ready', 'go ahead'
        ]
        
        message_lower = message.lower().strip()
        return any(indicator in message_lower for indicator in consent_indicators)
    
    def _is_consent_denied(self, message: str) -> bool:
        """Check if user has denied consent."""
        denial_indicators = [
            'no', 'i decline', 'i don\'t consent', 'not now', 'later',
            'maybe later', 'i\'m not sure', 'i need to think about it'
        ]
        
        message_lower = message.lower().strip()
        return any(indicator in message_lower for indicator in denial_indicators)
    
    async def _conduct_triage(self, session: Session, message: str) -> Dict[str, Any]:
        """Conduct initial triage to understand user needs."""
        # Analyze message for key themes and urgency
        triage_info = {
            'primary_concern': self._identify_primary_concern(message),
            'urgency_level': self._assess_urgency(message),
            'support_type': self._identify_support_type(message),
            'user_state': self._assess_user_state(message),
            'triage_timestamp': datetime.utcnow().isoformat()
        }
        
        return triage_info
    
    def _identify_primary_concern(self, message: str) -> str:
        """Identify the primary concern from the message."""
        message_lower = message.lower()
        
        # Define concern categories
        concerns = {
            'depression': ['sad', 'depressed', 'hopeless', 'worthless', 'empty', 'numb'],
            'anxiety': ['anxious', 'worried', 'nervous', 'panic', 'fear', 'stress'],
            'relationship': ['relationship', 'partner', 'family', 'friend', 'breakup', 'divorce'],
            'work': ['work', 'job', 'career', 'boss', 'colleague', 'stress'],
            'grief': ['loss', 'grief', 'death', 'died', 'passed away', 'missing'],
            'trauma': ['trauma', 'abuse', 'assault', 'accident', 'ptsd'],
            'substance': ['alcohol', 'drugs', 'addiction', 'substance', 'drinking'],
            'general': ['help', 'support', 'talk', 'feeling', 'emotion']
        }
        
        for concern, keywords in concerns.items():
            if any(keyword in message_lower for keyword in keywords):
                return concern
        
        return 'general'
    
    def _assess_urgency(self, message: str) -> str:
        """Assess the urgency level of the situation."""
        message_lower = message.lower()
        
        high_urgency_indicators = [
            'right now', 'immediately', 'urgent', 'emergency', 'crisis',
            'can\'t take it', 'breaking point', 'last straw'
        ]
        
        medium_urgency_indicators = [
            'soon', 'today', 'tonight', 'this week', 'recently',
            'getting worse', 'struggling', 'difficult'
        ]
        
        if any(indicator in message_lower for indicator in high_urgency_indicators):
            return 'high'
        elif any(indicator in message_lower for indicator in medium_urgency_indicators):
            return 'medium'
        else:
            return 'low'
    
    def _identify_support_type(self, message: str) -> str:
        """Identify the type of support needed."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['listen', 'talk', 'vent']):
            return 'listening'
        elif any(word in message_lower for word in ['advice', 'help', 'solution']):
            return 'guidance'
        elif any(word in message_lower for word in ['cope', 'manage', 'handle']):
            return 'coping'
        elif any(word in message_lower for word in ['resource', 'referral', 'professional']):
            return 'referral'
        else:
            return 'general'
    
    def _assess_user_state(self, message: str) -> str:
        """Assess the current emotional state of the user."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['crisis', 'emergency', 'urgent']):
            return 'crisis'
        elif any(word in message_lower for word in ['overwhelmed', 'desperate', 'hopeless']):
            return 'distressed'
        elif any(word in message_lower for word in ['confused', 'unsure', 'lost']):
            return 'uncertain'
        elif any(word in message_lower for word in ['okay', 'fine', 'managing']):
            return 'stable'
        else:
            return 'neutral'
    
    async def _create_triage_response(self, triage_info: Dict[str, Any]) -> str:
        """Create a response based on triage information."""
        concern = triage_info['primary_concern']
        urgency = triage_info['urgency_level']
        support_type = triage_info['support_type']
        
        # Base acknowledgment
        response = "I hear you and I'm here to support you. "
        
        # Add concern-specific acknowledgment
        concern_acknowledgments = {
            'depression': "It sounds like you're going through a really difficult time. ",
            'anxiety': "I can sense that you're feeling overwhelmed and anxious. ",
            'relationship': "Relationship challenges can be incredibly painful and confusing. ",
            'work': "Work-related stress can take a significant toll on our well-being. ",
            'grief': "Loss and grief are among the most difficult experiences we face. ",
            'trauma': "Trauma can have a profound impact on how we feel and function. ",
            'substance': "Struggling with substance use can feel isolating and overwhelming. ",
            'general': "It sounds like you're going through a challenging time. "
        }
        
        response += concern_acknowledgments.get(concern, concern_acknowledgments['general'])
        
        # Add urgency acknowledgment
        if urgency == 'high':
            response += "I want you to know that you're not alone, and help is available. "
        elif urgency == 'medium':
            response += "It's important to address these feelings and get the support you need. "
        else:
            response += "It's good that you're reaching out for support. "
        
        # Add next steps
        response += "I'm here to listen and provide support. What would be most helpful for you right now?"
        
        return response
    
    async def _get_emergency_number(self, location: str) -> str:
        """Get emergency number for the location."""
        # This would integrate with the HotlineRouter tool
        # For now, return default
        return '911'
