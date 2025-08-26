"""
Session management schemas for PsyAssist AI.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SessionState(str, Enum):
    """Session state enumeration."""
    INIT = "INIT"
    CONSENTED = "CONSENTED"
    TRIAGE = "TRIAGE"
    SUPPORT_LOOP = "SUPPORT_LOOP"
    RISK_CHECK = "RISK_CHECK"
    RESOURCES = "RESOURCES"
    ESCALATE = "ESCALATE"
    CLOSE = "CLOSE"


class ConsentStatus(str, Enum):
    """User consent status."""
    PENDING = "PENDING"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    WITHDRAWN = "WITHDRAWN"


class Session(BaseModel):
    """Session model for tracking user interactions."""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier if available")
    state: SessionState = Field(SessionState.INIT, description="Current session state")
    consent_status: ConsentStatus = Field(ConsentStatus.PENDING, description="User consent status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    
    # Session data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    message_count: int = Field(0, description="Number of messages exchanged")
    risk_flags: List[str] = Field(default_factory=list, description="Risk flags raised during session")
    
    # Safety and limits
    max_messages: int = Field(50, description="Maximum messages per session")
    timeout_minutes: int = Field(30, description="Session timeout in minutes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionUpdate(BaseModel):
    """Model for updating session state."""
    state: Optional[SessionState] = None
    consent_status: Optional[ConsentStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    risk_flags: Optional[List[str]] = None
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v is not None:
            # Ensure no sensitive data in metadata
            sensitive_keys = ['ssn', 'credit_card', 'password', 'token']
            for key in sensitive_keys:
                if key in v:
                    raise ValueError(f"Sensitive key '{key}' not allowed in metadata")
        return v


class SessionSummary(BaseModel):
    """Summary of session for reporting and analytics."""
    session_id: str
    state: SessionState
    consent_status: ConsentStatus
    duration_minutes: float
    message_count: int
    risk_flags: List[str]
    escalated: bool
    created_at: datetime
    closed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
