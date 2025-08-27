"""
Main settings configuration for PsyAssist AI.
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "PsyAssist AI"
    app_version: str = "0.1.0"
    debug: bool = Field(False, env="DEBUG")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # AI/LLM Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    default_model: str = Field("gpt-4", env="DEFAULT_MODEL")
    
    # Session Configuration
    session_timeout_minutes: int = Field(30, env="SESSION_TIMEOUT_MINUTES")
    max_messages_per_session: int = Field(50, env="MAX_MESSAGES_PER_SESSION")
    session_cleanup_interval_minutes: int = Field(60, env="SESSION_CLEANUP_INTERVAL_MINUTES")
    
    # Risk Assessment Configuration
    risk_assessment_interval_messages: int = Field(3, env="RISK_ASSESSMENT_INTERVAL_MESSAGES")
    escalation_threshold: str = Field("HIGH", env="ESCALATION_THRESHOLD")
    emergency_threshold: str = Field("CRITICAL", env="EMERGENCY_THRESHOLD")
    
    # Event System Configuration
    event_batch_size: int = Field(10, env="EVENT_BATCH_SIZE")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    # Privacy & Compliance
    data_retention_days: int = Field(7, env="DATA_RETENTION_DAYS")
    pii_redaction_enabled: bool = Field(True, env="PII_REDACTION_ENABLED")
    consent_required: bool = Field(True, env="CONSENT_REQUIRED")
    
    # External Services
    hotline_api_url: Optional[str] = Field(None, env="HOTLINE_API_URL")
    warm_transfer_api_url: Optional[str] = Field(None, env="WARM_TRANSFER_API_URL")
    directory_api_url: Optional[str] = Field(None, env="DIRECTORY_API_URL")
    
    # Monitoring
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    health_check_interval_seconds: int = Field(30, env="HEALTH_CHECK_INTERVAL_SECONDS")
    
    # Development Settings
    test_mode: bool = Field(False, env="TEST_MODE")
    mock_external_services: bool = Field(True, env="MOCK_EXTERNAL_SERVICES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
