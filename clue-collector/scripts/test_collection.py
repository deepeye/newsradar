"""
采集测试脚本 - 调试解析规则
"""
import asyncio
import json
import sys

sys.path.insert(0, '/app')

from scrapling import Fetcher
from app.anti_crawl import anti_crawl
from app.storage import db_manager


async def test_weibo():
    """测试微博采集"""
    print("=" * 60)
    print("测试: 微博热搜")
    print("=" * 60)

    await anti_crawl.initialize()
    context = await anti_crawl.get_context("10000000-0000-0000-0000-000000000001")

    fetcher = Fetcher()

    try:
        response = fetcher.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={"Referer": "https://weibo.com"},
            cookies=context.cookies
        )

        print(f"状态: {response.status}")

        # 尝试解析JSON
        try:
            data = response.json()
            print(f"JSON结构预览: {json.dumps(data, ensure_ascii=False, indent=2)[:2000]}...")

            # 测试解析规则
            if 'data' in data and 'realtime' in data['data']:
                items = data['data']['realtime']
                print(f"\n找到 {len(items)} 条热搜")
                for i, item in enumerate(items[:5]):
                    print(f"  [{i+1}] {item.get('note', 'N/A')} - {item.get('num', 'N/A')}")
        except Exception as e:
            print(f"JSON解析失败: {e}")
            print(f"响应内容: {response.text[:500]}")

    except Exception as e:
        print(f"请求失败: {e}")

    await anti_crawl.close()
    print()


async def test_bilibili():
    """测试B站采集"""
    print("=" * 60)
    print("测试: B站热门")
    print("=" * 60)

    fetcher = Fetcher()

    try:
        response = fetcher.get(
            "https://api.bilibili.com/x/web-interface/popular",
            headers={"Referer": "https://www.bilibili.com"}
        )

        print(f"状态: {response.status}")

        try:
            data = response.json()
            if data.get('data') and 'list' in data['data']:
                items = data['data']['list']
                print(f"\n找到 {len(items)} 条热门视频")
                for i, item in enumerate(items[:3]):
                    print(f"  [{i+1}] {item.get('title', 'N/A')} by {item.get('owner', {}).get('name', 'N/A')}")
            else:
                print(f"数据结构: {json.dumps(data, ensure_ascii=False, indent=2)[:1000]}")
        except Exception as e:
            print(f"解析失败: {e}")

    except Exception as e:
        print(f"请求失败: {e}")

    print()


async def test_baidu():
    """测试百度热搜"""
    print("=" * 60)
    print("测试: 百度热搜")
    print("=" * 60)

    fetcher = Fetcher()

    try:
        response = fetcher.get("https://top.baidu.com/board?tab=realtime")
        print(f"状态: {response.status}")

        # CSS解析
        elements = response.css(".content_1YWBm .item-wrap_2P2WB")
        print(f"\n找到 {len(elements)} 个元素")

        for i, el in enumerate(elements[:3]):
            try:
                title = el.css(".content-title_3k3PR a").text(strip=True, first=True)
                print(f"  [{i+1}] {title}")
            except Exception as e:
                print(f"  [{i+1}] 解析失败: {e}")

    except Exception as e:
        print(f"请求失败: {e}")

    print()


async def main():
    await db_manager.initialize()
    await test_weibo()
    await test_bilibili()
    await test_baidu()
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())