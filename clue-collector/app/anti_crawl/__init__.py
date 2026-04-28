"""反爬模块初始化"""
from app.anti_crawl.manager import AntiCrawlModule, anti_crawl, RequestContext
from app.anti_crawl.ip_pool import IPPool, ip_pool, ProxyInfo
from app.anti_crawl.cookie_pool import CookiePool, cookie_pool
from app.anti_crawl.rate_limiter import RateLimiter, rate_limiter, FrequencyState
from app.anti_crawl.ua_rotator import UARotator, ua_rotator

__all__ = [
    'AntiCrawlModule',
    'anti_crawl',
    'RequestContext',
    'IPPool',
    'ip_pool',
    'ProxyInfo',
    'CookiePool',
    'cookie_pool',
    'RateLimiter',
    'rate_limiter',
    'FrequencyState',
    'UARotator',
    'ua_rotator',
]