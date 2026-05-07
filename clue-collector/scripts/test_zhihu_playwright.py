"""
知乎热榜采集测试脚本 - 使用 Playwright + extra_wait
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.collectors.adaptors.playwright_adaptor import playwright_adaptor
from scrapling import Selector
import json

async def test_zhihu():
    """测试知乎热榜 Playwright 渲染"""
    print("=" * 60)
    print("测试: 知乎热榜 (TopHub)")
    print("=" * 60)

    url = "https://tophub.today/n/mproPpoq6O"

    # 初始化 Playwright
    await playwright_adaptor.initialize()

    # 渲染配置（与数据库配置一致）
    config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
        "cookies": {},
    }

    # 使用 extra_wait=5000ms
    result = await playwright_adaptor.render(
        url=url,
        config=config,
        timeout=60000,
        wait_for="table tbody tr",
        wait_state="attached",
        network_idle=True,
        extra_wait=5000,  # 增加等待时间
    )

    print(f"Success: {result.success}")
    print(f"Status: {result.status_code}")
    print(f"Content Length: {len(result.content) if result.content else 0}")

    if result.error_message:
        print(f"Error: {result.error_message}")
        return

    # 使用 Scrapling Selector 解析
    response = Selector(result.content)

    # 解析规则
    parse_rules = {
        "container": "table tbody tr",
        "rank": "td:nth-child(1)",
        "title": "a:first-of-type",
        "heat": "a:first-of-type",
        "link": "a:first-of-type@href",
    }

    # 检查页面结构
    tables = response.css("table")
    print(f"\n找到 {len(tables)} 个 table")

    for i, table in enumerate(tables):
        rows = table.css("tbody tr")
        print(f"  table[{i}] 有 {len(rows)} 行")

    # 解析数据
    elements = response.css(parse_rules["container"])
    print(f"\n总共 {len(elements)} 条数据")

    items = []
    for idx, element in enumerate(elements[:10]):
        try:
            rank_text = element.css(parse_rules["rank"]).text(strip=True, first=True)
            rank = int(rank_text) if rank_text else None

            # 使用 a:first-of-type 提取标题
            title_el = element.css(parse_rules["title"])
            if title_el.first:
                title = title_el.first.text.strip() if title_el.first.text else None
                link = title_el.first.attrib.get("href")
            else:
                title = None
                link = None

            heat_text = element.css(parse_rules["heat"]).text(strip=True, first=True) or ""

            if title:
                items.append({
                    "rank": rank,
                    "title": title,
                    "heat": heat_text,
                    "link": link,
                })
                print(f"  [{rank}] {title} | {heat_text}")
        except Exception as e:
            print(f"  [{idx}] 解析失败: {e}")

    print(f"\n成功解析 {len(items)} 条数据")

    # 关闭 Playwright
    await playwright_adaptor.close()


if __name__ == "__main__":
    asyncio.run(test_zhihu())