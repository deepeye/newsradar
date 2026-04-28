"""采集器单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from app.collectors.base import BaseCollector, ClueData, CollectResult
from app.collectors.configurable import ConfigurableCollector
from app.collectors.adaptors.playwright_adaptor import RenderResult


class TestClueData:
    """线索数据类测试"""

    def test_create_clue_data(self):
        """测试创建线索数据"""
        clue = ClueData(
            title="测试标题",
            url="https://example.com",
            rank=1,
            heat_value="100万"
        )
        assert clue.title == "测试标题"
        assert clue.rank == 1
        assert clue.likes == 0  # 默认值

    def test_clue_data_with_all_fields(self):
        """测试完整线索数据"""
        clue = ClueData(
            title="完整标题",
            url="https://example.com/full",
            cover_image="https://example.com/img.jpg",
            author="测试作者",
            rank=5,
            heat_value="50万",
            likes=1000,
            comments=500,
            shares=200,
            tags=["科技", "热门"]
        )
        assert clue.author == "测试作者"
        assert clue.likes == 1000
        assert len(clue.tags) == 2


class TestCollectResult:
    """采集结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = CollectResult(
            success=True,
            items=[ClueData(title="标题1"), ClueData(title="标题2")]
        )
        assert result.success == True
        assert len(result.items) == 2
        assert result.error_message is None

    def test_failure_result(self):
        """测试失败结果"""
        result = CollectResult(
            success=False,
            error_message="Connection timeout"
        )
        assert result.success == False
        assert result.error_message == "Connection timeout"
        assert len(result.items) == 0


class TestConfigurableCollector:
    """配置化采集器测试"""

    @pytest.fixture
    def collector(self):
        """创建采集器实例"""
        return ConfigurableCollector()

    def test_collector_init(self, collector):
        """测试初始化"""
        assert collector.name == "configurable"
        assert collector.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_validate_valid_config(self, collector):
        """测试有效配置验证"""
        config = {
            "url": "https://example.com",
            "parse_type": "css",
            "parse_rules": {
                "container": ".item",
                "title": ".title"
            }
        }
        assert await collector.validate(config) == True

    @pytest.mark.asyncio
    async def test_validate_missing_url(self, collector):
        """测试缺少URL配置"""
        config = {
            "parse_type": "css",
            "parse_rules": {"container": ".item"}
        }
        assert await collector.validate(config) == False

    @pytest.mark.asyncio
    async def test_validate_invalid_parse_type(self, collector):
        """测试无效解析类型"""
        config = {
            "url": "https://example.com",
            "parse_type": "invalid",
            "parse_rules": {}
        }
        assert await collector.validate(config) == False

    def test_supported_parse_types(self, collector):
        """测试支持的解析类型"""
        assert "css" in collector.supported_parse_types
        assert "json" in collector.supported_parse_types
        assert "xpath" in collector.supported_parse_types

    @pytest.mark.asyncio
    async def test_collect_with_playwright(self, collector):
        """测试Playwright动态渲染采集"""
        # Mock playwright_adaptor.render
        mock_html = '<html><body><div class="item"><span class="title">测试标题</span></div></body></html>'

        with patch('app.collectors.configurable.playwright_adaptor') as mock_adaptor:
            mock_adaptor.render = AsyncMock(return_value=RenderResult(
                success=True,
                content=mock_html,
                status_code=200
            ))

            # Mock anti_crawl module
            mock_anti_crawl = MagicMock()
            mock_anti_crawl.get_context = AsyncMock(return_value=MagicMock(
                headers={},
                cookies={},
                cookie_id=None,
                proxy=None
            ))
            mock_anti_crawl.report_success = AsyncMock()

            config = {
                "url": "https://www.douyin.com/discover",
                "use_playwright": True,
                "parse_type": "css",
                "parse_rules": {
                    "container": ".item",
                    "title": ".title"
                }
            }

            result = await collector.collect(config, mock_anti_crawl, "test_source")

            assert result.success == True
            assert result.metadata["playwright_used"] == True
            mock_adaptor.render.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_playwright_failure(self, collector):
        """测试Playwright渲染失败"""
        with patch('app.collectors.configurable.playwright_adaptor') as mock_adaptor:
            mock_adaptor.render = AsyncMock(return_value=RenderResult(
                success=False,
                error_message="Timeout waiting for page"
            ))

            mock_anti_crawl = MagicMock()
            mock_anti_crawl.get_context = AsyncMock(return_value=MagicMock(
                headers={},
                cookies={},
                cookie_id=None,
                proxy=None
            ))
            mock_anti_crawl.report_failure = AsyncMock()

            config = {
                "url": "https://example.com",
                "use_playwright": True,
                "parse_type": "css",
                "parse_rules": {"container": ".item"}
            }

            result = await collector.collect(config, mock_anti_crawl)

            assert result.success == False
            assert "Timeout" in result.error_message