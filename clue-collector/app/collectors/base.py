"""采集器基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.anti_crawl import AntiCrawlModule


@dataclass
class ClueData:
    """采集线索数据"""
    title: str
    original_content: Optional[str] = None
    translated_content: Optional[str] = None
    url: Optional[str] = None
    cover_image: Optional[str] = None
    author: Optional[str] = None
    rank: Optional[int] = None
    heat_value: Optional[str] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class CollectResult:
    """采集结果"""
    success: bool
    items: List[ClueData] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """采集器基类"""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    @abstractmethod
    async def collect(
        self,
        config: Dict[str, Any],
        anti_crawl: AntiCrawlModule,
        source_id: str = None
    ) -> CollectResult:
        """执行采集

        Args:
            config: 采集配置
            anti_crawl: 反爬防护模块
            source_id: 数据源ID（用于Cookie轮换）

        Returns:
            CollectResult: 采集结果
        """
        pass

    @abstractmethod
    async def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置是否有效

        Args:
            config: 采集配置

        Returns:
            bool: 配置是否有效
        """
        pass

    def get_supported_types(self) -> List[str]:
        """获取支持的采集类型"""
        return []
