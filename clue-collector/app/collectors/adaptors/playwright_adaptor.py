"""Playwright 动态渲染适配器"""
import asyncio
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RenderResult:
    """渲染结果"""
    success: bool
    content: Optional[str] = None
    status_code: int = 200
    error_message: Optional[str] = None
    cookies: Dict[str, str] = None
    headers: Dict[str, str] = None


class PlaywrightAdaptor:
    """Playwright 动态渲染适配器

    用于处理需要 JavaScript 渲染的页面，如抖音、微博等动态加载内容
    基于 scrapling 框架的最佳实践优化
    """

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._playwright = None
        self._initialized = False

    def _get_proxy(self, config: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """获取代理配置，优先使用 config 中的 proxy，其次环境变量"""
        proxy_url = config.get("proxy")
        if not proxy_url:
            proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if proxy_url:
            return {"server": proxy_url}
        return None

    async def initialize(self) -> None:
        """初始化 Playwright"""
        if self._initialized:
            return

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                ]
            )
            self._initialized = True
            logger.info("playwright_initialized")
        except Exception as e:
            logger.error("playwright_init_failed", error=str(e))
            raise

    async def close(self) -> None:
        """关闭 Playwright"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._initialized = False
        logger.info("playwright_closed")

    async def render(
        self,
        url: str,
        config: Dict[str, Any],
        timeout: int = 30000,
        wait_for: Optional[str] = None,
        wait_state: str = "attached",
        network_idle: bool = True,
        extra_wait: int = 2000,
    ) -> RenderResult:
        """渲染页面

        Args:
            url: 目标URL
            config: 配置项，包含 headers, cookies, user_agent 等
            timeout: 超时时间（毫秒）
            wait_for: 等待特定元素出现的选择器
            wait_state: 等待状态 (attached/visible/hidden/detached)，默认 attached
            network_idle: 是否等待网络空闲，默认 True
            extra_wait: 页面加载后的额外等待时间（毫秒），默认 2000

        Returns:
            RenderResult: 渲染结果
        """
        if not self._initialized:
            await self.initialize()

        context = None
        page = None

        try:
            # 创建浏览器上下文
            context_options = {
                "user_agent": config.get("user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"),
                "viewport": {"width": 1920, "height": 1080},
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
            }

            # 添加自定义 headers
            if config.get("headers"):
                context_options["extra_http_headers"] = config["headers"]

            # 添加代理
            proxy = self._get_proxy(config)
            if proxy:
                context_options["proxy"] = proxy
                logger.debug("playwright_using_proxy", proxy=proxy["server"])

            context = await self._browser.new_context(**context_options)

            # 添加 cookies
            if config.get("cookies"):
                await context.add_cookies([
                    {"name": k, "value": v, "domain": self._extract_domain(url), "path": "/"}
                    for k, v in config["cookies"].items()
                ])

            page = await context.new_page()

            # 设置超时
            page.set_default_timeout(timeout)

            # 导航到页面 - 使用 domcontentloaded 而非 networkidle（更快）
            response = await page.goto(url, wait_until="domcontentloaded")

            status_code = response.status if response else 200

            if status_code >= 400:
                return RenderResult(
                    success=False,
                    status_code=status_code,
                    error_message=f"HTTP {status_code}"
                )

            # 等待网络空闲（动态内容加载）
            if network_idle:
                try:
                    await page.wait_for_load_state("networkidle", timeout=min(timeout, 10000))
                except Exception:
                    # 网络空闲超时不影响继续，只记录
                    logger.debug("network_idle_timeout", url=url)

            # 等待特定元素 - 使用 attached 状态（元素存在于 DOM 即可）
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, state=wait_state, timeout=min(timeout, 15000))
                except asyncio.TimeoutError as e:
                    # 检查元素是否实际存在
                    elements = await page.locator(wait_for).count()
                    if elements > 0:
                        logger.debug("wait_for_found_but_not_state",
                                    url=url, selector=wait_for, elements=elements, state=wait_state)
                        # 元素存在但状态不对，继续执行
                    else:
                        raise e
            else:
                # 默认等待页面稳定
                await page.wait_for_load_state("domcontentloaded")

            # 额外等待时间让动态内容完全加载
            if extra_wait > 0:
                await asyncio.sleep(extra_wait / 1000)

            # 获取渲染后的 HTML
            content = await page.content()

            # 获取 cookies
            cookies = {}
            for cookie in await context.cookies():
                cookies[cookie["name"]] = cookie["value"]

            logger.info("playwright_render_success",
                       url=url,
                       status_code=status_code,
                       content_length=len(content))

            return RenderResult(
                success=True,
                content=content,
                status_code=status_code,
                cookies=cookies
            )

        except asyncio.TimeoutError:
            logger.error("playwright_timeout", url=url)
            return RenderResult(
                success=False,
                error_message="Timeout waiting for page"
            )
        except Exception as e:
            logger.error("playwright_render_error", url=url, error=str(e))
            return RenderResult(
                success=False,
                error_message=str(e)
            )
        finally:
            if page:
                await page.close()
            if context:
                await context.close()

    async def execute_script(
        self,
        url: str,
        script: str,
        config: Dict[str, Any] = None,
    ) -> Any:
        """在页面中执行 JavaScript

        Args:
            url: 目标URL
            script: JavaScript 代码
            config: 配置项

        Returns:
            Any: JavaScript 执行结果
        """
        if not self._initialized:
            await self.initialize()

        context = None
        page = None

        try:
            context = await self._browser.new_context(
                user_agent=config.get("user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0")
            )
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle")
            result = await page.evaluate(script)

            return result

        finally:
            if page:
                await page.close()
            if context:
                await context.close()

    def _extract_domain(self, url: str) -> str:
        """从URL提取域名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc


# 全局实例
playwright_adaptor = PlaywrightAdaptor()