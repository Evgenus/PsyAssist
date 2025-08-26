"""
Escalation agent for PsyAssist AI.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base_agent import BasePsyAssistAgent
from ..schemas.session import Session, SessionState
from ..schemas.events import EventType, EventPriority
from ..schemas.resources import Resource
from ..config.prompts import EscalationPrompt
from ..tools import WarmTransferAPI, DirectoryLookup


class EscalationAgent(BasePsyAssistAgent):
    """Escalation agent for handling transitions to human support."""
    
    def __init__(self, warm_transfer_api: WarmTransferAPI = None, directory_lookup: DirectoryLookup = None, **kwargs):
        prompt_config = EscalationPrompt()
        super().__init__(
            name="Escalation",
            prompt_config=prompt_config,
            **kwargs
        )
        self.warm_transfer_api = warm_transfer_api or WarmTransferAPI()
        self.directory_lookup = directory_lookup or DirectoryLookup()
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message during escalation."""
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
        
        # Process escalation
        escalation_response = await self._handle_escalation(session, message, context)
        
        # Update session
        session = self.update_session(session)
        
        return self.format_response(
            escalation_response,
            {
                'escalation_handled': True,
                'risk_assessed': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value
            }
        )
    
    async def _handle_escalation(self, session: Session, message: str, context: Dict[str, Any]) -> str:
        """Handle the escalation process."""
        # Check if user is ready for escalation
        if self._is_user_ready_for_escalation(message):
            return await self._initiate_transfer(session, context)
        elif self._is_user_not_ready(message):
            return await self._provide_support_while_waiting(session, message, context)
        else:
            return await self._explain_escalation_benefits(session, context)
    
    async def _handle_emergency(self, session: Session, message: str, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situations."""
        # Update session state
        session.state = SessionState.ESCALATE
        session.metadata['emergency_triggered'] = True
        session = self.update_session(session)
        
        # Get emergency resources
        location = session.metadata.get('location', 'US')
        emergency_resources = await self.directory_lookup.get_crisis_resources(location)
        
        # Create emergency response
        emergency_response = "I'm very concerned about your safety. You're not alone, and help is available right now. "
        
        if emergency_resources:
            primary_resource = emergency_resources[0]
            emergency_response += f"\n\nPlease call {primary_resource.name} immediately: "
            if primary_resource.phone_number:
                emergency_response += f"{primary_resource.phone_number}"
            elif primary_resource.text_number:
                emergency_response += f"Text {primary_resource.text_number}"
        
        emergency_response += "\n\nI'll stay with you until you're connected with help. Would you like me to help you find local resources?"
        
        return self.format_response(
            emergency_response,
            {
                'emergency_escalation': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value,
                'emergency_resources_provided': bool(emergency_resources),
                'next_state': SessionState.ESCALATE.value
            }
        )
    
    def _is_user_ready_for_escalation(self, message: str) -> bool:
        """Check if user is ready for escalation."""
        ready_indicators = [
            'yes', 'okay', 'ok', 'sure', 'ready', 'let\'s do it', 'connect me',
            'transfer me', 'talk to someone', 'speak to someone', 'counselor'
        ]
        
        message_lower = message.lower().strip()
        return any(indicator in message_lower for indicator in ready_indicators)
    
    def _is_user_not_ready(self, message: str) -> bool:
        """Check if user is not ready for escalation."""
        not_ready_indicators = [
            'no', 'not yet', 'not ready', 'later', 'maybe later', 'i don\'t know',
            'i\'m not sure', 'need to think', 'scared', 'nervous', 'anxious'
        ]
        
        message_lower = message.lower().strip()
        return any(indicator in message_lower for indicator in not_ready_indicators)
    
    async def _initiate_transfer(self, session: Session, context: Dict[str, Any]) -> str:
        """Initiate the warm transfer process."""
        # Get appropriate resource
        location = session.metadata.get('location', 'US')
        resources = await self.directory_lookup.get_mental_health_resources(location)
        
        if not resources:
            return "I'm having trouble finding available resources right now. Please call 988 or your local crisis line for immediate support."
        
        # Select primary resource
        primary_resource = resources[0]
        
        # Initiate transfer
        transfer_context = {
            'session_id': session.session_id,
            'user_needs': session.metadata.get('triage_info', {}),
            'risk_level': session.metadata.get('last_risk_assessment', {}).get('severity', 'UNKNOWN')
        }
        
        transfer_result = await self.warm_transfer_api.initiate_transfer(
            session.session_id, primary_resource, transfer_context
        )
        
        if transfer_result.get('status') == 'initiated':
            session.metadata['transfer_id'] = transfer_result['transfer_id']
            session.metadata['transfer_initiated'] = True
            
            response = (
                f"Great! I'm connecting you with {primary_resource.name}. "
                f"They should be available in about {transfer_result.get('estimated_wait_time', 5)} minutes. "
                f"I'll stay with you until the connection is established. "
                f"What would you like to focus on when you speak with them?"
            )
        else:
            response = (
                "I'm having trouble connecting you right now. "
                f"Please call {primary_resource.name} directly at {primary_resource.phone_number or 'their listed number'}. "
                "I'm here to support you while you make that call."
            )
        
        return response
    
    async def _provide_support_while_waiting(self, session: Session, message: str, context: Dict[str, Any]) -> str:
        """Provide support while the user considers escalation."""
        response = (
            "I understand that this might feel overwhelming or scary. That's completely normal. "
            "You don't have to make any decisions right now. "
            "I'm here to support you, and we can take this at your own pace. "
            "What would be most helpful for you right now?"
        )
        
        return response
    
    async def _explain_escalation_benefits(self, session: Session, context: Dict[str, Any]) -> str:
        """Explain the benefits of escalation."""
        response = (
            "I want to make sure you get the best possible support. "
            "A trained counselor can provide more specialized help and has more tools and resources available. "
            "They can also help you develop a longer-term plan for managing what you're going through. "
            "Would you be open to talking with someone who has more training in this area?"
        )
        
        return response
    
    async def check_transfer_status(self, session: Session) -> Dict[str, Any]:
        """Check the status of an active transfer."""
        transfer_id = session.metadata.get('transfer_id')
        if not transfer_id:
            return {'status': 'no_transfer'}
        
        status_info = await self.warm_transfer_api.check_transfer_status(transfer_id)
        
        if status_info['status'] == 'connected':
            session.state = SessionState.CLOSE
            session.metadata['transfer_completed'] = True
            session = self.update_session(session)
        
        return status_info
