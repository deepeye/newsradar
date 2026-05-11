"""配置化采集器"""
import json
import re
from typing import Dict, Any, List, Optional

from scrapling import Fetcher, Selector

from app.collectors.base import BaseCollector, ClueData, CollectResult
from app.anti_crawl import AntiCrawlModule
from app.collectors.adaptors.playwright_adaptor import playwright_adaptor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigurableCollector(BaseCollector):
    """配置化采集器 - 通过JSON配置描述采集规则

    基于 scrapling 框架实现，支持:
    - CSS/XPath/JSON 解析
    - Playwright 动态渲染
    - 智能元素提取
    """

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
                    wait_state=config.get("wait_selector_state", "attached"),
                    network_idle=config.get("network_idle", True),
                    extra_wait=config.get("extra_wait", 2000),
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
        """使用CSS选择器解析 - 基于 scrapling Selector"""
        items = []
        container = rules.get("container", "")

        if container:
            elements = response.css(container)
        else:
            elements = [response]

        logger.debug(f"css_parse_start", container=container, elements_count=len(elements))

        for idx, element in enumerate(elements):
            try:
                # 提取标题
                title = self._extract_css_text(element, rules.get("title", ""))
                if not title:
                    logger.debug(f"css_parse_no_title", element_idx=idx)
                    continue

                # 提取链接
                link = self._extract_css_attr(element, rules.get("link", ""), "href")
                logger.debug(f"css_parse_item", element_idx=idx, title=title[:30], link=link[:50] if link else None)

                # 提取热度值 - 改进处理，提取纯数字
                heat_text = self._extract_css_text(element, rules.get("heat", ""))
                heat_value = self._parse_heat_value(heat_text)

                # 提取排名
                rank_text = self._extract_css_text(element, rules.get("rank", ""))
                rank = self._parse_rank_value(rank_text)

                # 提取作者/来源
                author = self._extract_css_text(element, rules.get("author", ""))

                # 提取摘要/片段
                snippet = self._extract_css_text(element, rules.get("snippet", ""))

                clue = ClueData(
                    title=title,
                    url=link,
                    author=author,
                    rank=rank,
                    heat_value=heat_value,
                    original_content=snippet,
                )
                items.append(clue)
            except Exception as e:
                logger.debug(f"css_parse_error", element_idx=idx, error=str(e))
                continue

        logger.debug(f"css_parse_done", items_count=len(items))
        return items

    def _extract_css_text(self, element, selector: str) -> Optional[str]:
        """提取CSS选择器的文本内容"""
        if not selector:
            return None
        try:
            # scrapling Selector 支持 ::text 伪元素
            if "::text" in selector:
                result = element.css(selector)
                return result.get() if result else None
            else:
                result = element.css(selector)
                if result.first:
                    # 获取元素的所有文本
                    return result.first.get_all_text(strip=True) if hasattr(result.first, 'get_all_text') else result.first.text.strip() if result.first.text else None
                return None
        except Exception:
            return None

    def _extract_css_attr(self, element, selector: str, attr: str) -> Optional[str]:
        """提取CSS选择器的属性值"""
        if not selector:
            return None
        try:
            # 处理 @attr 语法 (如 "a@href")
            if "@" in selector:
                parts = selector.split("@")
                css_sel = parts[0]
                attr_name = parts[1] if len(parts) > 1 else attr
                result = element.css(css_sel)
                if result.first:
                    return result.first.attrib.get(attr_name)
                return None

            # 处理 ::attr(name) 语法
            if "::attr" in selector:
                result = element.css(selector)
                return result.get() if result else None

            result = element.css(selector)
            if result.first:
                return result.first.attrib.get(attr)
            return None
        except Exception:
            return None

    def _parse_heat_value(self, heat_text: Optional[str]) -> Optional[str]:
        """解析热度值，提取纯数字"""
        if not heat_text:
            return None
        # 提取数字部分（支持 "123万"、"1.2亿"、"12345" 等格式）
        heat_text = heat_text.strip()
        # 匹配数字和单位
        match = re.search(r'(\d+\.?\d*)\s*(万|亿)?', heat_text)
        if match:
            num = float(match.group(1))
            unit = match.group(2)
            if unit == '万':
                num *= 10000
            elif unit == '亿':
                num *= 100000000
            return str(int(num))
        return heat_text

    def _parse_rank_value(self, rank_text: Optional[str]) -> Optional[int]:
        """解析排名值"""
        if not rank_text:
            return None
        # 提取数字部分
        match = re.search(r'\d+', rank_text.strip())
        if match:
            return int(match.group())
        return None

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
                        # Collect values from rules-defined paths first
                        for key, path in rules.items():
                            if key != "link" and f"{{{key}}}" in template:
                                value = self._get_nested_value(element, path)
                                if value:
                                    format_args[key] = value
                        # Also resolve template placeholders from element fields directly
                        import re as _re
                        for placeholder in _re.findall(r'\{(\w+)\}', template):
                            if placeholder not in format_args:
                                value = self._get_nested_value(element, placeholder)
                                if value:
                                    format_args[placeholder] = value
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

    def _extract_xpath_text(self, element, xpath: str) -> Optional[str]:
        """提取XPath文本"""
        if not xpath:
            return None
        try:
            result = element.xpath(xpath)
            if result:
                return result[0].text.strip() if result[0].text else None
            return None
        except Exception:
            return None

    def _extract_xpath_attr(self, element, xpath: str, attr: str) -> Optional[str]:
        """提取XPath属性"""
        if not xpath:
            return None
        try:
            result = element.xpath(xpath)
            if result:
                return result[0].attrib.get(attr)
            return None
        except Exception:
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
