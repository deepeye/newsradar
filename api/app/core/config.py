"""Application configuration"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # App
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8001

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Qwen AI
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-plus"
    QWEN_TIMEOUT: int = 300
    QWEN_BASE_URL: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        alias="QWEN_API_BASE",
    )

    # AI Cache
    AI_CACHE_TTL: int = 300

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Inter-service communication
    COLLECTOR_API_URL: str = "http://localhost:8002"


settings = Settings()
