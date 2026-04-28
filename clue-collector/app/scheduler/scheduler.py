"""分组调度器"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.storage import db_manager
from app.storage.models import SourceGroup, DataSource, DataSourceType, SourceStatus
from app.scheduler.task_queue import task_queue, Task
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """分组调度器"""

    def __init__(self):
        self.running = False
        self.interval = 60  # 扫描间隔（秒）
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """启动调度器"""
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("scheduler_started")

    async def stop(self) -> None:
        """停止调度器"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("scheduler_stopped")

    async def _run_loop(self) -> None:
        """主循环"""
        while self.running:
            try:
                await self._scan_and_schedule()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error("scheduler_loop_error", error=str(e))
                await asyncio.sleep(self.interval)

    async def _scan_and_schedule(self) -> None:
        """扫描并调度任务"""
        async with db_manager.session() as session:
            # 获取所有活跃分组
            result = await session.execute(
                select(SourceGroup).where(SourceGroup.is_active == True)
            )
            groups = result.scalars().all()

            for group in groups:
                await self._process_group(session, group)

    async def _process_group(self, session: AsyncSession, group: SourceGroup) -> None:
        """处理单个分组"""
        if not self._should_trigger(group):
            return

        # 获取分组下的活跃数据源
        result = await session.execute(
            select(DataSource)
            .where(DataSource.group_id == group.id)
            .where(DataSource.is_active == True)
            .where(DataSource.status.in_([SourceStatus.ACTIVE, SourceStatus.ERROR]))
            .order_by(DataSource.priority.desc())
        )
        sources = result.scalars().all()

        # 为每个数据源创建任务
        now = datetime.now(timezone.utc)
        for source in sources:
            task = Task(
                id=f"{source.id}_{now.timestamp()}",
                source_id=str(source.id),
                priority=source.priority,
                metadata={
                    "collector_type": source.collector_type.value,
                    "source_type": source.type.value,
                    "config": source.config
                }
            )
            await task_queue.push(task)
            logger.debug("task_scheduled", source_id=str(source.id), group=group.name)

        # 更新分组最后调度时间
        group.updated_at = now

    def _should_trigger(self, group: SourceGroup) -> bool:
        """判断是否应该触发采集"""
        if not group.is_active:
            return False

        # 检查是否达到采集间隔
        interval = timedelta(minutes=group.collect_interval)
        now = datetime.now(timezone.utc)
        if now - group.updated_at >= interval:
            return True

        return False

    async def force_trigger(self, group_id: Optional[UUID] = None) -> int:
        """强制触发采集"""
        async with db_manager.session() as session:
            if group_id:
                result = await session.execute(
                    select(SourceGroup).where(SourceGroup.id == group_id)
                )
                groups = [result.scalar_one_or_none()]
            else:
                result = await session.execute(
                    select(SourceGroup).where(SourceGroup.is_active == True)
                )
                groups = result.scalars().all()

            count = 0
            for group in groups:
                if group:
                    await self._process_group(session, group)
                    count += 1

            logger.info("force_trigger_completed", count=count)
            return count


# 全局调度器实例
scheduler = Scheduler()
