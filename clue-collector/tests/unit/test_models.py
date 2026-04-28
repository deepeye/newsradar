"""模型单元测试"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.storage.models import (
    SourceGroup, DataSource, Clue, HotlistHistory, CollectLog,
    DataSourceType, CollectorType, SourceStatus, CollectStatus, ChangeType
)


class TestSourceGroup:
    """数据源分组测试"""

    def test_create_source_group(self):
        """测试创建分组"""
        group = SourceGroup(
            name="热榜组",
            collect_interval=5,
            is_active=True
        )
        assert group.name == "热榜组"
        assert group.collect_interval == 5
        assert group.is_active == True

    def test_source_group_repr(self):
        """测试字符串表示"""
        group = SourceGroup(name="测试组")
        assert "SourceGroup" in repr(group)
        assert group.name in repr(group)


class TestDataSource:
    """数据源配置测试"""

    def test_create_data_source(self):
        """测试创建数据源"""
        source = DataSource(
            group_id=uuid4(),
            name="微博热搜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={"url": "https://weibo.com/hot"},
            priority=9,
            is_active=True,
            status=SourceStatus.ACTIVE
        )
        assert source.name == "微博热搜"
        assert source.type == DataSourceType.HOTLIST
        assert source.priority == 9

    def test_source_status_enum(self):
        """测试状态枚举"""
        assert SourceStatus.ACTIVE.value == "active"
        assert SourceStatus.PAUSED.value == "paused"
        assert SourceStatus.ERROR.value == "error"


class TestClue:
    """线索数据测试"""

    def test_create_clue(self):
        """测试创建线索"""
        clue = Clue(
            source_id=uuid4(),
            title="测试标题",
            url="https://example.com",
            rank=1,
            heat_value="100万",
            unique_hash="abc123"
        )
        assert clue.title == "测试标题"
        assert clue.rank == 1
        assert clue.heat_value == "100万"

    def test_clue_with_tags(self):
        """测试带标签的线索"""
        clue = Clue(
            source_id=uuid4(),
            title="带标签的标题",
            tags=["科技", "AI", "热门"],
            unique_hash="def456"
        )
        assert len(clue.tags) == 3
        assert "科技" in clue.tags


class TestCollectLog:
    """采集日志测试"""

    def test_create_success_log(self):
        """测试成功日志"""
        log = CollectLog(
            source_id=uuid4(),
            status=CollectStatus.SUCCESS,
            items_count=50
        )
        assert log.status == CollectStatus.SUCCESS
        assert log.items_count == 50

    def test_create_failure_log(self):
        """测试失败日志"""
        log = CollectLog(
            source_id=uuid4(),
            status=CollectStatus.FAILED,
            error_type="network_timeout",
            error_message="Connection timed out"
        )
        assert log.status == CollectStatus.FAILED
        assert log.error_type == "network_timeout"


class TestHotlistHistory:
    """热榜历史测试"""

    def test_create_history(self):
        """测试创建历史记录"""
        history = HotlistHistory(
            clue_id=uuid4(),
            change_type=ChangeType.RANK_UP,
            old_rank=10,
            new_rank=5
        )
        assert history.change_type == ChangeType.RANK_UP
        assert history.old_rank == 10
        assert history.new_rank == 5


class TestEnums:
    """枚举类型测试"""

    def test_data_source_type(self):
        """测试数据源类型枚举"""
        types = [DataSourceType.HOTLIST, DataSourceType.ACCOUNT,
                DataSourceType.VIDEO, DataSourceType.CUSTOM]
        for t in types:
            assert isinstance(t.value, str)

    def test_collector_type(self):
        """测试采集器类型枚举"""
        assert CollectorType.CONFIGURABLE.value == "configurable"
        assert CollectorType.PLUGIN.value == "plugin"

    def test_change_type(self):
        """测试变化类型枚举"""
        changes = [ChangeType.NEW, ChangeType.RANK_UP,
                  ChangeType.RANK_DOWN, ChangeType.OFF]
        for c in changes:
            assert isinstance(c.value, str)