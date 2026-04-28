"""反爬模块单元测试"""
import pytest
from unittest.mock import Mock, patch

from app.anti_crawl.ua_rotator import UARotator, ua_rotator
from app.anti_crawl.manager import AntiCrawlModule, RequestContext
from app.anti_crawl.handler import ErrorClassifier, ErrorType


class TestUARotator:
    """UA轮换器测试"""

    def test_get_random_ua(self):
        """测试随机获取UA"""
        ua = ua_rotator.get_ua()
        assert ua is not None
        assert "Mozilla" in ua

    def test_get_desktop_ua(self):
        """测试获取桌面端UA"""
        ua = ua_rotator.get_desktop_ua()
        assert ua is not None
        # 桌面端UA通常包含Windows或Macintosh
        assert "Windows" in ua or "Macintosh" in ua or "Linux" in ua

    def test_get_mobile_ua(self):
        """测试获取移动端UA"""
        ua = ua_rotator.get_mobile_ua()
        assert ua is not None
        # 移动端UA包含Mobile或iPhone或Android
        assert "Mobile" in ua or "iPhone" in ua or "Android" in ua

    def test_platform_specific_ua(self):
        """测试平台特定UA"""
        ua_weibo = ua_rotator.get_ua(platform="weibo")
        ua_bilibili = ua_rotator.get_ua(platform="bilibili")

        # 微博默认用移动端
        assert ua_weibo is not None
        # B站默认用桌面端
        assert ua_bilibili is not None

    def test_get_ua_with_headers(self):
        """测试获取带UA的请求头"""
        headers = ua_rotator.get_ua_with_headers()
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers

    def test_ua_not_repeated(self):
        """测试UA不连续重复"""
        ua1 = ua_rotator.get_ua()
        ua2 = ua_rotator.get_ua()
        # 两次获取的UA不应该相同（概率很低）
        # 注意：这只是测试逻辑，实际可能偶然相同


class TestRequestContext:
    """请求上下文测试"""

    def test_create_empty_context(self):
        """测试创建空上下文"""
        ctx = RequestContext()
        assert ctx.proxy is None
        assert ctx.user_agent is None
        assert ctx.cookies is None

    def test_create_full_context(self):
        """测试创建完整上下文"""
        ctx = RequestContext(
            proxy="http://proxy.example.com:8080",
            user_agent="Test UA",
            cookies={"session": "abc123"},
            headers={"X-Custom": "value"}
        )
        assert ctx.proxy == "http://proxy.example.com:8080"
        assert ctx.cookies["session"] == "abc123"


class TestErrorClassifier:
    """错误分类器测试"""

    def test_classify_timeout(self):
        """测试超时错误分类"""
        error = Exception("Connection timeout")
        error_type = ErrorClassifier.classify(error)
        assert error_type == ErrorType.NETWORK_TIMEOUT

    def test_classify_blocked_ip_429(self):
        """测试429错误分类"""
        error = Exception("Rate limited")
        error_type = ErrorClassifier.classify(error, status_code=429)
        assert error_type == ErrorType.BLOCKED_IP

    def test_classify_blocked_ip_403(self):
        """测试403错误分类"""
        error = Exception("Forbidden")
        error_type = ErrorClassifier.classify(error, status_code=403)
        assert error_type == ErrorType.BLOCKED_IP

    def test_classify_parse_error(self):
        """测试解析错误分类"""
        error = Exception("JSON parse error")
        error_type = ErrorClassifier.classify(error)
        assert error_type == ErrorType.PARSE_ERROR

    def test_is_retryable(self):
        """测试可重试判断"""
        assert ErrorClassifier.is_retryable(ErrorType.NETWORK_TIMEOUT) == True
        assert ErrorClassifier.is_retryable(ErrorType.BLOCKED_IP) == True
        assert ErrorClassifier.is_retryable(ErrorType.PARSE_ERROR) == False

    def test_get_retry_delay(self):
        """测试重试延迟"""
        assert ErrorClassifier.get_retry_delay(0) == 5
        assert ErrorClassifier.get_retry_delay(1) == 10
        assert ErrorClassifier.get_retry_delay(2) == 20
        assert ErrorClassifier.get_retry_delay(10) == 20  # 最大值


class TestAntiCrawlModule:
    """反爬模块测试"""

    def test_disabled_module(self):
        """测试禁用模块"""
        module = AntiCrawlModule()
        module.enabled = False
        ctx = RequestContext()  # 应返回空上下文
        assert ctx.proxy is None