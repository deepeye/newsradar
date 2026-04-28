"""UA轮换器"""
import random
from typing import List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class UARotator:
    """UA轮换器"""

    # 桌面端UA池
    DESKTOP_UAS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    # 移动端UA池
    MOBILE_UAS = [
        # iOS Safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        # Android Chrome
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
        # Android Firefox
        "Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
        # 微信内置浏览器
        "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/TP1A.220905.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.45.2520",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1 MicroMessenger/8.0.45(0x1f2f3287)",
    ]

    # 平台UA映射
    PLATFORM_UA_MAP = {
        "weibo": "mobile",      # 微博用移动端
        "zhihu": "mobile",      # 知乎用移动端
        "douyin": "mobile",     # 抖音用移动端
        "bilibili": "desktop",  # B站用桌面端
        "toutiao": "mobile",    # 今日头条用移动端
        "baidu": "desktop",     # 百度用桌面端
        "wechat": "mobile",     # 微信用移动端
        "xiaohongshu": "mobile", # 小红书用移动端
    }

    def __init__(self):
        self._last_ua = None

    def get_ua(self, platform: Optional[str] = None, device_type: Optional[str] = None) -> str:
        """获取UA"""
        # 根据平台或设备类型选择池
        if device_type:
            pool_type = device_type.lower()
        elif platform and platform.lower() in self.PLATFORM_UA_MAP:
            pool_type = self.PLATFORM_UA_MAP[platform.lower()]
        else:
            pool_type = random.choice(["desktop", "mobile"])

        pool = self.DESKTOP_UAS if pool_type == "desktop" else self.MOBILE_UAS

        # 随机选择，避免连续使用相同UA
        ua = random.choice(pool)
        while ua == self._last_ua and len(pool) > 1:
            ua = random.choice(pool)

        self._last_ua = ua
        logger.debug("ua_selected", ua=ua[:50], pool_type=pool_type)
        return ua

    def get_ua_with_headers(self, platform: Optional[str] = None) -> dict:
        """获取带UA的请求头"""
        ua = self.get_ua(platform)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def get_mobile_ua(self) -> str:
        """获取移动端UA"""
        return self.get_ua(device_type="mobile")

    def get_desktop_ua(self) -> str:
        """获取桌面端UA"""
        return self.get_ua(device_type="desktop")


# 全局实例
ua_rotator = UARotator()