"""
Risk assessment schemas for PsyAssist AI safety system.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    """Categories of risk factors."""
    SUICIDE = "SUICIDE"
    SELF_HARM = "SELF_HARM"
    HARM_TO_OTHERS = "HARM_TO_OTHERS"
    SUBSTANCE_ABUSE = "SUBSTANCE_ABUSE"
    DOMESTIC_VIOLENCE = "DOMESTIC_VIOLENCE"
    CHILD_ABUSE = "CHILD_ABUSE"
    ELDER_ABUSE = "ELDER_ABUSE"
    CRISIS = "CRISIS"
    OTHER = "OTHER"


class RiskFactor(BaseModel):
    """Individual risk factor assessment."""
    category: RiskCategory = Field(..., description="Risk category")
    severity: RiskSeverity = Field(..., description="Risk severity level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment (0-1)")
    keywords: List[str] = Field(default_factory=list, description="Keywords that triggered this risk")
    context: str = Field("", description="Contextual information about the risk")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When risk was assessed")


class RiskAssessment(BaseModel):
    """Complete risk assessment for a session or message."""
    assessment_id: str = Field(..., description="Unique assessment identifier")
    session_id: str = Field(..., description="Associated session ID")
    
    # Overall assessment
    overall_severity: RiskSeverity = Field(..., description="Overall risk severity")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    
    # Individual factors
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Individual risk factors")
    
    # Assessment metadata
    assessed_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")
    assessor: str = Field("RiskAssessmentAgent", description="Agent that performed assessment")
    model_used: Optional[str] = Field(None, description="AI model used for assessment")
    
    # Actions taken
    escalation_triggered: bool = Field(False, description="Whether escalation was triggered")
    emergency_contact_provided: bool = Field(False, description="Whether emergency contact was provided")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('overall_severity')
    def validate_overall_severity(cls, v, values):
        """Ensure overall severity reflects the highest individual factor severity."""
        if 'risk_factors' in values:
            max_factor_severity = max(
                (factor.severity for factor in values['risk_factors']),
                default=RiskSeverity.NONE
            )
            # Map severity levels to numeric values for comparison
            severity_order = {
                RiskSeverity.NONE: 0,
                RiskSeverity.LOW: 1,
                RiskSeverity.MEDIUM: 2,
                RiskSeverity.HIGH: 3,
                RiskSeverity.CRITICAL: 4
            }
            if severity_order[v] < severity_order[max_factor_severity]:
                raise ValueError(f"Overall severity {v} cannot be lower than highest factor severity {max_factor_severity}")
        return v


class RiskThreshold(BaseModel):
    """Configurable risk thresholds for different actions."""
    escalation_threshold: RiskSeverity = Field(RiskSeverity.HIGH, description="Severity level that triggers escalation")
    emergency_threshold: RiskSeverity = Field(RiskSeverity.CRITICAL, description="Severity level that requires emergency contact")
    monitoring_threshold: RiskSeverity = Field(RiskSeverity.MEDIUM, description="Severity level that triggers increased monitoring")
    
    # Confidence thresholds
    min_confidence_for_escalation: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence for escalation")
    min_confidence_for_emergency: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence for emergency contact")


class RiskKeywords(BaseModel):
    """Keywords and patterns for risk detection."""
    suicide_keywords: List[str] = Field(default_factory=lambda: [
        "kill myself", "end my life", "suicide", "want to die", "better off dead",
        "no reason to live", "plan to die", "final goodbye", "last message"
    ])
    
    self_harm_keywords: List[str] = Field(default_factory=lambda: [
        "cut myself", "self harm", "hurt myself", "bleeding", "scars",
        "burn myself", "hit myself", "punish myself"
    ])
    
    harm_to_others_keywords: List[str] = Field(default_factory=lambda: [
        "kill them", "hurt someone", "attack", "violent", "weapon",
        "revenge", "payback", "make them suffer"
    ])
    
    crisis_keywords: List[str] = Field(default_factory=lambda: [
        "emergency", "crisis", "help now", "immediate", "urgent",
        "can't take it", "breaking point", "last straw"
    ])
    
    # Patterns for more complex detection
    patterns: Dict[str, str] = Field(default_factory=lambda: {
        "suicide_plan": r"(plan|going to|will|intend).*(kill|die|suicide)",
        "immediate_risk": r"(right now|tonight|today|immediately).*(kill|die|suicide|harm)",
        "means_available": r"(gun|pills|rope|knife|weapon).*(have|got|access)",
    })
