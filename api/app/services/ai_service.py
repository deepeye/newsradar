"""AI service — Alibaba Cloud Bailian (Qwen) integration"""
import json
import hashlib
from typing import Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import (
    AIServiceError,
    AIServiceTimeoutError,
    AIServiceRateLimitError,
    AIServiceContentError,
)
from app.utils.cache import cache_manager

logger = structlog.get_logger("ai_service")


class AIService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.model = model or settings.QWEN_MODEL
        self.base_url = settings.QWEN_BASE_URL
        self.timeout = settings.QWEN_TIMEOUT

    # --- Public methods ---

    async def generate_topic_recommendations(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        limit: int = 5,
    ) -> list[dict]:
        cache_key = self._cache_key("recommendations", domains, style, clues_text[:200])
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        prompt = self._build_recommendation_prompt(domains, style, clues_text)
        response = await self._call_qwen(prompt)
        result = self._parse_json_list(response, limit)

        await cache_manager.set(cache_key, result, ttl=settings.AI_CACHE_TTL)
        return result

    async def generate_outline(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        additional_context: Optional[str] = None,
    ) -> dict:
        prompt = self._build_outline_prompt(domains, style, clues_text, additional_context)
        response = await self._call_qwen(prompt)
        return self._parse_json_dict(response)

    async def generate_headlines(
        self,
        outline_text: str,
        styles: list[str] | None = None,
    ) -> list[dict]:
        styles = styles or ["硬核新闻风", "叙事分析风", "深度解读风"]
        prompt = self._build_headlines_prompt(outline_text, styles)
        response = await self._call_qwen(prompt)
        return self._parse_json_list(response, 3)

    async def generate_writing_suggestions(
        self,
        title: str,
        content: str,
    ) -> list[dict]:
        prompt = self._build_writing_suggestions_prompt(title, content)
        response = await self._call_qwen(prompt)
        return self._parse_json_list(response, 5)

    async def analyze_content_metrics(
        self,
        content: str,
    ) -> dict:
        prompt = self._build_metrics_prompt(content)
        response = await self._call_qwen(prompt)
        return self._parse_json_dict(response)

    # --- Prompt builders ---

    def _build_recommendation_prompt(
        self, domains: list[str], style: list[str], clues_text: str
    ) -> str:
        return f"""你是一位资深媒体选题顾问。请根据以下信息，推荐 5 个值得深入报道的选题。

## 组织定位
- 关注领域：{', '.join(domains)}
- 报道风格：{', '.join(style)}

## 最新线索数据
{clues_text}

## 输出要求
以 JSON 数组格式输出，每个元素包含：
- source: 来源平台
- source_icon: 图标类型(newspaper/flame/trending-up)
- tag: 分类标签
- title: 选题标题（简洁有力）
- reason: 推荐理由
- angles: 切入角度数组（2-3个）

请直接输出 JSON 数组，不要包含其他文字。"""

    def _build_outline_prompt(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        additional_context: Optional[str] = None,
    ) -> str:
        context_section = f"\n## 补充说明\n{additional_context}" if additional_context else ""
        return f"""你是一位资深媒体选题策划师。请根据以下线索，生成完整的选题大纲。

## 组织定位
- 关注领域：{', '.join(domains)}
- 报道风格：{', '.join(style)}
{context_section}

## 线索详情
{clues_text}

## 输出要求
以 JSON 对象格式输出，包含以下字段：
- title: 选题标题（简洁有力，20字内）
- summary: 概要描述（100字内）
- urgency: 紧急程度（高/中/低）
- info_density: 信息密度评分（0-100整数）
- headlines: 标题建议数组，每个元素包含 style 和 text
- lead_paragraph: 导语段落（200字内）
- outline_sections: 大纲结构数组，每个元素包含 id, number, title, items(数组，每个含 id, content, has_ai_rewrite)
- interview_directions: 采访方向数组，每个含 id, role, description
- references: 参考资料数组，每个含 id, title, source, url

请直接输出 JSON 对象，不要包含其他文字。"""

    def _build_headlines_prompt(self, outline_text: str, styles: list[str]) -> str:
        styles_str = "、".join(styles)
        return f"""请为以下选题内容生成 3 个不同风格的标题建议。

## 选题内容
{outline_text}

## 需要的风格
{styles_str}

以 JSON 数组输出，每个元素包含 style 和 text。直接输出 JSON。"""

    def _build_writing_suggestions_prompt(self, title: str, content: str) -> str:
        return f"""你是一位资深新闻编辑。请阅读以下文章，提供写作改进建议。

## 文章标题
{title}

## 文章内容
{content}

以 JSON 数组输出，每个元素包含：
- type: 类型(grammar/style/fact)
- original: 原文片段
- suggested: 建议修改
- reason: 理由

最多提供 5 条建议。直接输出 JSON。"""

    def _build_metrics_prompt(self, content: str) -> str:
        return f"""请分析以下新闻文章的客观性和可读性。

## 文章内容
{content}

以 JSON 对象输出：
- objectivity: 客观性评分（0-100整数）
- readability: 可读性等级（如 A1, A2, B1, B2, C1, C2）

直接输出 JSON。"""

    # --- API call ---

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=5, max=30),
        reraise=True,
    )
    async def _call_qwen(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # OpenAI compatible endpoint requires /chat/completions path
                api_url = f"{self.base_url.rstrip('/')}/chat/completions"
                response = await client.post(
                    api_url, headers=headers, json=payload
                )

                if response.status_code == 429:
                    raise AIServiceRateLimitError("Qwen API rate limit exceeded")
                if response.status_code == 400:
                    raise AIServiceContentError(f"Content error: {response.text}")

                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            raise AIServiceTimeoutError("Qwen API timeout")
        except httpx.HTTPStatusError as e:
            raise AIServiceError(f"Qwen API error: {e}")
        except (AIServiceRateLimitError, AIServiceTimeoutError, AIServiceContentError):
            raise
        except Exception as e:
            raise AIServiceError(f"Unexpected error: {e}")

    # --- Helpers ---

    def _parse_json_list(self, text: str, limit: int = 10) -> list[dict]:
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result[:limit]
            if isinstance(result, dict) and "items" in result:
                return result["items"][:limit]
            return [result][:limit]
        except json.JSONDecodeError:
            logger.error("ai_json_parse_error", text=text[:200])
            return []

    def _parse_json_dict(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error("ai_json_parse_error", text=text[:200])
            return {}

    def _cache_key(self, prefix: str, *args) -> str:
        content = ":".join(str(a) for a in args)
        hash_val = hashlib.md5(content.encode()).hexdigest()
        return f"ai:{prefix}:{hash_val}"