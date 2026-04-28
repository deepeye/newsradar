"""服务主入口"""
import asyncio
import signal
from contextlib import asynccontextmanager

import structlog

from app.config import settings
from app.storage import db_manager
from app.scheduler import task_queue, scheduler, task_runner
from app.anti_crawl import anti_crawl
from app.utils import configure_logging
from app.collectors.adaptors.playwright_adaptor import playwright_adaptor


logger = structlog.get_logger()


class Application:
    """应用主类"""

    def __init__(self):
        self.running = False
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """初始化应用"""
        configure_logging(settings.app.log_level)
        logger.info("application_starting", version=settings.app.version)

        # 初始化数据库
        await db_manager.initialize()
        logger.info("database_initialized")

        # 初始化任务队列
        await task_queue.initialize()
        logger.info("task_queue_initialized")

        # 初始化反爬模块
        await anti_crawl.initialize()
        logger.info("anti_crawl_initialized")

        # 初始化Playwright动态渲染
        await playwright_adaptor.initialize()
        logger.info("playwright_initialized")

        # 启动调度器
        await scheduler.start()
        logger.info("scheduler_started")

        # 启动任务执行器
        await task_runner.start()
        logger.info("task_runner_started")

    async def shutdown(self) -> None:
        """关闭应用"""
        logger.info("application_shutting_down")
        self.running = False
        self._shutdown_event.set()

        # 停止任务执行器
        await task_runner.stop()
        logger.info("task_runner_stopped")

        # 停止调度器
        await scheduler.stop()
        logger.info("scheduler_stopped")

        # 关闭反爬模块
        await anti_crawl.close()
        logger.info("anti_crawl_closed")

        # 关闭Playwright
        await playwright_adaptor.close()
        logger.info("playwright_closed")

        # 关闭任务队列
        await task_queue.close()
        logger.info("task_queue_closed")

        # 关闭数据库连接
        await db_manager.close()
        logger.info("database_closed")

        logger.info("application_shutdown_complete")

    async def run(self) -> None:
        """运行应用主循环"""
        await self.initialize()
        self.running = True

        logger.info("application_running")

        # 主循环
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass

        await self.shutdown()


def handle_signals(app: Application) -> None:
    """处理系统信号"""
    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(app.shutdown()))


async def main() -> None:
    """主函数"""
    app = Application()
    handle_signals(app)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
