"""
HIPAA-compliant configuration management for mental health chatbot.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with HIPAA compliance built-in."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Security & HIPAA Compliance
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    encryption_algorithm: str = Field("HS256", env="ENCRYPTION_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    patient_data_encryption_key: str = Field(..., env="PATIENT_DATA_ENCRYPTION_KEY")
    audit_log_retention_days: int = Field(2555, env="AUDIT_LOG_RETENTION_DAYS")  # 7 years
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_encryption_key: str = Field(..., env="DATABASE_ENCRYPTION_KEY")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379/1", env="REDIS_URL")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_ssl: bool = Field(True, env="REDIS_SSL")
    
    # GoHighLevel MCP Configuration
    ghl_mcp_server_url: str = Field("http://localhost:3000", env="GHL_MCP_SERVER_URL")
    ghl_api_key: str = Field(..., env="GHL_API_KEY")
    ghl_location_id: str = Field(..., env="GHL_LOCATION_ID")
    ghl_rate_limit_per_minute: int = Field(100, env="GHL_RATE_LIMIT_PER_MINUTE")
    
    # AI Model Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    default_ai_model: str = Field("claude-3-5-sonnet-20241022", env="DEFAULT_AI_MODEL")
    mental_health_model_temperature: float = Field(0.3, env="MENTAL_HEALTH_MODEL_TEMPERATURE")
    max_conversation_history: int = Field(50, env="MAX_CONVERSATION_HISTORY")
    
    # Mental Health Specific Settings
    crisis_hotline_numbers: List[str] = Field(["988", "1-800-273-8255"], env="CRISIS_HOTLINE_NUMBERS")
    emergency_contact_email: str = Field(..., env="EMERGENCY_CONTACT_EMAIL")
    therapist_escalation_threshold: str = Field("high_risk", env="THERAPIST_ESCALATION_THRESHOLD")
    session_timeout_minutes: int = Field(30, env="SESSION_TIMEOUT_MINUTES")
    patient_anonymization_enabled: bool = Field(True, env="PATIENT_ANONYMIZATION_ENABLED")
    
    # Compliance & Monitoring
    hipaa_audit_webhook_url: Optional[str] = Field(None, env="HIPAA_AUDIT_WEBHOOK_URL")
    data_retention_policy_days: int = Field(2555, env="DATA_RETENTION_POLICY_DAYS")
    patient_consent_required: bool = Field(True, env="PATIENT_CONSENT_REQUIRED")
    therapist_supervision_required: bool = Field(True, env="THERAPIST_SUPERVISION_REQUIRED")
    
    # Email Configuration
    smtp_server: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str = Field(..., env="SMTP_USERNAME")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    email_from: str = Field(..., env="EMAIL_FROM")
    
    # Backup & Recovery
    backup_encryption_key: str = Field(..., env="BACKUP_ENCRYPTION_KEY")
    backup_schedule: str = Field("daily", env="BACKUP_SCHEDULE")
    backup_retention_days: int = Field(90, env="BACKUP_RETENTION_DAYS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(1000, env="RATE_LIMIT_PER_HOUR")
    rate_limit_per_day: int = Field(5000, env="RATE_LIMIT_PER_DAY")
    
    # Development Settings
    mock_ghl_responses: bool = Field(False, env="MOCK_GHL_RESPONSES")
    test_patient_data: bool = Field(False, env="TEST_PATIENT_DATA")
    bypass_hipaa_checks: bool = Field(False, env="BYPASS_HIPAA_CHECKS")
    
    @validator("crisis_hotline_numbers", pre=True)
    def parse_crisis_hotlines(cls, v):
        """Parse crisis hotline numbers from string or list."""
        if isinstance(v, str):
            return [num.strip() for num in v.split(",")]
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is valid."""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @validator("patient_data_encryption_key", "database_encryption_key", "backup_encryption_key")
    def validate_encryption_keys(cls, v):
        """Ensure encryption keys are properly formatted."""
        if len(v) < 32:
            raise ValueError("Encryption keys must be at least 32 characters long")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def hipaa_compliant_mode(self) -> bool:
        """Check if HIPAA compliance is enforced."""
        return self.is_production or not self.bypass_hipaa_checks
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()