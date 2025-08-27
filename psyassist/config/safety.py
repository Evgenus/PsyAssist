"""
Safety configuration for PsyAssist AI.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SafetyConfig(BaseModel):
    """Safety configuration for the system."""
    
    # Risk assessment thresholds
    risk_thresholds: Dict[str, float] = Field(
        default={
            "suicide": 0.7,
            "self_harm": 0.6,
            "violence": 0.8,
            "abuse": 0.7,
            "crisis": 0.8
        },
        description="Risk assessment thresholds for different categories"
    )
    
    # Safety keywords and phrases
    safety_keywords: Dict[str, List[str]] = Field(
        default={
            "suicide": [
                "kill myself", "end my life", "want to die", "suicide",
                "take my life", "end it all", "no reason to live"
            ],
            "self_harm": [
                "hurt myself", "cut myself", "self harm", "self injury",
                "burn myself", "hit myself"
            ],
            "violence": [
                "kill someone", "hurt someone", "attack", "violence",
                "weapon", "gun", "knife", "fight"
            ],
            "abuse": [
                "abuse", "domestic violence", "beaten", "hit me",
                "threaten", "stalk", "harass"
            ],
            "crisis": [
                "emergency", "crisis", "immediate help", "urgent",
                "right now", "can't wait", "desperate"
            ]
        },
        description="Keywords and phrases that trigger risk assessment"
    )
    
    # Escalation rules
    escalation_rules: Dict[str, str] = Field(
        default={
            "CRITICAL": "immediate_hotline",
            "HIGH": "warm_transfer",
            "MEDIUM": "monitor_closely",
            "LOW": "continue_support",
            "NONE": "normal_support"
        },
        description="Escalation actions based on risk levels"
    )
    
    # Response templates
    safety_responses: Dict[str, str] = Field(
        default={
            "suicide_crisis": "I'm very concerned about what you're saying. Your life has value and there are people who want to help you. Please call the National Suicide Prevention Lifeline at 988 or 1-800-273-8255 right now. They're available 24/7 and can provide immediate support.",
            "self_harm": "I hear that you're in a lot of pain right now. Hurting yourself isn't the answer. Please reach out to a crisis hotline or mental health professional who can help you find healthier ways to cope.",
            "violence": "I understand you're feeling very angry and hurt, but violence will only make things worse. Let's talk about what's really bothering you and find a better way to handle this situation.",
            "abuse": "What you're describing sounds like abuse, and that's never okay. You deserve to be safe. Please consider reaching out to the National Domestic Violence Hotline at 1-800-799-7233 for confidential support.",
            "general_crisis": "I can see you're going through something very difficult right now. While I'm here to listen and support you, you might also benefit from talking to a crisis counselor who can provide more specialized help."
        },
        description="Pre-written safety responses for different crisis situations"
    )
    
    # Monitoring settings
    monitoring: Dict[str, Any] = Field(
        default={
            "session_timeout_minutes": 30,
            "max_consecutive_risk_messages": 3,
            "risk_check_interval_seconds": 60,
            "escalation_cooldown_minutes": 5
        },
        description="Monitoring and timeout settings"
    )
    
    # Privacy and data handling
    privacy: Dict[str, Any] = Field(
        default={
            "pii_redaction_enabled": True,
            "session_retention_days": 7,
            "data_encryption_required": True,
            "audit_logging_enabled": True
        },
        description="Privacy and data handling settings"
    )


# Global safety configuration instance
safety_config = SafetyConfig()
