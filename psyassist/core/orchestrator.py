"""
Main orchestrator for PsyAssist AI.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..schemas.session import Session, SessionState, SessionUpdate
from ..schemas.events import BaseEvent, EventType, EventPriority
from ..schemas.risk import RiskAssessment
from ..core.state_machine import StateMachine
from ..tools import RiskClassifier, PIIRedactor, DirectoryLookup, WarmTransferAPI
from ..config.settings import settings


class PsyAssistOrchestrator:
    """Main orchestrator for PsyAssist AI system."""
    
    def __init__(self):
        self.state_machine = StateMachine()
        self.risk_classifier = RiskClassifier()
        self.pii_redactor = PIIRedactor()
        self.directory_lookup = DirectoryLookup()
        self.warm_transfer_api = WarmTransferAPI()
        
        # Session storage (in production, this would be a database)
        self.sessions: Dict[str, Session] = {}
        
        # Event queue (in production, this would be NATS/Kafka)
        self.event_queue: List[BaseEvent] = []
    
    async def create_session(self, user_id: str = None, metadata: Dict[str, Any] = None) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            state=SessionState.INIT,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.session_timeout_minutes),
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        
        # Emit session created event
        await self._emit_event(
            EventType.SESSION_CREATED,
            session_id,
            metadata={'user_id': user_id}
        )
        
        return session
    
    async def process_message(self, session_id: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message through the system."""
        # Get session
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Validate session
        if not self._validate_session(session):
            return {
                'content': 'Session has expired or reached its limit. Please start a new session.',
                'agent': 'System',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'error': 'session_invalid'}
            }
        
        # Redact PII from message for logging
        redacted_message, redaction_metadata = self.pii_redactor.redact_text(message)
        
        # Emit message received event
        await self._emit_event(
            EventType.MESSAGE_RECEIVED,
            session_id,
            metadata={
                'content_length': len(message),
                'redacted': redaction_metadata['total_redactions'] > 0,
                'pii_types': redaction_metadata['redaction_types']
            }
        )
        
        # Process through state machine
        response = await self.state_machine.process_message(session, message, context or {})
        
        # Update session
        session = self._update_session(session, response)
        
        # Emit message sent event
        await self._emit_event(
            EventType.MESSAGE_SENT,
            session_id,
            metadata={
                'agent': response.get('agent', 'Unknown'),
                'content_length': len(response.get('content', ''))
            }
        )
        
        return response
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, updates: SessionUpdate) -> Optional[Session]:
        """Update a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Apply updates
        if updates.state:
            session.state = updates.state
        if updates.consent_status:
            session.consent_status = updates.consent_status
        if updates.metadata:
            session.metadata.update(updates.metadata)
        if updates.risk_flags:
            session.risk_flags.extend(updates.risk_flags)
        
        session.updated_at = datetime.utcnow()
        
        # Emit session updated event
        await self._emit_event(
            EventType.SESSION_UPDATED,
            session_id,
            metadata={'updates': updates.dict()}
        )
        
        return session
    
    async def close_session(self, session_id: str, reason: str = "user_requested") -> bool:
        """Close a session."""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.state = SessionState.CLOSE
        session.updated_at = datetime.utcnow()
        session.metadata['close_reason'] = reason
        
        # Emit session closed event
        await self._emit_event(
            EventType.SESSION_CLOSED,
            session_id,
            metadata={'reason': reason}
        )
        
        return True
    
    async def assess_risk(self, session_id: str, text: str) -> RiskAssessment:
        """Perform risk assessment on text."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        context = {
            'session_id': session_id,
            'user_id': session.user_id,
            'message_count': session.message_count,
            'previous_risk_level': session.risk_flags[-1] if session.risk_flags else None
        }
        
        assessment = await self.risk_classifier.assess_risk(text, context)
        
        # Update session with risk information
        if assessment.overall_severity.value not in ['NONE', 'LOW']:
            session.risk_flags.append(assessment.overall_severity.value)
        
        # Emit risk assessed event
        await self._emit_event(
            EventType.RISK_ASSESSED,
            session_id,
            priority=EventPriority.HIGH if assessment.overall_severity.value in ['HIGH', 'CRITICAL'] else EventPriority.NORMAL,
            metadata={
                'severity': assessment.overall_severity.value,
                'confidence': assessment.overall_confidence,
                'factors': [factor.category.value for factor in assessment.risk_factors]
            }
        )
        
        return assessment
    
    async def get_resources(self, session_id: str, categories: List[str] = None) -> List[Dict[str, Any]]:
        """Get resources for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        location = session.metadata.get('location', 'US')
        resources = await self.directory_lookup.get_resources(location, categories)
        
        # Convert to dict for JSON serialization
        return [resource.dict() for resource in resources]
    
    async def initiate_escalation(self, session_id: str, resource_id: str) -> Dict[str, Any]:
        """Initiate escalation to human support."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get resource
        location = session.metadata.get('location', 'US')
        resources = await self.directory_lookup.get_resources(location)
        resource = next((r for r in resources if r.resource_id == resource_id), None)
        
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")
        
        # Initiate transfer
        transfer_context = {
            'session_id': session_id,
            'user_needs': session.metadata.get('triage_info', {}),
            'risk_level': session.metadata.get('last_risk_assessment', {}).get('severity', 'UNKNOWN')
        }
        
        transfer_result = await self.warm_transfer_api.initiate_transfer(
            session_id, resource, transfer_context
        )
        
        # Update session
        session.state = SessionState.ESCALATE
        session.metadata['escalation_initiated'] = True
        session.metadata['transfer_id'] = transfer_result.get('transfer_id')
        
        # Emit escalation initiated event
        await self._emit_event(
            EventType.ESCALATION_INITIATED,
            session_id,
            priority=EventPriority.HIGH,
            metadata={
                'resource_id': resource_id,
                'transfer_id': transfer_result.get('transfer_id'),
                'estimated_wait_time': transfer_result.get('estimated_wait_time')
            }
        )
        
        return transfer_result
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.expires_at and session.expires_at < now:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.close_session(session_id, "expired")
            del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def _validate_session(self, session: Session) -> bool:
        """Validate that a session is active and not expired."""
        if not session:
            return False
        
        # Check if session has expired
        if session.expires_at and datetime.utcnow() > session.expires_at:
            return False
        
        # Check if session has reached message limit
        if session.message_count >= session.max_messages:
            return False
        
        # Check if session is closed
        if session.state == SessionState.CLOSE:
            return False
        
        return True
    
    def _update_session(self, session: Session, response: Dict[str, Any]) -> Session:
        """Update session with response information."""
        session.updated_at = datetime.utcnow()
        session.message_count += 1
        
        # Update metadata with response info
        metadata = response.get('metadata', {})
        if metadata:
            session.metadata.update(metadata)
        
        return session
    
    async def _emit_event(self, event_type: EventType, session_id: str, source: str = "orchestrator", 
                         priority: EventPriority = EventPriority.NORMAL, metadata: Dict[str, Any] = None):
        """Emit an event to the event queue."""
        event = BaseEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            session_id=session_id,
            source=source,
            priority=priority,
            metadata=metadata or {}
        )
        
        self.event_queue.append(event)
        
        # In production, this would send to NATS/Kafka
        # For now, just log it
        print(f"Event emitted: {event_type.value} for session {session_id}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status information."""
        active_sessions = len([s for s in self.sessions.values() if s.state != SessionState.CLOSE])
        total_sessions = len(self.sessions)
        
        return {
            'active_sessions': active_sessions,
            'total_sessions': total_sessions,
            'event_queue_size': len(self.event_queue),
            'system_health': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
