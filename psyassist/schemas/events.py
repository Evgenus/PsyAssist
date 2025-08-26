"""
Event schemas for PsyAssist AI observability system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .session import SessionState, ConsentStatus
from .risk import RiskSeverity, RiskCategory


class EventType(str, Enum):
    """Types of events that can be emitted."""
    # Session events
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_CLOSED = "session.closed"
    SESSION_EXPIRED = "session.expired"
    
    # Consent events
    CONSENT_GRANTED = "consent.granted"
    CONSENT_DENIED = "consent.denied"
    CONSENT_WITHDRAWN = "consent.withdrawn"
    
    # Message events
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_PROCESSED = "message.processed"
    
    # Risk events
    RISK_ASSESSED = "risk.assessed"
    RISK_FLAG_RAISED = "risk.flag_raised"
    RISK_ESCALATION_TRIGGERED = "risk.escalation_triggered"
    
    # Agent events
    AGENT_ACTIVATED = "agent.activated"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"
    
    # Resource events
    RESOURCE_PROVIDED = "resource.provided"
    RESOURCE_ACCESSED = "resource.accessed"
    
    # Escalation events
    ESCALATION_INITIATED = "escalation.initiated"
    ESCALATION_COMPLETED = "escalation.completed"
    ESCALATION_FAILED = "escalation.failed"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BaseEvent(BaseModel):
    """Base event model."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    session_id: str = Field(..., description="Associated session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    priority: EventPriority = Field(EventPriority.NORMAL, description="Event priority")
    
    # Event metadata
    source: str = Field(..., description="Source of the event")
    user_id: Optional[str] = Field(None, description="User ID if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionEvent(BaseEvent):
    """Session-related events."""
    old_state: Optional[SessionState] = Field(None, description="Previous session state")
    new_state: Optional[SessionState] = Field(None, description="New session state")
    consent_status: Optional[ConsentStatus] = Field(None, description="Consent status")
    message_count: Optional[int] = Field(None, description="Message count")
    duration_minutes: Optional[float] = Field(None, description="Session duration")


class RiskEvent(BaseEvent):
    """Risk assessment events."""
    risk_severity: Optional[RiskSeverity] = Field(None, description="Risk severity level")
    risk_categories: List[RiskCategory] = Field(default_factory=list, description="Risk categories")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Assessment confidence")
    escalation_triggered: bool = Field(False, description="Whether escalation was triggered")
    keywords_detected: List[str] = Field(default_factory=list, description="Keywords that triggered risk")


class MessageEvent(BaseEvent):
    """Message-related events."""
    message_id: str = Field(..., description="Message identifier")
    message_type: str = Field(..., description="Type of message (user/agent)")
    content_length: int = Field(..., description="Length of message content")
    processing_time_ms: Optional[float] = Field(None, description="Message processing time")
    agent_involved: Optional[str] = Field(None, description="Agent that processed the message")


class AgentEvent(BaseEvent):
    """Agent-related events."""
    agent_name: str = Field(..., description="Name of the agent")
    task_type: str = Field(..., description="Type of task performed")
    task_duration_ms: Optional[float] = Field(None, description="Task duration")
    success: bool = Field(True, description="Whether task was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class EscalationEvent(BaseEvent):
    """Escalation-related events."""
    escalation_type: str = Field(..., description="Type of escalation")
    target_service: str = Field(..., description="Target service for escalation")
    contact_info: Optional[str] = Field(None, description="Contact information provided")
    success: bool = Field(True, description="Whether escalation was successful")
    response_time_ms: Optional[float] = Field(None, description="Response time from target service")


class SystemEvent(BaseEvent):
    """System-related events."""
    component: str = Field(..., description="System component")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    error_details: Optional[str] = Field(None, description="Detailed error information")
    stack_trace: Optional[str] = Field(None, description="Stack trace for errors")


class EventBatch(BaseModel):
    """Batch of events for efficient processing."""
    batch_id: str = Field(..., description="Unique batch identifier")
    events: List[BaseEvent] = Field(..., description="List of events in the batch")
    batch_size: int = Field(..., description="Number of events in batch")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('batch_size')
    def validate_batch_size(cls, v, values):
        if 'events' in values and v != len(values['events']):
            raise ValueError("Batch size must match number of events")
        return v
