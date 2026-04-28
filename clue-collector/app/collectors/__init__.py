"""采集器模块初始化"""
from app.collectors.base import BaseCollector, ClueData, CollectResult
from app.collectors.configurable import ConfigurableCollector

__all__ = [
    'BaseCollector',
    'ClueData',
    'CollectResult',
    'ConfigurableCollector',
]
