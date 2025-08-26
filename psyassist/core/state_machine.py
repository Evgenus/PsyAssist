"""
State machine for PsyAssist AI session orchestration.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from ..schemas.session import Session, SessionState
from ..schemas.events import EventType, EventPriority
from ..agents import (
    GreeterAgent, EmpathyAgent, TherapyGuideAgent, 
    RiskAssessmentAgent, ResourceAgent, EscalationAgent
)


class StateTransition(Enum):
    """Possible state transitions."""
    INIT_TO_CONSENTED = "INIT_TO_CONSENTED"
    CONSENTED_TO_TRIAGE = "CONSENTED_TO_TRIAGE"
    TRIAGE_TO_SUPPORT = "TRIAGE_TO_SUPPORT"
    SUPPORT_TO_RISK_CHECK = "SUPPORT_TO_RISK_CHECK"
    RISK_CHECK_TO_SUPPORT = "RISK_CHECK_TO_SUPPORT"
    SUPPORT_TO_RESOURCES = "SUPPORT_TO_RESOURCES"
    ANY_TO_ESCALATE = "ANY_TO_ESCALATE"
    ANY_TO_CLOSE = "ANY_TO_CLOSE"


class StateMachine:
    """State machine for managing PsyAssist AI session flow."""
    
    def __init__(self):
        self.agents = {
            SessionState.INIT: GreeterAgent(),
            SessionState.CONSENTED: GreeterAgent(),
            SessionState.TRIAGE: GreeterAgent(),
            SessionState.SUPPORT_LOOP: EmpathyAgent(),
            SessionState.RISK_CHECK: RiskAssessmentAgent(),
            SessionState.RESOURCES: ResourceAgent(),
            SessionState.ESCALATE: EscalationAgent(),
            SessionState.CLOSE: None  # No agent for close state
        }
        
        self.transitions = self._build_transitions()
    
    def _build_transitions(self) -> Dict[StateTransition, Callable]:
        """Build the transition rules."""
        return {
            StateTransition.INIT_TO_CONSENTED: self._init_to_consented,
            StateTransition.CONSENTED_TO_TRIAGE: self._consented_to_triage,
            StateTransition.TRIAGE_TO_SUPPORT: self._triage_to_support,
            StateTransition.SUPPORT_TO_RISK_CHECK: self._support_to_risk_check,
            StateTransition.RISK_CHECK_TO_SUPPORT: self._risk_check_to_support,
            StateTransition.SUPPORT_TO_RESOURCES: self._support_to_resources,
            StateTransition.ANY_TO_ESCALATE: self._any_to_escalate,
            StateTransition.ANY_TO_CLOSE: self._any_to_close
        }
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message through the state machine."""
        context = context or {}
        
        # Get current agent
        current_agent = self.agents.get(session.state)
        if not current_agent:
            return {
                'content': 'Session has ended.',
                'agent': 'System',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'session_ended': True}
            }
        
        # Process with current agent
        response = await current_agent.process_message(session, message, context)
        
        # Determine next state
        next_state = await self._determine_next_state(session, response, context)
        
        # Transition if needed
        if next_state and next_state != session.state:
            await self._transition_state(session, next_state, response, context)
        
        return response
    
    async def _determine_next_state(self, session: Session, response: Dict[str, Any], context: Dict[str, Any]) -> Optional[SessionState]:
        """Determine the next state based on current state and response."""
        current_state = session.state
        metadata = response.get('metadata', {})
        
        # Check for emergency escalation
        if metadata.get('emergency_escalation') or metadata.get('escalation_triggered'):
            return SessionState.ESCALATE
        
        # Check for session close
        if metadata.get('session_closed') or metadata.get('consent_denied'):
            return SessionState.CLOSE
        
        # State-specific transitions
        if current_state == SessionState.INIT:
            if metadata.get('consent_granted'):
                return SessionState.CONSENTED
        
        elif current_state == SessionState.CONSENTED:
            if metadata.get('triage_completed'):
                return SessionState.TRIAGE
        
        elif current_state == SessionState.TRIAGE:
            if metadata.get('triage_completed'):
                return SessionState.SUPPORT_LOOP
        
        elif current_state == SessionState.SUPPORT_LOOP:
            # Check if risk assessment is needed
            if self._should_trigger_risk_check(session, metadata):
                return SessionState.RISK_CHECK
            
            # Check if resources are requested
            if metadata.get('resources_requested'):
                return SessionState.RESOURCES
        
        elif current_state == SessionState.RISK_CHECK:
            # Return to support loop after risk assessment
            return SessionState.SUPPORT_LOOP
        
        elif current_state == SessionState.RESOURCES:
            # Return to support loop after providing resources
            return SessionState.SUPPORT_LOOP
        
        elif current_state == SessionState.ESCALATE:
            # Stay in escalation until transfer is complete
            if metadata.get('transfer_completed'):
                return SessionState.CLOSE
        
        return None  # Stay in current state
    
    def _should_trigger_risk_check(self, session: Session, metadata: Dict[str, Any]) -> bool:
        """Determine if a risk check should be triggered."""
        # Check message count
        if session.message_count % 3 == 0:
            return True
        
        # Check if there are risk flags
        if session.risk_flags:
            return True
        
        # Check if risk was detected in current response
        if metadata.get('risk_level') in ['MEDIUM', 'HIGH', 'CRITICAL']:
            return True
        
        return False
    
    async def _transition_state(self, session: Session, new_state: SessionState, response: Dict[str, Any], context: Dict[str, Any]):
        """Transition to a new state."""
        old_state = session.state
        session.state = new_state
        
        # Update session metadata
        session.metadata['state_transitions'] = session.metadata.get('state_transitions', [])
        session.metadata['state_transitions'].append({
            'from_state': old_state.value,
            'to_state': new_state.value,
            'timestamp': datetime.utcnow().isoformat(),
            'trigger': response.get('metadata', {})
        })
        
        # Update session
        session.updated_at = datetime.utcnow()
    
    # Transition rule implementations
    def _init_to_consented(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition from INIT to CONSENTED is valid."""
        return session.consent_status.value == 'GRANTED'
    
    def _consented_to_triage(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition from CONSENTED to TRIAGE is valid."""
        return 'triage_info' in session.metadata
    
    def _triage_to_support(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition from TRIAGE to SUPPORT_LOOP is valid."""
        return session.metadata.get('triage_completed', False)
    
    def _support_to_risk_check(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition from SUPPORT_LOOP to RISK_CHECK is valid."""
        return self._should_trigger_risk_check(session, {})
    
    def _risk_check_to_support(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition from RISK_CHECK to SUPPORT_LOOP is valid."""
        return True  # Always return to support after risk check
    
    def _support_to_resources(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition from SUPPORT_LOOP to RESOURCES is valid."""
        return context.get('resources_requested', False)
    
    def _any_to_escalate(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition to ESCALATE is valid from any state."""
        return context.get('escalation_required', False)
    
    def _any_to_close(self, session: Session, context: Dict[str, Any]) -> bool:
        """Check if transition to CLOSE is valid from any state."""
        return context.get('session_ended', False)
    
    def get_current_agent(self, session: Session):
        """Get the agent for the current session state."""
        return self.agents.get(session.state)
    
    def get_available_transitions(self, session: Session) -> list:
        """Get available transitions from the current state."""
        available = []
        
        for transition in StateTransition:
            if transition.value.startswith('ANY_TO_'):
                available.append(transition.value)
            elif session.state.value in transition.value:
                available.append(transition.value)
        
        return available
    
    def validate_transition(self, from_state: SessionState, to_state: SessionState) -> bool:
        """Validate if a state transition is allowed."""
        # Define valid transitions
        valid_transitions = {
            SessionState.INIT: [SessionState.CONSENTED, SessionState.ESCALATE, SessionState.CLOSE],
            SessionState.CONSENTED: [SessionState.TRIAGE, SessionState.ESCALATE, SessionState.CLOSE],
            SessionState.TRIAGE: [SessionState.SUPPORT_LOOP, SessionState.ESCALATE, SessionState.CLOSE],
            SessionState.SUPPORT_LOOP: [SessionState.RISK_CHECK, SessionState.RESOURCES, SessionState.ESCALATE, SessionState.CLOSE],
            SessionState.RISK_CHECK: [SessionState.SUPPORT_LOOP, SessionState.ESCALATE, SessionState.CLOSE],
            SessionState.RESOURCES: [SessionState.SUPPORT_LOOP, SessionState.ESCALATE, SessionState.CLOSE],
            SessionState.ESCALATE: [SessionState.CLOSE],
            SessionState.CLOSE: []
        }
        
        return to_state in valid_transitions.get(from_state, [])
