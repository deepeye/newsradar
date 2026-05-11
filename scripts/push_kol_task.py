"""Trigger X KOL collection by pushing task to Redis queue"""
import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, "/Users/felixwang/devspace/cc-project/cqh-agent/clue-collector")

from app.config import settings
from app.scheduler.task_queue import Task


async def main():
    import redis.asyncio as redis_lib

    r = redis_lib.from_url(settings.redis.url, decode_responses=True)

    source_id = "f15cfbc9-10ce-4ccf-85d3-f0a53e34d666"
    now = datetime.utcnow().isoformat()
    timestamp = datetime.utcnow().timestamp()

    task = Task(
        id=f"{source_id}_{timestamp}",
        source_id=source_id,
        priority=1,
        retry_count=0,
        created_at=now,
        metadata={
            "collector_type": "kol",
            "source_type": "ACCOUNT",
            "config": {
                "platform": "x",
                "platform_id": "elonmusk",
                "screen_name": "Elon Musk",
            },
        },
    )

    task_data = json.dumps(task.to_dict())
    score = 10 - task.priority  # 9 = high priority
    await r.zadd("clue_collector:tasks", {task_data: score})

    print(f"Pushed task: {task.id}")
    print(f"Queue size: {await r.zcard('clue_collector:tasks')}")

    await r.close()


asyncio.run(main())