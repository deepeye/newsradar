"""任务执行器"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.scheduler.task_queue import task_queue, Task
from app.storage import db_manager
from app.storage.repository import DataSourceRepository, ClueRepository, CollectLogRepository
from app.storage.models import DataSource, CollectStatus, DataSourceType, CollectorType
from app.collectors import ConfigurableCollector
from app.anti_crawl import anti_crawl
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskRunner:
    """任务执行器"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.running = False
        self._workers: list[asyncio.Task] = []
        self._collectors = {
            CollectorType.CONFIGURABLE: ConfigurableCollector(),
        }

    async def start(self) -> None:
        """启动执行器"""
        self.running = True

        # 启动worker
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

        logger.info("task_runner_started", workers=self.max_workers)

    async def stop(self) -> None:
        """停止执行器"""
        self.running = False

        # 取消所有worker
        for worker in self._workers:
            worker.cancel()

        # 等待所有worker完成
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("task_runner_stopped")

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker循环"""
        logger.info("worker_started", worker_id=worker_id)

        while self.running:
            try:
                task = await task_queue.pop(timeout=5)
                if task:
                    await self._execute_task(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("worker_error", worker_id=worker_id, error=str(e))

        logger.info("worker_stopped", worker_id=worker_id)

    async def _execute_task(self, task: Task) -> None:
        """执行单个任务"""
        source_id = task.source_id
        logger.info("task_execution_started", task_id=task.id, source_id=source_id)

        async with db_manager.session() as session:
            # 创建日志记录
            log_repo = CollectLogRepository(session)
            log = await log_repo.create(
                source_id=source_id,
                status=CollectStatus.SUCCESS,
                retry_count=task.retry_count
            )

            started_at = datetime.now(timezone.utc)

            try:
                # 获取数据源配置
                ds_repo = DataSourceRepository(session)
                source = await ds_repo.get_by_id(source_id)

                if not source:
                    raise ValueError(f"Data source not found: {source_id}")

                if not source.is_active:
                    logger.info("source_inactive", source_id=source_id)
                    await task_queue.complete(task)
                    return

                # 获取采集器
                collector = self._get_collector(source.collector_type)
                if not collector:
                    raise ValueError(f"Collector not found: {source.collector_type}")

                # 执行采集
                result = await collector.collect(source.config, anti_crawl, source_id)

                if result.success:
                    # 保存采集结果
                    clue_repo = ClueRepository(session)
                    saved_count = 0

                    for item in result.items:
                        clue, is_new = await clue_repo.create_or_update(
                            source_id=source_id,
                            title=item.title,
                            url=item.url,
                            cover_image=item.cover_image,
                            author=item.author,
                            rank=item.rank,
                            heat_value=item.heat_value,
                            likes=item.likes,
                            comments=item.comments,
                            shares=item.shares,
                            tags=item.tags
                        )
                        if is_new:
                            saved_count += 1

                    # 完成日志
                    duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
                    await log_repo.finish(
                        log_id=log.id,
                        status=CollectStatus.SUCCESS,
                        items_count=saved_count,
                    )

                    # 更新数据源状态
                    await ds_repo.record_success(source_id)

                    logger.info("task_execution_completed",
                              task_id=task.id,
                              items_count=len(result.items),
                              saved_count=saved_count,
                              duration_ms=duration_ms)

                else:
                    # 采集失败
                    raise Exception(result.error_message or "Collection failed")

                await task_queue.complete(task)

            except Exception as e:
                logger.error("task_execution_failed",
                           task_id=task.id,
                           error=str(e))

                # 记录失败日志
                duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
                await log_repo.finish(
                    log_id=log.id,
                    status=CollectStatus.FAILED,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )

                # 更新数据源失败状态
                ds_repo = DataSourceRepository(session)
                await ds_repo.record_failure(source_id, str(e))

                # 重试逻辑
                if task.retry_count < 3:
                    await task_queue.retry(task, delay=60 * (task.retry_count + 1))
                else:
                    await task_queue.complete(task)

    def _get_collector(self, collector_type: CollectorType):
        """获取采集器实例"""
        return self._collectors.get(collector_type)


# 全局执行器实例
task_runner = TaskRunner()
