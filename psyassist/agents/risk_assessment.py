"""
RiskAssessment agent for PsyAssist AI.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base_agent import BasePsyAssistAgent
from ..schemas.session import Session, SessionState
from ..schemas.events import EventType, EventPriority
from ..config.prompts import RiskAssessmentPrompt


class RiskAssessmentAgent(BasePsyAssistAgent):
    """RiskAssessment agent for continuous safety monitoring."""
    
    def __init__(self, **kwargs):
        prompt_config = RiskAssessmentPrompt()
        super().__init__(
            name="RiskAssessment",
            prompt_config=prompt_config,
            **kwargs
        )
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message for risk assessment."""
        context = context or {}
        
        # Perform comprehensive risk assessment
        risk_assessment = await self.assess_risk(message, session)
        
        # Create assessment summary
        assessment_summary = self._create_assessment_summary(risk_assessment)
        
        # Determine action needed
        action_needed = self._determine_action_needed(risk_assessment, session)
        
        # Update session with risk information
        session.metadata['last_risk_assessment'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': risk_assessment['assessment'].overall_severity.value,
            'confidence': risk_assessment['assessment'].overall_confidence,
            'factors': [factor.category.value for factor in risk_assessment['assessment'].risk_factors]
        }
        
        session = self.update_session(session)
        
        return self.format_response(
            assessment_summary,
            {
                'risk_assessment_completed': True,
                'severity': risk_assessment['assessment'].overall_severity.value,
                'confidence': risk_assessment['assessment'].overall_confidence,
                'action_needed': action_needed,
                'escalation_required': risk_assessment['should_escalate'],
                'emergency_required': risk_assessment['is_emergency']
            }
        )
    
    def _create_assessment_summary(self, risk_assessment: Dict[str, Any]) -> str:
        """Create a summary of the risk assessment."""
        assessment = risk_assessment['assessment']
        
        if assessment.overall_severity.value == 'NONE':
            return "No immediate safety concerns detected."
        
        summary = f"Risk assessment completed. Overall severity: {assessment.overall_severity.value} "
        summary += f"(confidence: {assessment.overall_confidence:.1%}). "
        
        if assessment.risk_factors:
            factors = [factor.category.value for factor in assessment.risk_factors]
            summary += f"Risk factors identified: {', '.join(factors)}. "
        
        if risk_assessment['should_escalate']:
            summary += "Escalation recommended. "
        
        if risk_assessment['is_emergency']:
            summary += "Emergency response required. "
        
        return summary
    
    def _determine_action_needed(self, risk_assessment: Dict[str, Any], session: Session) -> str:
        """Determine what action is needed based on the risk assessment."""
        assessment = risk_assessment['assessment']
        
        if risk_assessment['is_emergency']:
            return 'emergency_response'
        elif risk_assessment['should_escalate']:
            return 'escalation'
        elif assessment.overall_severity.value in ['MEDIUM', 'HIGH']:
            return 'increased_monitoring'
        else:
            return 'continue_monitoring'
    
    async def should_trigger_assessment(self, session: Session, message_count: int) -> bool:
        """Determine if a risk assessment should be triggered."""
        # Assess every few messages
        if message_count % 3 == 0:
            return True
        
        # Assess if there are previous risk flags
        if session.risk_flags:
            return True
        
        # Assess if session has been active for a while
        session_duration = (datetime.utcnow() - session.created_at).total_seconds() / 60
        if session_duration > 15:  # 15 minutes
            return True
        
        return False
