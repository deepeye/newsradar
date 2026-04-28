"""
诊断采集解析问题
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from app.collectors.configurable import ConfigurableCollector
from app.anti_crawl import anti_crawl
from app.storage import db_manager


async def test_collector():
    await db_manager.initialize()
    await anti_crawl.initialize()

    collector = ConfigurableCollector()

    # 测试微博配置
    weibo_config = {
        "url": "https://weibo.com/ajax/side/hotSearch",
        "method": "GET",
        "parse_type": "json",
        "parse_rules": {
            "container": "data.realtime",
            "title": "note",
            "rank": "rank",
            "heat": "num",
            "link": {"template": "https://s.weibo.com/weibo?q={word}"},
            "word": "word"
        },
        "headers": {
            "Referer": "https://weibo.com"
        }
    }

    print("测试微博采集...")
    result = await collector.collect(weibo_config, anti_crawl, "10000000-0000-0000-0000-000000000001")
    print(f"  成功: {result.success}")
    print(f"  条数: {len(result.items)}")
    print(f"  错误: {result.error_message}")
    print(f"  元数据: {result.metadata}")
    if result.items:
        for i, item in enumerate(result.items[:3]):
            print(f"    [{i+1}] {item.title} - {item.heat_value}")

    print()

    # 测试B站配置
    bilibili_config = {
        "url": "https://api.bilibili.com/x/web-interface/popular",
        "method": "GET",
        "parse_type": "json",
        "parse_rules": {
            "container": "data.list",
            "title": "title",
            "author": "owner.name",
            "link": {"template": "https://www.bilibili.com/video/{bvid}"},
            "bvid": "bvid"
        },
        "headers": {
            "Referer": "https://www.bilibili.com"
        }
    }

    print("测试B站采集...")
    result = await collector.collect(bilibili_config, anti_crawl, "10000000-0000-0000-0000-000000000005")
    print(f"  成功: {result.success}")
    print(f"  条数: {len(result.items)}")
    print(f"  错误: {result.error_message}")
    print(f"  元数据: {result.metadata}")
    if result.items:
        for i, item in enumerate(result.items[:3]):
            print(f"    [{i+1}] {item.title} by {item.author}")

    await anti_crawl.close()
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_collector())