"""异常处理模块 - 错误分类、重试、降级和告警"""
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorType(str, Enum):
    """错误类型"""
    NETWORK_TIMEOUT = "network_timeout"      # 请求超时
    CONNECTION_ERROR = "connection_error"    # 连接失败
    BLOCKED_IP = "blocked_ip"                # IP被封
    PARSE_ERROR = "parse_error"              # 解析失败
    COOKIE_EXPIRED = "cookie_expired"        # Cookie过期
    SOURCE_UNAVAILABLE = "source_unavailable" # 源站不可访问


RETRYABLE_ERRORS = [
    ErrorType.NETWORK_TIMEOUT,
    ErrorType.CONNECTION_ERROR,
    ErrorType.BLOCKED_IP,
    ErrorType.COOKIE_EXPIRED,
]


NON_RETRYABLE_ERRORS = [
    ErrorType.PARSE_ERROR,
    ErrorType.SOURCE_UNAVAILABLE,
]


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: ErrorType
    message: str
    source_id: Optional[str] = None
    timestamp: datetime = None
    retry_count: int = 0
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.context is None:
            self.context = {}


class ErrorClassifier:
    """错误分类器"""

    @staticmethod
    def classify(error: Exception, status_code: Optional[int] = None) -> ErrorType:
        """根据异常和状态码分类错误"""
        error_msg = str(error).lower()

        # HTTP状态码判断
        if status_code == 429:
            return ErrorType.BLOCKED_IP
        if status_code == 403:
            return ErrorType.BLOCKED_IP
        if status_code == 401:
            return ErrorType.COOKIE_EXPIRED

        # 超时类错误
        if "timeout" in error_msg:
            return ErrorType.NETWORK_TIMEOUT

        # 连接错误
        if any(word in error_msg for word in ["connection", "refused", "reset", "reset"]):
            return ErrorType.CONNECTION_ERROR

        # 解析错误
        if any(word in error_msg for word in ["parse", "selector", "json", "xml"]):
            return ErrorType.PARSE_ERROR

        # Cookie相关
        if any(word in error_msg for word in ["cookie", "session", "login", "unauthorized"]):
            return ErrorType.COOKIE_EXPIRED

        # 源站不可用
        if any(word in error_msg for word in ["unavailable", "not found", "404", "503", "502"]):
            return ErrorType.SOURCE_UNAVAILABLE

        # 默认
        return ErrorType.CONNECTION_ERROR

    @staticmethod
    def is_retryable(error_type: ErrorType) -> bool:
        """判断是否可重试"""
        return error_type in RETRYABLE_ERRORS

    @staticmethod
    def get_retry_delay(retry_count: int) -> int:
        """获取重试延迟（秒）- 指数退避"""
        delays = [5, 10, 20]  # 5s, 10s, 20s
        return delays[min(retry_count, len(delays) - 1)]


class RetryHandler:
    """重试处理器"""

    MAX_RETRIES = 3

    @staticmethod
    def should_retry(error_info: ErrorInfo) -> bool:
        """判断是否应该重试"""
        if error_info.retry_count >= RetryHandler.MAX_RETRIES:
            return False

        if error_info.error_type in NON_RETRYABLE_ERRORS:
            return False

        return True

    @staticmethod
    def get_next_retry_time(error_info: ErrorInfo) -> datetime:
        """获取下次重试时间"""
        delay = ErrorClassifier.get_retry_delay(error_info.retry_count)
        return datetime.utcnow() + __import__('datetime').timedelta(seconds=delay)


class DegradationStrategy:
    """降级策略"""

    @staticmethod
    async def ip_degradation(ip: str) -> bool:
        """IP降级 - 连续3次被封标记不可用"""
        logger.warning("ip_degradation_triggered", ip=ip)
        # TODO: 实现IP降级逻辑
        return True

    @staticmethod
    async def frequency_degradation(source_id: str) -> bool:
        """频率降级 - 检测到429降低50%频率"""
        logger.warning("frequency_degradation_triggered", source_id=source_id)
        # TODO: 实现频率降级逻辑
        return True

    @staticmethod
    async def source_degradation(source_id: str, consecutive_failures: int) -> bool:
        """数据源降级 - 连续5次失败暂停采集"""
        if consecutive_failures >= 5:
            logger.error("source_degradation_triggered",
                        source_id=source_id,
                        consecutive_failures=consecutive_failures)
            # TODO: 实现数据源降级逻辑
            return True
        return False


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.enabled = True
        self.channels = ["log"]  # 默认只记录日志

    async def send_alert(self, level: str, message: str, context: Dict[str, Any] = None) -> bool:
        """发送告警"""
        if not self.enabled:
            return False

        alert_data = {
            "level": level,
            "message": message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        # 记录到日志
        if "log" in self.channels:
            logger_method = getattr(logger, level.lower(), logger.info)
            logger_method("alert_sent", **alert_data)

        # TODO: 实现邮件、Webhook、Slack告警

        return True

    async def check_and_alert(
        self,
        source_id: str,
        consecutive_failures: int,
        is_paused: bool = False
    ) -> bool:
        """检查并发送告警"""
        # 连续5次失败告警
        if consecutive_failures >= 5:
            await self.send_alert(
                "error",
                f"数据源连续{consecutive_failures}次采集失败",
                {"source_id": source_id, "consecutive_failures": consecutive_failures}
            )
            return True

        # 状态变更为暂停
        if is_paused:
            await self.send_alert(
                "warning",
                f"数据源状态变更为暂停",
                {"source_id": source_id}
            )
            return True

        return False


class ErrorHandler:
    """异常处理统一入口"""

    def __init__(self):
        self.classifier = ErrorClassifier()
        self.retry_handler = RetryHandler()
        self.degradation = DegradationStrategy()
        self.alert_manager = AlertManager()

    async def handle(
        self,
        error: Exception,
        source_id: Optional[str] = None,
        retry_count: int = 0,
        status_code: Optional[int] = None,
        **context
    ) -> Dict[str, Any]:
        """处理异常"""
        # 分类错误
        error_type = self.classifier.classify(error, status_code)

        error_info = ErrorInfo(
            error_type=error_type,
            message=str(error),
            source_id=source_id,
            retry_count=retry_count,
            context=context
        )

        logger.error("error_handled",
                    error_type=error_type.value,
                    message=str(error),
                    source_id=source_id,
                    retry_count=retry_count)

        result = {
            "error_type": error_type.value,
            "retryable": False,
            "should_retry": False,
            "retry_delay": 0,
        }

        # 判断是否可重试
        if self.classifier.is_retryable(error_type):
            result["retryable"] = True
            result["should_retry"] = self.retry_handler.should_retry(error_info)
            result["retry_delay"] = ErrorClassifier.get_retry_delay(retry_count)

        # 应用降级策略
        if error_type == ErrorType.BLOCKED_IP:
            # TODO: 获取实际IP
            await self.degradation.ip_degradation("unknown")
            await self.degradation.frequency_degradation(source_id)

        # 发送告警
        if retry_count >= 5:
            await self.alert_manager.check_and_alert(source_id, retry_count)

        return result


# 全局异常处理器实例
error_handler = ErrorHandler()
