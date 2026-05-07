"""
TopHub 解析规则测试 - 查看实际 HTML 结构
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.collectors.adaptors.playwright_adaptor import playwright_adaptor
from scrapling import Selector

async def test_tophub_structure():
    """分析 TopHub 页面真实结构"""
    await playwright_adaptor.initialize()

    # 测试知乎热榜
    result = await playwright_adaptor.render(
        url="https://tophub.today/n/mproPpoq6O",
        config={
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        },
        timeout=60000,
        wait_for="table tbody tr",
        wait_state="attached",
        network_idle=True,
        extra_wait=5000,
    )

    if not result.success:
        print(f"Render failed: {result.error_message}")
        await playwright_adaptor.close()
        return

    print(f"Content length: {len(result.content)}")

    sel = Selector(result.content)

    # 分析 table 结构
    tables = sel.css('table')
    print(f"\nTables count: {len(tables)}")

    for i, table in enumerate(tables):
        # 检查 table header
        header_rows = table.css('thead tr')
        if header_rows:
            header = header_rows[0].css('th')
            header_texts = [th.get_all_text(strip=True) if hasattr(th, 'get_all_text') else str(th) for th in header]
            print(f"  Table {i} header: {header_texts}")

        # 检查第一行数据
        rows = table.css('tbody tr')
        print(f"  Table {i} rows: {len(rows)}")

        if rows:
            first_row = rows[0]
            tds = first_row.css('td')
            print(f"  First row td count: {len(tds)}")

            for j, td in enumerate(tds):
                text = td.get_all_text(strip=True) if hasattr(td, 'get_all_text') else str(td)
                print(f"    td[{j}]: {text[:50]}...")

                # 检查 td 内的元素
                links = td.css('a')
                if links:
                    print(f"      Links: {len(links)}, first text: {links.first.text[:30] if links.first else 'N/A'}")

    await playwright_adaptor.close()


if __name__ == "__main__":
    asyncio.run(test_tophub_structure())