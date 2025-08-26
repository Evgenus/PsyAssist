"""
Base agent class for PsyAssist AI agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from crewai import Agent
from langchain.tools import BaseTool

from ..schemas.session import Session
from ..schemas.events import BaseEvent, EventType, EventPriority
from ..tools import RiskClassifier, PIIRedactor
from ..config.prompts import AgentPrompt


class BasePsyAssistAgent(ABC):
    """Base class for all PsyAssist AI agents."""
    
    def __init__(
        self,
        name: str,
        prompt_config: AgentPrompt,
        tools: List[BaseTool] = None,
        risk_classifier: RiskClassifier = None,
        pii_redactor: PIIRedactor = None,
        **kwargs
    ):
        self.name = name
        self.prompt_config = prompt_config
        self.tools = tools or []
        self.risk_classifier = risk_classifier or RiskClassifier()
        self.pii_redactor = pii_redactor or PIIRedactor()
        
        # Initialize CrewAI agent
        self.agent = self._create_crewai_agent(**kwargs)
        
        # Session tracking
        self.active_sessions: Dict[str, Session] = {}
    
    def _create_crewai_agent(self, **kwargs) -> Agent:
        """Create the underlying CrewAI agent."""
        role = self.prompt_config.role
        goal = self.prompt_config.goal
        
        # Build constraints and safety rules
        constraints = "\n".join(self.prompt_config.constraints)
        safety_rules = "\n".join(self.prompt_config.safety_rules)
        style_guide = "\n".join(self.prompt_config.style_guide)
        
        # Create backstory with all components
        backstory = f"""
{role}

Goal: {goal}

Constraints:
{constraints}

Safety Rules:
{safety_rules}

Style Guide:
{style_guide}

Remember: This is not a medical device and cannot provide medical treatment.
Always prioritize user safety and escalate when in doubt.
"""
        
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            **kwargs
        )
    
    @abstractmethod
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and return a response."""
        pass
    
    async def assess_risk(self, text: str, session: Session) -> Dict[str, Any]:
        """Assess risk in the given text."""
        context = {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'message_count': session.message_count,
            'previous_risk_level': session.risk_flags[-1] if session.risk_flags else None
        }
        
        assessment = await self.risk_classifier.assess_risk(text, context)
        
        # Update session with risk flags
        if assessment.overall_severity.value not in ['NONE', 'LOW']:
            session.risk_flags.append(assessment.overall_severity.value)
        
        return {
            'assessment': assessment,
            'should_escalate': self.risk_classifier.should_escalate(assessment),
            'is_emergency': self.risk_classifier.is_emergency(assessment)
        }
    
    def redact_pii(self, data: Any) -> Any:
        """Redact PII from data."""
        return self.pii_redactor.redact_for_logging(data)
    
    def create_event(
        self,
        event_type: EventType,
        session_id: str,
        source: str = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Dict[str, Any] = None
    ) -> BaseEvent:
        """Create an event for observability."""
        return BaseEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            session_id=session_id,
            source=source or self.name,
            priority=priority,
            metadata=metadata or {}
        )
    
    def validate_session(self, session: Session) -> bool:
        """Validate that a session is active and not expired."""
        if not session:
            return False
        
        # Check if session has expired
        if session.expires_at and datetime.utcnow() > session.expires_at:
            return False
        
        # Check if session has reached message limit
        if session.message_count >= session.max_messages:
            return False
        
        return True
    
    def update_session(self, session: Session, **updates) -> Session:
        """Update session with new information."""
        session.updated_at = datetime.utcnow()
        session.message_count += 1
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        return session
    
    def get_session_context(self, session: Session) -> Dict[str, Any]:
        """Get context information for the session."""
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'state': session.state.value,
            'consent_status': session.consent_status.value,
            'message_count': session.message_count,
            'risk_flags': session.risk_flags,
            'metadata': session.metadata
        }
    
    def format_response(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format agent response."""
        response = {
            'content': content,
            'agent': self.name,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        return response
    
    def should_escalate_session(self, session: Session, risk_assessment: Dict[str, Any]) -> bool:
        """Determine if session should be escalated."""
        # Check risk assessment
        if risk_assessment.get('should_escalate', False):
            return True
        
        # Check session state
        if session.state.value in ['ESCALATE', 'CLOSE']:
            return True
        
        # Check message count
        if session.message_count >= session.max_messages:
            return True
        
        # Check for explicit escalation request
        if session.metadata.get('escalation_requested', False):
            return True
        
        return False
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            'name': self.name,
            'role': self.prompt_config.role,
            'goal': self.prompt_config.goal,
            'constraints': self.prompt_config.constraints,
            'safety_rules': self.prompt_config.safety_rules,
            'tools': [tool.name for tool in self.tools],
            'active_sessions': len(self.active_sessions)
        }
