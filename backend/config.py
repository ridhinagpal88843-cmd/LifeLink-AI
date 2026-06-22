import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings using pydantic-settings.
    Loads variables from Environment or .env file.
    """
    # Application Config
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # FastAPI Config
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Google AI Studio API Key (Gemini)
    GEMINI_API_KEY: Optional[str] = None

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./lifelink.db"

    # Model Context Protocol Config
    MCP_SERVER_URL: Optional[str] = "http://localhost:8080"

    # Security Settings
    SECRET_KEY: str = "fallback_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate settings for global use in the backend
settings = Settings()
