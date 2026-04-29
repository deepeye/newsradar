"""配置管理"""
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(env_prefix='DATABASE_')

    url: str = Field(alias='DATABASE_URL', default="postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector")
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


class RedisConfig(BaseSettings):
    """Redis配置"""
    model_config = SettingsConfigDict(env_prefix='REDIS_')

    url: str = Field(alias='REDIS_URL', default="redis://localhost:6379/0")
    decode_responses: bool = True


class AntiCrawlConfig(BaseSettings):
    """反爬配置"""
    enabled: bool = True
    request_interval: float = 2.0
    min_interval: float = 1.0
    max_interval: float = 10.0


class SchedulerConfig(BaseSettings):
    """调度器配置"""
    hotlist_interval: int = 5
    social_interval: int = 30
    video_interval: int = 30
    custom_interval: int = 60



class AlertConfig(BaseSettings):
    """告警配置"""
    enabled: bool = True
    channels: list = Field(default_factory=lambda: ['log'])


class TranslationConfig(BaseSettings):
    """翻译配置"""
    model_config = SettingsConfigDict(env_prefix='TRANSLATION_')

    enabled: bool = True
    api_key: str = Field(default="")
    api_base: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    model: str = Field(default="qwen-plus")
    max_length: int = Field(default=2000)
    timeout: int = Field(default=30)


class AppConfig(BaseSettings):
    """应用配置"""
    name: str = "clue-collector"
    version: str = "0.1.0"
    log_level: str = "INFO"


class Settings(BaseSettings):
    """全局配置"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='allow'
    )

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    anti_crawl: AntiCrawlConfig = Field(default_factory=AntiCrawlConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)



def load_yaml_config(path: Optional[str] = None) -> dict:
    """加载YAML配置"""
    if path is None:
        path = Path(__file__).parent.parent / 'config' / 'settings.yaml'

    if not Path(path).exists():
        return {}

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


# 全局配置实例
settings = Settings()

# 尝试从YAML加载额外配置
_yaml_config = load_yaml_config()
if _yaml_config:
    # 合并配置
    if 'app' in _yaml_config:
        for key, value in _yaml_config['app'].items():
            if hasattr(settings.app, key):
                setattr(settings.app, key, value)
