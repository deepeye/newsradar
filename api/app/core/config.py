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
    QWEN_MODEL: str = "qwen3.6-35b-a3b"
    QWEN_TIMEOUT: int = 300
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    # AI Cache
    AI_CACHE_TTL: int = 300


settings = Settings()
