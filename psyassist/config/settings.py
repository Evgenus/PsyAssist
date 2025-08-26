"""
Main settings configuration for PsyAssist AI.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator


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
    
    # Database
    database_url: str = Field("sqlite:///./psyassist.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # AI/LLM Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    default_model: str = Field("gpt-4", env="DEFAULT_MODEL")
    
    # Session Configuration
    session_timeout_minutes: int = Field(30, env="SESSION_TIMEOUT_MINUTES")
    max_messages_per_session: int = Field(50, env="MAX_MESSAGES_PER_SESSION")
    session_cleanup_interval_minutes: int = Field(60, env="SESSION_CLEANUP_INTERVAL_MINUTES")
    
    # Risk Assessment
    risk_assessment_interval_messages: int = Field(3, env="RISK_ASSESSMENT_INTERVAL_MESSAGES")
    escalation_threshold: str = Field("HIGH", env="ESCALATION_THRESHOLD")
    emergency_threshold: str = Field("CRITICAL", env="EMERGENCY_THRESHOLD")
    
    # Event System
    event_bus_url: str = Field("nats://localhost:4222", env="EVENT_BUS_URL")
    event_batch_size: int = Field(10, env="EVENT_BATCH_SIZE")
    event_batch_timeout_seconds: int = Field(30, env="EVENT_BATCH_TIMEOUT_SECONDS")
    
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
    
    # Development
    test_mode: bool = Field(False, env="TEST_MODE")
    mock_external_services: bool = Field(False, env="MOCK_EXTERNAL_SERVICES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("escalation_threshold", "emergency_threshold")
    def validate_risk_thresholds(cls, v):
        valid_thresholds = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if v not in valid_thresholds:
            raise ValueError(f"Risk threshold must be one of: {valid_thresholds}")
        return v
    
    @validator("default_llm_provider")
    def validate_llm_provider(cls, v):
        valid_providers = ["openai", "anthropic"]
        if v not in valid_providers:
            raise ValueError(f"LLM provider must be one of: {valid_providers}")
        return v


# Global settings instance
settings = Settings()
