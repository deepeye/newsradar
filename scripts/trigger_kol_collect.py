"""Force trigger KOL group collection"""
import asyncio
import sys

sys.path.insert(0, "/Users/felixwang/devspace/cc-project/cqh-agent/clue-collector")

from app.storage import db_manager
from app.scheduler import scheduler
from app.anti_crawl import anti_crawl
from app.collectors.adaptors.playwright_adaptor import playwright_adaptor
from app.scheduler import task_queue, task_runner
from app.config import settings
from app.utils import configure_logging


async def main():
    configure_logging(settings.app.log_level)

    # Initialize (reuse running processes if available)
    await db_manager.initialize()
    await task_queue.initialize()
    await anti_crawl.initialize()

    # Find KOL group
    from sqlalchemy import select, text
    from app.storage.models import SourceGroup

    async with db_manager.session() as session:
        result = await session.execute(
            text("SELECT id FROM source_groups WHERE name = 'KOL监控'")
        )
        group = result.fetchone()

    if not group:
        print("No KOL group found!")
        return

    group_id = group[0]
    print(f"Force triggering KOL group: {group_id}")

    # Force trigger
    count = await scheduler.force_trigger(group_id)
    print(f"Triggered {count} groups")

    # Start task runner to execute the queued tasks
    await task_runner.start()

    # Wait for tasks to complete (max 3 min)
    for _ in range(180):
        main_q_size = await task_queue.size()
        retry_q_size = await task_queue.retry_size()
        if main_q_size == 0 and retry_q_size == 0:
            print("All tasks completed!")
            break
        await asyncio.sleep(1)

    await task_runner.stop()
    await anti_crawl.close()
    await task_queue.close()
    await db_manager.close()


asyncio.run(main())