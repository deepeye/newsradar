"""On-demand search API server for clue-collector"""
from urllib.parse import urlencode, quote_plus

from fastapi import FastAPI
from pydantic import BaseModel

import structlog

from app.collectors.configurable import ConfigurableCollector
from app.anti_crawl import anti_crawl

logger = structlog.get_logger()

app = FastAPI(title="clue-collector-ondemand")

collector = ConfigurableCollector()


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResultItem(BaseModel):
    title: str
    snippet: str
    source: str
    url: str


class SearchResponse(BaseModel):
    success: bool
    results: list[SearchResultItem]
    error: str = ""


# Google News search config template
GOOGLE_NEWS_CONFIG = {
    "parse_type": "css",
    "use_playwright": True,
    "parse_rules": {
        "container": "div.SoaBEf, div.Gx5Zad",
        "title": "a.Wly4e, div.nDgi9d a",
        "link": "a.Wly4e@href, div.nDgi9d a@href",
        "snippet": "div.GI74Re",
        "author": "div.mCBkyc, span.mCBkyc",
    },
    "timeout": 30000,
    "wait_for_selector": "div.SoaBEf, div.Gx5Zad",
    "network_idle": True,
    "extra_wait": 3000,
}


@app.post("/api/search/google-news", response_model=SearchResponse)
async def search_google_news(req: SearchRequest):
    """Search Google News for a query and return parsed results."""
    encoded_query = quote_plus(req.query)
    url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&hl=zh-CN"

    config = {**GOOGLE_NEWS_CONFIG, "url": url}

    try:
        result = await collector.collect(config, anti_crawl, source_id="google-news")

        if not result.success:
            return SearchResponse(
                success=False, results=[], error=result.error_message or "Search failed"
            )

        items = result.items[:req.max_results]
        search_results = [
            SearchResultItem(
                title=item.title or "",
                snippet=item.original_content or "",
                source=item.author or "",
                url=item.url or "",
            )
            for item in items
            if item.title
        ]

        return SearchResponse(success=True, results=search_results)

    except Exception as e:
        logger.error("google_news_search_failed", query=req.query, error=str(e))
        return SearchResponse(success=False, results=[], error=str(e))