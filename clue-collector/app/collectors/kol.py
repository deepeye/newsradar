"""KOL采集器 - 支持微博和X平台"""
import re
import json
from typing import Dict, Any, List, Optional

from app.collectors.base import BaseCollector, ClueData, CollectResult
from app.anti_crawl import AntiCrawlModule
from app.collectors.adaptors.playwright_adaptor import playwright_adaptor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KOLCollector(BaseCollector):
    """KOL采集器 - 通过API或Playwright采集KOL发帖和互动数据"""

    def __init__(self):
        super().__init__("kol", "1.0.0")

    async def validate(self, config: Dict[str, Any]) -> bool:
        required = ["platform", "platform_id"]
        return all(k in config for k in required) and config["platform"] in ("weibo", "x")

    async def collect(
        self,
        config: Dict[str, Any],
        anti_crawl: AntiCrawlModule,
        source_id: str = None,
    ) -> CollectResult:
        platform = config.get("platform")
        if platform == "weibo":
            return await self._collect_weibo(config, anti_crawl, source_id)
        elif platform == "x":
            return await self._collect_x(config, anti_crawl, source_id)
        return CollectResult(success=False, error_message=f"Unsupported platform: {platform}")

    async def _collect_weibo(
        self, config: Dict[str, Any], anti_crawl: AntiCrawlModule, source_id: str
    ) -> CollectResult:
        """微博KOL采集 - 使用桌面端API"""
        uid = config["platform_id"]
        screen_name = config.get("screen_name", "")
        context = await anti_crawl.get_context(source_id, platform="weibo")

        try:
            from scrapling import Fetcher

            fetcher = Fetcher(retries=2, timeout=30)
            url = f"https://weibo.com/ajax/statuses/mymblog?uid={uid}&page=1&feature=0"

            headers = {
                "User-Agent": context.headers.get("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"),
                "Referer": f"https://weibo.com/u/{uid}",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/plain, */*",
            }
            if config.get("headers"):
                headers.update(config["headers"])

            cookies = context.cookies or {}
            xsrf_token = cookies.get("XSRF-TOKEN") or cookies.get("xsrf-token")
            if xsrf_token:
                headers["X-XSRF-TOKEN"] = xsrf_token

            response = fetcher.get(url, headers=headers, cookies=cookies)
            status_code = getattr(response, "status_code", getattr(response, "status", 200))

            if status_code in (401, 403, 432):
                await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy, status_code=status_code)
                return CollectResult(success=False, error_message=f"Weibo auth failed: HTTP {status_code}")

            if status_code >= 400:
                await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy, status_code=status_code)
                return CollectResult(success=False, error_message=f"HTTP {status_code}")

            data = response.json()
            weibo_list = data.get("data", {}).get("list", [])
            logger.info("weibo_api_response", ok=data.get("ok"), list_count=len(weibo_list), uid=uid)

            if data.get("ok") != 1:
                await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy)
                return CollectResult(success=False, error_message=f"Weibo API error: ok={data.get('ok')}")

            await anti_crawl.report_success(source_id, cookie_id=context.cookie_id, proxy=context.proxy)

            items = self._parse_weibo_desktop_posts(weibo_list, screen_name, uid)
            return CollectResult(
                success=True,
                items=items,
                metadata={"platform": "weibo", "uid": uid, "items_count": len(items)},
            )

        except Exception as e:
            await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy)
            return CollectResult(success=False, error_message=str(e))

    def _parse_weibo_desktop_posts(self, weibo_list: list, screen_name: str, uid: str = "") -> List[ClueData]:
        """解析微博桌面端API返回的帖子列表"""
        items = []
        for post in weibo_list:
            try:
                raw_text = post.get("text", "")
                title = self._strip_html_tags(raw_text)
                if not title:
                    continue

                mid = post.get("mid", post.get("id", ""))
                url = f"https://weibo.com/{uid}/{mid}" if mid else None
                mblogid = post.get("mblogid", "")
                if mblogid:
                    url = f"https://weibo.com/detail/{mblogid}"

                user = post.get("user", {})
                author = user.get("screen_name", screen_name)

                pics = post.get("pic_ids", [])
                pic_num = post.get("pic_num", 0)
                cover_image = None
                if pics:
                    cover_image = f"https://wx1.sinaimg.cn/orj480/{pics[0]}"

                tags = [t.get("topic", "") for t in post.get("topic_struct", []) if t.get("topic")]
                tags.extend(re.findall(r'#([^#]+)#', raw_text))

                item = ClueData(
                    title=title[:500],
                    url=url,
                    cover_image=cover_image,
                    author=author,
                    likes=post.get("attitudes_count", 0) or 0,
                    comments=post.get("comments_count", 0) or 0,
                    shares=post.get("reposts_count", 0) or 0,
                    original_content=raw_text,
                    tags=tags,
                )
                items.append(item)
            except Exception as e:
                logger.debug("weibo_desktop_parse_error", error=str(e))
                continue
        return items

    def _parse_weibo_posts(self, data: dict, screen_name: str) -> List[ClueData]:
        """解析微博API返回的帖子"""
        items = []
        cards = data.get("data", {}).get("cards", [])
        logger.info("weibo_cards_debug", total_cards=len(cards), card_types=[c.get("card_type") for c in cards[:5]])

        for card in cards:
            # 类型9/11通常是微博帖子卡片
            if card.get("card_type") not in (9, 11):
                # 也可能在 card_group 中
                card_group = card.get("card_group", [])
                for group_item in card_group:
                    if group_item.get("card_type") in (9, 11):
                        mblog = group_item.get("mblog")
                        if mblog:
                            item = self._extract_mblog(mblog, screen_name)
                            if item:
                                items.append(item)
                continue

            mblog = card.get("mblog")
            if mblog:
                item = self._extract_mblog(mblog, screen_name)
                if item:
                    items.append(item)

        return items

    def _extract_mblog(self, mblog: dict, screen_name: str) -> Optional[ClueData]:
        """从mblog提取ClueData"""
        try:
            raw_text = mblog.get("text", "")
            title = self._strip_html_tags(raw_text)
            if not title:
                return None

            mid = mblog.get("mid", mblog.get("id", ""))
            url = f"https://m.weibo.cn/detail/{mid}" if mid else None

            user = mblog.get("user", {})
            author = user.get("screen_name", screen_name)

            pics = mblog.get("pics", [])
            cover_image = pics[0].get("url") if pics else None

            tags = re.findall(r'#([^#]+)#', raw_text)

            return ClueData(
                title=title[:500],
                url=url,
                cover_image=cover_image,
                author=author,
                likes=mblog.get("attitudes_count", 0) or 0,
                comments=mblog.get("comments_count", 0) or 0,
                shares=mblog.get("reposts_count", 0) or 0,
                original_content=raw_text,
                tags=tags,
            )
        except Exception as e:
            logger.debug("weibo_parse_error", error=str(e))
            return None

    async def _collect_x(
        self, config: Dict[str, Any], anti_crawl: AntiCrawlModule, source_id: str
    ) -> CollectResult:
        """X(Twitter) KOL采集 - 使用Playwright渲染"""
        username = config["platform_id"]
        screen_name = config.get("screen_name", "")
        context = await anti_crawl.get_context(source_id, platform="x")

        try:
            # 无有效 Cookie 时不传递 headers，避免触发 X 反爬
            has_cookies = bool(context.cookies)
            render_config = {
                "headers": context.headers or {} if has_cookies else {},
                "cookies": context.cookies or {},
                "user_agent": context.headers.get("User-Agent") if has_cookies and context.headers else None,
            }
            render_result = await playwright_adaptor.render(
                url=f"https://x.com/{username}",
                config=render_config,
                timeout=120000,
                wait_for=None,
                network_idle=False,
                extra_wait=8000,
            )

            if not render_result.success:
                await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy)
                return CollectResult(success=False, error_message=render_result.error_message or "Playwright render failed")

            # 检查是否跳转到登录页
            if "/login" in (render_result.content or "") and 'input[name="text"]' in (render_result.content or ""):
                await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy, status_code=401)
                return CollectResult(success=False, error_message="X requires login - cookie may be expired")

            await anti_crawl.report_success(source_id, cookie_id=context.cookie_id, proxy=context.proxy)

            from scrapling import Selector
            doc = Selector(render_result.content)
            tweets = doc.css('[data-testid="tweet"]')
            logger.info("x_page_debug", content_length=len(render_result.content or ""), tweet_elements=len(tweets), has_login="/login" in (render_result.content or ""))
            items = self._parse_x_tweets(doc, screen_name, username)

            return CollectResult(
                success=True,
                items=items,
                metadata={"platform": "x", "username": username, "items_count": len(items)},
            )

        except Exception as e:
            await anti_crawl.report_failure(source_id, cookie_id=context.cookie_id, proxy=context.proxy)
            return CollectResult(success=False, error_message=str(e))

    def _parse_x_tweets(self, doc, screen_name: str, username: str) -> List[ClueData]:
        """解析X页面推文"""
        items = []
        tweets = doc.css('[data-testid="tweet"]')

        for tweet in tweets:
            try:
                # 推文文本
                text_el = tweet.css('[data-testid="tweetText"]')
                if not text_el or not text_el.first:
                    continue
                title = text_el.first.get_all_text(strip=True) if hasattr(text_el.first, "get_all_text") else (text_el.first.text.strip() if text_el.first.text else "")
                if not title:
                    continue

                # 推文链接 - 从time元素获取
                link = None
                time_el = tweet.css("time")
                if time_el and time_el.first:
                    parent_a = time_el.first.parent
                    if parent_a and parent_a.tag == "a":
                        href = parent_a.attrib.get("href", "")
                        if href:
                            link = f"https://x.com{href}" if href.startswith("/") else href

                # 作者
                user_el = tweet.css('[data-testid="User-Name"]')
                author = screen_name
                if user_el and user_el.first:
                    author_text = user_el.first.get_all_text(strip=True) if hasattr(user_el.first, "get_all_text") else (user_el.first.text.strip() if user_el.first.text else "")
                    if author_text:
                        # 取@之前的部分作为显示名
                        author = author_text.split("@")[0].strip() or screen_name

                # 互动数据
                likes = self._parse_x_count(tweet, "like")
                shares = self._parse_x_count(tweet, "retweet")
                comments = self._parse_x_count(tweet, "reply")

                # 图片
                cover_image = None
                photo_el = tweet.css('[data-testid="tweetPhoto"] img')
                if photo_el and photo_el.first:
                    cover_image = photo_el.first.attrib.get("src")

                # 话题标签
                tags = re.findall(r'#(\w+)', title)

                clue = ClueData(
                    title=title[:500],
                    url=link,
                    cover_image=cover_image,
                    author=author,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    original_content=title,
                    tags=tags,
                )
                items.append(clue)
            except Exception as e:
                logger.debug("x_parse_error", error=str(e))
                continue

        return items

    def _parse_x_count(self, tweet_element, action: str) -> int:
        """解析X互动计数"""
        try:
            el = tweet_element.css(f'[data-testid="{action}"] span')
            if el and el.first:
                text = el.first.get_all_text(strip=True) if hasattr(el.first, "get_all_text") else (el.first.text.strip() if el.first.text else "")
                if not text:
                    return 0
                # 处理 K, M 等缩写
                text = text.replace(",", "")
                if text.upper().endswith("K"):
                    return int(float(text[:-1]) * 1000)
                elif text.upper().endswith("M"):
                    return int(float(text[:-1]) * 1000000)
                return int(text)
        except (ValueError, TypeError):
            pass
        return 0

    @staticmethod
    def _strip_html_tags(html: str) -> str:
        """去除HTML标签"""
        clean = re.sub(r"<[^>]+>", "", html)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean
