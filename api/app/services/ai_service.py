"""AI service — Alibaba Cloud Bailian (Qwen) integration"""
import json
import hashlib
from typing import Optional, AsyncGenerator

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

    async def generate_single_recommendation(
        self,
        domains: list[str],
        style: list[str],
        clue_text: str,
        clue_id: str,
    ) -> dict:
        """Generate one topic recommendation for a single clue."""
        cache_key = self._cache_key("single_rec", domains, style, clue_id)
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        prompt = self._build_single_recommendation_prompt(domains, style, clue_text)
        response = await self._call_qwen(prompt)
        result = self._parse_json_dict(response)

        if not result:
            # LLM returned invalid JSON — return minimal fallback
            result = {"title": "", "reason": "", "angles": [], "source": "", "source_icon": "newspaper", "tag": ""}

        await cache_manager.set(cache_key, result, ttl=settings.AI_CACHE_TTL)
        return result

    async def generate_topic_recommendations(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        limit: int = 5,
        clue_ids: list[str] | None = None,
    ) -> list[dict]:
        # Use clue_ids hash for stable cache key — avoids re-calling LLM when new clues arrive
        # but old clue set is unchanged
        ids_hash = hashlib.md5(":".join(clue_ids or []).encode()).hexdigest() if clue_ids else hashlib.md5(clues_text[:200].encode()).hexdigest()
        cache_key = self._cache_key("recommendations", domains, style, ids_hash)
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

    async def continue_writing(
        self,
        title: str,
        content: str,
        outline_sections: list[dict],
    ) -> dict:
        prompt = self._build_continue_writing_prompt(title, content, outline_sections)
        response = await self._call_qwen(prompt)
        return self._parse_json_dict(response)

    async def generate_initial_draft(
        self,
        title: str,
        style: list[str],
        lead_paragraph: str,
        outline_sections: list[dict],
        outline_id: str,
    ) -> dict:
        """Generate a full initial draft based on outline structure."""
        cache_key = self._cache_key("initial_draft", title, outline_id)
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        prompt = self._build_initial_draft_prompt(title, style, lead_paragraph, outline_sections)
        response = await self._call_qwen(prompt)
        result = self._parse_json_dict(response)

        if not result or not result.get("content"):
            result = {"content": ""}

        await cache_manager.set(cache_key, result, ttl=settings.AI_CACHE_TTL)
        return result

    async def generate_initial_draft_stream(
        self,
        title: str,
        style: list[str],
        lead_paragraph: str,
        outline_sections: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Stream initial draft content chunk by chunk."""
        prompt = self._build_initial_draft_stream_prompt(title, style, lead_paragraph, outline_sections)
        async for chunk in self._call_qwen_stream(prompt):
            yield chunk

    async def translate(self, content: str, target_language: str) -> dict:
        prompt = self._build_translate_prompt(content, target_language)
        response = await self._call_qwen(prompt)
        return self._parse_json_dict(response)

    async def extract_claims(self, title: str, content: str) -> list[dict]:
        """Phase 1: Extract factual claims from article."""
        prompt = self._build_claim_extraction_prompt(title, content)
        response = await self._call_qwen(prompt)
        return self._parse_json_list(response, 10)

    async def synthesize_fact_check(
        self, claims: list[dict], search_results: list[dict]
    ) -> list[dict]:
        """Phase 3: Compare search results against claims."""
        prompt = self._build_fact_check_synthesis_prompt(claims, search_results)
        response = await self._call_qwen(prompt)
        return self._parse_json_list(response, 10)

    # --- Prompt builders ---

    def _build_initial_draft_prompt(
        self,
        title: str,
        style: list[str],
        lead_paragraph: str,
        outline_sections: list[dict],
    ) -> str:
        sections_text = "\n".join(
            f"{s.get('number', i+1)}. {s.get('title', '')} — {', '.join(item.get('content', '') for item in s.get('items', []))}"
            for i, s in enumerate(outline_sections)
        )
        return f"""你是一位资深新闻撰稿人。请根据以下选题大纲，撰写一篇完整的新闻初稿。

## 选题标题
{title}

## 报道风格
{', '.join(style)}

## 导语
{lead_paragraph}

## 大纲结构
{sections_text}

## 输出要求
以 JSON 对象输出：
- content: 完整初稿文本（Markdown格式，每个大纲章节用 ## 标题分隔，总字数1000-2000字）

请严格按照大纲结构顺序撰写，每个章节内容充实、风格统一。导语已提供，从第一个大纲章节开始撰写正文。直接输出 JSON。"""

    def _build_initial_draft_stream_prompt(
        self,
        title: str,
        style: list[str],
        lead_paragraph: str,
        outline_sections: list[dict],
    ) -> str:
        sections_text = "\n".join(
            f"{s.get('number', i+1)}. {s.get('title', '')} — {', '.join(item.get('content', '') for item in s.get('items', []))}"
            for i, s in enumerate(outline_sections)
        )
        return f"""你是一位资深新闻撰稿人。请根据以下选题大纲，撰写一篇完整的新闻初稿。

## 选题标题
{title}

## 报道风格
{', '.join(style)}

## 导语
{lead_paragraph}

## 大纲结构
{sections_text}

请严格按照大纲结构顺序撰写，每个章节用 ## 标题分隔。总字数1000-2000字，风格统一，内容充实。直接输出 Markdown 正文，不要输出 JSON 或其他格式。"""

    def _build_single_recommendation_prompt(
        self, domains: list[str], style: list[str], clue_text: str
    ) -> str:
        return f"""你是一位资深媒体选题顾问。请根据以下单条线索，推荐 1 个值得深入报道的选题。

## 组织定位
- 关注领域：{', '.join(domains)}
- 报道风格：{', '.join(style)}

## 线索信息
{clue_text}

## 输出要求
以 JSON 对象格式输出，包含：
- source: 来源平台
- source_icon: 图标类型(newspaper/flame/trending-up)
- tag: 分类标签
- title: 选题标题（简洁有力，20字内）
- reason: 推荐理由（需说明为何值得深入、传播潜力如何）
- angles: 切入角度数组（2-3个，需体现不同视角）

直接输出 JSON 对象，不要包含其他文字。"""

    def _build_recommendation_prompt(
        self, domains: list[str], style: list[str], clues_text: str
    ) -> str:
        return f"""你是一位资深媒体选题顾问。请根据以下信息，推荐 5 个值得深入报道的选题。

## 组织定位
- 关注领域：{', '.join(domains)}
- 报道风格：{', '.join(style)}

## 最新线索数据（含来源类型、热度、互动数据、优先级）
{clues_text}

## 输出要求
以 JSON 数组格式输出，每个元素包含：
- source: 来源平台
- source_icon: 图标类型(newspaper/flame/trending-up)
- tag: 分类标签
- title: 选题标题（简洁有力）
- reason: 推荐理由（需说明为何值得深入、传播潜力如何）
- angles: 切入角度数组（2-3个，需体现不同视角）

请在不同平台和来源类型间均衡推荐，避免全部集中在一个来源。直接输出 JSON 数组，不要包含其他文字。"""

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

    def _build_continue_writing_prompt(
        self, title: str, content: str, outline_sections: list[dict]
    ) -> str:
        sections_text = "\n".join(
            f"{s.get('number', i+1)}. {s.get('title', '')}"
            for i, s in enumerate(outline_sections)
        )
        return f"""你是一位资深新闻撰稿人。请根据以下信息，续写文章的下一个章节。

## 文章标题
{title}

## 已有内容
{content}

## 大纲结构
{sections_text}

## 输出要求
请根据大纲结构，选择下一个未写到的章节，续写 300-500 字的内容。
续写内容需与已有内容的风格、叙事方向保持一致。

以 JSON 对象输出：
- section_title: 章节标题
- continued_content: 续写正文（纯文本，不含标题）

直接输出 JSON。"""

    def _build_translate_prompt(self, content: str, target_language: str) -> str:
        language_names = {
            "en": "英文",
            "zh-TW": "中文繁体",
            "ru": "俄语",
            "ja": "日语",
            "ko": "韩语",
            "es": "西班牙语",
            "de": "德语",
        }
        lang_label = language_names.get(target_language, target_language)
        return f"""你是一位专业的新闻翻译专家。请将以下文章翻译为{lang_label}。

## 原文内容
{content}

## 输出要求
以 JSON 对象输出：
- translated_content: 翻译后的完整文章内容
- target_language: 目标语言代码

翻译要求：
1. 保持原文的新闻风格和叙事结构
2. 准确传达原文信息，不遗漏关键内容
3. 目标语言表达自然流畅，符合当地读者习惯
4. 专业术语和地名采用目标语言的通用译法

直接输出 JSON。"""

    def _build_claim_extraction_prompt(self, title: str, content: str) -> str:
        return f"""你是一位专业新闻事实核查分析师。请从以下文章中提取所有可验证的事实性声明。

## 文章标题
{title}

## 文章内容
{content}

以 JSON 数组输出，每个元素包含：
- claim: 声明原文（精确引用）
- type: 声明类型（date/statistic/person/event/quote/location）
- confidence: 可信度（high/medium/low）— high 表示常识或广泛认可的事实，low 表示需要交叉验证的具体数据
- search_query: 用于Google搜索验证的查询词（英文，简洁精确）

请提取所有涉及具体日期、数字、人物、事件、引用的事实声明。直接输出 JSON 数组。"""

    def _build_fact_check_synthesis_prompt(
        self, claims: list[dict], search_results: list[dict]
    ) -> str:
        claims_text = "\n".join(
            f"- [{c.get('type','')}/{c.get('confidence','')}] {c.get('claim','')} (搜索词: {c.get('search_query','')})"
            for c in claims
        )
        evidence_text = "\n".join(
            f"- [{r.get('source','')}] {r.get('title','')} | {r.get('snippet','')}"
            for r in search_results
        )
        return f"""你是一位专业新闻事实核查分析师。请根据搜索结果，对以下声明逐一进行验证判断。

## 待验证声明
{claims_text}

## 搜索到的相关新闻
{evidence_text}

以 JSON 数组输出，每个元素包含：
- claim: 声明原文
- type: 声明类型
- confidence: 原始可信度
- status: 验证结果（verified/unverified/contradicted）
- evidence: 支撑证据摘要（引用搜索结果中的具体信息）
- source_urls: 证据来源URL数组

验证标准：
- verified: 搜索结果明确支持该声明
- contradicted: 搜索结果明确反驳该声明
- unverified: 搜索结果无法确认或反驳

直接输出 JSON 数组。"""

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
            "X-DashScope-DataInspection": '{"input": "disable", "output": "disable"}',
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

    async def _call_qwen_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream Qwen response chunk by chunk via SSE."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-DataInspection": '{"input": "disable", "output": "disable"}',
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        api_url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", api_url, headers=headers, json=payload) as response:
                    if response.status_code == 429:
                        raise AIServiceRateLimitError("Qwen API rate limit exceeded")
                    if response.status_code == 400:
                        raise AIServiceContentError(f"Content error")
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            raise AIServiceTimeoutError("Qwen API stream timeout")
        except (AIServiceRateLimitError, AIServiceTimeoutError, AIServiceContentError):
            raise
        except Exception as e:
            raise AIServiceError(f"Stream error: {e}")

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