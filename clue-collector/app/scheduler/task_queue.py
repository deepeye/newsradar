"""Redis任务队列"""
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

import redis.asyncio as redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Task:
    """采集任务"""
    id: str
    source_id: str
    priority: int = 5
    retry_count: int = 0
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)


class TaskQueue:
    """Redis任务队列管理器"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.queue_key = "clue_collector:tasks"
        self.retry_queue_key = "clue_collector:tasks:retry"
        self.processing_key = "clue_collector:tasks:processing"

    async def initialize(self) -> None:
        """初始化Redis连接"""
        self.redis = redis.from_url(
            settings.redis.url,
            decode_responses=True
        )
        logger.info("task_queue_initialized")

    async def close(self) -> None:
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            logger.info("task_queue_closed")

    async def push(self, task: Task) -> bool:
        """推送任务到队列（按优先级）"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        task.created_at = datetime.utcnow().isoformat()
        task_data = json.dumps(task.to_dict())

        # 使用优先级分数（分数越低优先级越高）
        score = 10 - task.priority
        await self.redis.zadd(self.queue_key, {task_data: score})

        logger.debug("task_pushed", task_id=task.id, source_id=task.source_id)
        return True

    async def pop(self, timeout: int = 5) -> Optional[Task]:
        """从队列获取任务（阻塞）"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        # 获取优先级最高的任务
        result = await self.redis.zpopmin(self.queue_key)

        if result:
            task_data = result[0][0]
            task = Task.from_dict(json.loads(task_data))

            # 标记为处理中
            await self.redis.hset(
                self.processing_key,
                task.id,
                json.dumps({
                    "started_at": datetime.utcnow().isoformat(),
                    "source_id": task.source_id
                })
            )

            logger.debug("task_popped", task_id=task.id)
            return task

        return None

    async def complete(self, task: Task) -> bool:
        """标记任务完成"""
        if not self.redis:
            return False

        await self.redis.hdel(self.processing_key, task.id)
        logger.debug("task_completed", task_id=task.id)
        return True

    async def retry(self, task: Task, delay: int = 60) -> bool:
        """将任务放入重试队列"""
        if not self.redis:
            return False

        task.retry_count += 1
        task_data = json.dumps(task.to_dict())

        # 计算重试时间
        retry_at = datetime.utcnow().timestamp() + delay
        await self.redis.zadd(self.retry_queue_key, {task_data: retry_at})

        await self.redis.hdel(self.processing_key, task.id)
        logger.info("task_queued_for_retry", task_id=task.id, retry_count=task.retry_count)
        return True

    async def move_retry_to_main(self) -> int:
        """将到期的重试任务移回主队列"""
        if not self.redis:
            return 0

        now = datetime.utcnow().timestamp()
        tasks_to_retry = await self.redis.zrangebyscore(
            self.retry_queue_key,
            0,
            now
        )

        count = 0
        for task_data in tasks_to_retry:
            task = Task.from_dict(json.loads(task_data))
            await self.push(task)
            await self.redis.zrem(self.retry_queue_key, task_data)
            count += 1

        if count > 0:
            logger.info("retry_tasks_moved", count=count)

        return count

    async def get_queue_size(self) -> int:
        """获取队列大小"""
        if not self.redis:
            return 0
        return await self.redis.zcard(self.queue_key)

    async def get_processing_count(self) -> int:
        """获取正在处理的任务数"""
        if not self.redis:
            return 0
        return await self.redis.hlen(self.processing_key)

    async def clear(self) -> bool:
        """清空队列"""
        if not self.redis:
            return False

        await self.redis.delete(self.queue_key)
        await self.redis.delete(self.retry_queue_key)
        await self.redis.delete(self.processing_key)
        logger.info("task_queue_cleared")
        return True


# 全局队列实例
task_queue = TaskQueue()
