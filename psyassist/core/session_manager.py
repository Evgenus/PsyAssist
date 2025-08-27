"""
Session management for PsyAssist AI.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from uuid import uuid4

from ..schemas.session import Session, SessionState, SessionUpdate
from ..schemas.events import SessionEvent, EventType
from ..config.settings import settings


logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session lifecycle and storage."""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(settings.session_cleanup_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.state not in [SessionState.CLOSE]:
                # Check if session has timed out
                timeout_minutes = settings.session_timeout_minutes
                if session.updated_at and (now - session.updated_at).total_seconds() > timeout_minutes * 60:
                    expired_sessions.append(session_id)
                # Check if session has too many messages
                elif session.message_count > settings.max_messages_per_session:
                    expired_sessions.append(session_id)
            elif session.state == SessionState.CLOSE:
                # Remove closed sessions after retention period
                retention_days = settings.data_retention_days
                if session.updated_at and (now - session.updated_at).days > retention_days:
                    expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.close_session(session_id, "Session expired or exceeded limits")
            logger.info(f"Cleaned up expired session: {session_id}")
    
    async def create_session(self, user_id: Optional[str] = None) -> Session:
        """Create a new session."""
        session_id = str(uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            state=SessionState.INIT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
            message_count=0,
            risk_flags=[]
        )
        
        self.sessions[session_id] = session
        
        # Add session creation event
        event = SessionEvent(
            session_id=session_id,
            event_type=EventType.SESSION_CREATED,
            timestamp=datetime.utcnow(),
            data={"user_id": user_id}
        )
        session.events.append(event)
        
        logger.info(f"Created new session: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if session and session.state != SessionState.CLOSE:
            # Update last activity
            session.updated_at = datetime.utcnow()
        return session
    
    async def update_session(self, session_id: str, **kwargs) -> Optional[Session]:
        """Update session attributes."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.utcnow()
        return session
    
    async def add_message(self, session_id: str, message: dict) -> Optional[Session]:
        """Add a message to a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        
        # Note: Events are handled separately in the orchestrator
        pass
        
        return session
    
    async def add_event(self, session_id: str, event: SessionEvent) -> Optional[Session]:
        """Add an event to a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        session.updated_at = datetime.utcnow()
        # Note: Events are handled separately in the orchestrator
        return session
    
    async def close_session(self, session_id: str, reason: str = "User requested") -> Optional[Session]:
        """Close a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        session.state = SessionState.CLOSE
        session.updated_at = datetime.utcnow()
        
        # Note: Events are handled separately in the orchestrator
        pass
        
        logger.info(f"Closed session {session_id}: {reason}")
        return session
    
    async def list_active_sessions(self) -> List[Session]:
        """Get all active sessions."""
        return [
            session for session in self.sessions.values()
            if session.state != SessionState.CLOSE
        ]
    
    async def get_session_stats(self) -> dict:
        """Get session statistics."""
        total_sessions = len(self.sessions)
        active_sessions = len([s for s in self.sessions.values() if s.state != SessionState.CLOSE])
        closed_sessions = len([s for s in self.sessions.values() if s.state == SessionState.CLOSE])
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "closed_sessions": closed_sessions,
            "cleanup_interval_minutes": settings.session_cleanup_interval_minutes,
            "session_timeout_minutes": settings.session_timeout_minutes,
            "max_messages_per_session": settings.max_messages_per_session
        }
    
    async def cleanup(self):
        """Clean up resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all active sessions
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            if session.state != SessionState.CLOSE:
                await self.close_session(session_id, "System shutdown")
        
        logger.info("Session manager cleaned up")


# Global session manager instance
session_manager = SessionManager()
