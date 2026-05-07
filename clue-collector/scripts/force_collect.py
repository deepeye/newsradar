"""手动触发采集测试 - 完整初始化"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.storage import db_manager
from app.scheduler.task_queue import task_queue
from app.scheduler.scheduler import scheduler

async def force_collect():
    """强制触发所有分组采集"""
    # 初始化所有必要组件
    await db_manager.initialize()
    await task_queue.initialize()

    # 强制触发
    count = await scheduler.force_trigger()
    print(f"✅ 强制触发采集完成，触发 {count} 个分组")

    # 等待任务执行
    print("等待任务执行...")
    await asyncio.sleep(30)

    # 关闭
    await task_queue.close()
    await db_manager.close()

asyncio.run(force_collect())