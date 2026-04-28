"""异常处理模块初始化"""
from app.error_handler.handler import (
    ErrorType, ErrorInfo, ErrorClassifier,
    RetryHandler, DegradationStrategy, AlertManager, ErrorHandler,
    error_handler
)

__all__ = [
    'ErrorType',
    'ErrorInfo',
    'ErrorClassifier',
    'RetryHandler',
    'DegradationStrategy',
    'AlertManager',
    'ErrorHandler',
    'error_handler',
]
