"""
Configuration settings for College ERP.
Adheres to 12-factor configuration principles and DPDP Act 2023 requirements.
"""

import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Prerana College ERP - Trust Management System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./college_erp.db")
    
    # Generate process-local secrets unless explicit environment values are provided.
    JWT_SECRET: str = secrets.token_urlsafe(48)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    DEMO_AUTH_ENABLED: bool = os.getenv("DEMO_AUTH_ENABLED", "false").lower() == "true"
    DEMO_ADMIN_PASSWORD: str = secrets.token_urlsafe(24)
    DEMO_FACULTY_PASSWORD: str = secrets.token_urlsafe(24)
    DEMO_MODERATOR_PASSWORD: str = secrets.token_urlsafe(24)
    
    # Campus & Programme Defaults (Problem Statement scope: one campus slice)
    DEFAULT_CAMPUS_CODE: str = "BBSR-ENG"
    DEFAULT_CAMPUS_NAME: str = "Bhubaneswar Engineering College"
    DEFAULT_TRUST_NAME: str = "Company A Educational Trust, Bhubaneswar"
    
    # Academic & Compliance Rules (Fixed Settings, NOT AI)
    MINIMUM_ATTENDANCE_PERCENTAGE: float = 75.0
    INTERNAL_MARKS_MAX: float = 40.0
    INTERNAL_PASS_THRESHOLD: float = 16.0  # 40% of 40
    
    # DPDP Act 2023 Settings
    DPDP_MINOR_AGE_THRESHOLD: int = 18
    DPDP_AUDIT_LOGGING_ENABLED: bool = True
    
    # Notification & Localization
    ENABLE_ODIA_NOTIFICATIONS: bool = True


settings = Settings()
