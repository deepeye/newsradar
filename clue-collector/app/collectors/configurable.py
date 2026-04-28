"""配置化采集器"""
import json
from typing import Dict, Any, List, Optional

from scrapling import Fetcher, Selector

from app.collectors.base import BaseCollector, ClueData, CollectResult
from app.anti_crawl import AntiCrawlModule
from app.collectors.adaptors.playwright_adaptor import playwright_adaptor


class ConfigurableCollector(BaseCollector):
    """配置化采集器 - 通过JSON配置描述采集规则"""

    def __init__(self):
        super().__init__("configurable", "1.0.0")
        self.supported_parse_types = ["css", "json", "xpath"]

    async def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        required_fields = ["url", "parse_type", "parse_rules"]
        for field in required_fields:
            if field not in config:
                return False

        if config["parse_type"] not in self.supported_parse_types:
            return False

        if not isinstance(config["parse_rules"], dict):
            return False

        return True

    async def collect(
        self,
        config: Dict[str, Any],
        anti_crawl: AntiCrawlModule,
        source_id: str = None
    ) -> CollectResult:
        """执行配置化采集"""
        # 使用数据源ID进行Cookie轮换
        cookie_source_id = source_id if source_id else "default"
        context = await anti_crawl.get_context(cookie_source_id)

        try:
            # 检查是否使用Playwright动态渲染
            use_playwright = config.get("use_playwright", False)

            if use_playwright:
                # 使用Playwright渲染动态页面
                render_result = await playwright_adaptor.render(
                    url=config["url"],
                    config={
                        "headers": context.headers or {},
                        "cookies": context.cookies or {},
                        "user_agent": context.headers.get("User-Agent") if context.headers else None,
                    },
                    timeout=config.get("timeout", 30000),
                    wait_for=config.get("wait_for_selector"),
                )

                if not render_result.success:
                    await anti_crawl.report_failure(
                        cookie_source_id,
                        cookie_id=context.cookie_id,
                        proxy=context.proxy,
                    )
                    return CollectResult(
                        success=False,
                        error_message=render_result.error_message or "Playwright render failed"
                    )

                # 使用Scrapling Selector解析渲染后的HTML
                response = Selector(render_result.content)

                # 报告成功
                await anti_crawl.report_success(
                    cookie_source_id,
                    cookie_id=context.cookie_id,
                    proxy=context.proxy
                )

            else:
                # 使用Scrapling静态请求（原有逻辑）
                fetcher = Fetcher(
                    retries=3,
                    timeout=30
                )

                # 合并headers
                headers = context.headers or {}
                if config.get("headers"):
                    headers.update(config["headers"])

                # 执行请求（同步调用）
                response = fetcher.get(
                    config["url"],
                    headers=headers,
                    proxy=context.proxy,
                    cookies=context.cookies
                )

                # Scrapling响应对象没有status_code属性，但有status属性
                # 检查响应状态
                status_code = getattr(response, 'status_code', getattr(response, 'status', 200))
                if status_code >= 400:
                    # 报告失败（会处理Cookie失效）
                    await anti_crawl.report_failure(
                        cookie_source_id,
                        cookie_id=context.cookie_id,
                        proxy=context.proxy,
                        status_code=status_code
                    )
                    return CollectResult(
                        success=False,
                        error_message=f"HTTP {status_code}"
                    )

                # 报告成功（更新Cookie成功次数）
                await anti_crawl.report_success(
                    cookie_source_id,
                    cookie_id=context.cookie_id,
                    proxy=context.proxy
                )

            # 解析数据（通用处理）
            parse_type = config.get("parse_type", "css")
            rules = config["parse_rules"]

            if parse_type == "css":
                items = self._parse_css(response, rules)
            elif parse_type == "json":
                items = self._parse_json(response, rules)
            elif parse_type == "xpath":
                items = self._parse_xpath(response, rules)
            else:
                return CollectResult(
                    success=False,
                    error_message=f"Unsupported parse type: {parse_type}"
                )

            return CollectResult(
                success=True,
                items=items,
                metadata={
                    "url": config["url"],
                    "parse_type": parse_type,
                    "items_count": len(items),
                    "cookie_used": context.cookie_id is not None,
                    "playwright_used": use_playwright,
                }
            )

        except Exception as e:
            # 报告失败
            await anti_crawl.report_failure(
                cookie_source_id,
                cookie_id=context.cookie_id,
                proxy=context.proxy
            )
            return CollectResult(
                success=False,
                error_message=str(e)
            )

    def _parse_css(self, response, rules: Dict[str, Any]) -> List[ClueData]:
        """使用CSS选择器解析"""
        items = []
        container = rules.get("container", "")

        if container:
            elements = response.css(container)
        else:
            elements = [response]

        for element in elements:
            try:
                clue = ClueData(
                    title=self._extract_text(element, rules.get("title", "")),
                    url=self._extract_attr(element, rules.get("link", ""), "href"),
                    author=self._extract_text(element, rules.get("author", "")),
                    rank=self._extract_int(element, rules.get("rank", "")),
                    heat_value=self._extract_text(element, rules.get("heat", "")),
                )
                if clue.title:
                    items.append(clue)
            except Exception:
                continue

        return items

    def _parse_json(self, response, rules: Dict[str, Any]) -> List[ClueData]:
        """使用JSON解析"""
        items = []
        try:
            data = response.json()
            container_path = rules.get("container", "")

            if container_path:
                elements = self._get_nested_value(data, container_path)
                if not isinstance(elements, list):
                    elements = [elements] if elements else []
            else:
                elements = data if isinstance(data, list) else [data]

            for element in elements:
                try:
                    title = self._get_nested_value(element, rules.get("title", ""))
                    if not title:
                        continue

                    # 处理链接模板
                    link = None
                    link_rule = rules.get("link")
                    if isinstance(link_rule, dict) and "template" in link_rule:
                        template = link_rule["template"]
                        format_args = {}
                        for key, path in rules.items():
                            if key != "link" and f"{{{key}}}" in template:
                                value = self._get_nested_value(element, path)
                                if value:
                                    format_args[key] = value
                        try:
                            link = template.format(**format_args)
                        except KeyError:
                            link = None
                    elif link_rule:
                        link = self._get_nested_value(element, link_rule)

                    # 提取并转换类型
                    heat = self._get_nested_value(element, rules.get("heat", ""))
                    if heat is not None:
                        heat = str(heat)  # 转换为字符串

                    rank = self._get_nested_value(element, rules.get("rank", ""))
                    if rank is not None and not isinstance(rank, int):
                        try:
                            rank = int(rank)
                        except (ValueError, TypeError):
                            rank = None

                    clue = ClueData(
                        title=str(title) if title else None,
                        url=link,
                        author=self._get_nested_value(element, rules.get("author", "")),
                        rank=rank,
                        heat_value=heat,
                    )
                    items.append(clue)
                except Exception:
                    continue
        except Exception:
            pass

        return items

    def _parse_xpath(self, response, rules: Dict[str, Any]) -> List[ClueData]:
        """使用XPath解析"""
        items = []
        container = rules.get("container", "")

        if container:
            elements = response.xpath(container)
        else:
            elements = [response]

        for element in elements:
            try:
                clue = ClueData(
                    title=self._extract_xpath_text(element, rules.get("title", "")),
                    url=self._extract_xpath_attr(element, rules.get("link", ""), "href"),
                    author=self._extract_xpath_text(element, rules.get("author", "")),
                )
                if clue.title:
                    items.append(clue)
            except Exception:
                continue

        return items

    def _extract_text(self, element, selector: str) -> Optional[str]:
        """提取文本"""
        if not selector:
            return None
        try:
            # Scrapling 0.4.1: css returns Selectors, need .first to get Selector, then .text
            result = element.css(selector)
            if result.first:
                return result.first.text.strip() if result.first.text else None
            return None
        except Exception:
            return None

    def _extract_attr(self, element, selector: str, attr: str) -> Optional[str]:
        """提取属性"""
        if not selector:
            return None
        try:
            result = element.css(selector)
            if result.first:
                return result.first.attrib.get(attr)
            return None
        except Exception:
            return None

    def _extract_int(self, element, selector: str) -> Optional[int]:
        """提取整数"""
        text = self._extract_text(element, selector)
        if text:
            try:
                return int(text.replace(',', ''))
            except ValueError:
                return None
        return None

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """获取嵌套值"""
        if not path:
            return None
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return None
            if current is None:
                return None
        return current

    def _extract_xpath_text(self, element, xpath: str) -> Optional[str]:
        """提取XPath文本"""
        if not xpath:
            return None
        try:
            result = element.xpath(xpath)
            return result[0].text if result else None
        except Exception:
            return None

    def _extract_xpath_attr(self, element, xpath: str, attr: str) -> Optional[str]:
        """提取XPath属性"""
        if not xpath:
            return None
        try:
            result = element.xpath(xpath)
            return result[0].attrs.get(attr) if result else None
        except Exception:
            return None
