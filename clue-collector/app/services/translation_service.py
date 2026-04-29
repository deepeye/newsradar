"""Translation service using Qwen model"""
import os
import httpx
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TranslationService:
    """Translation service for non-Chinese content"""

    def __init__(self):
        self.enabled = settings.translation.enabled
        # Read from environment variables (docker-compose passes QWEN_API_KEY directly)
        self.api_key = os.getenv("QWEN_API_KEY", settings.translation.api_key)
        self.api_base = os.getenv("QWEN_API_BASE", settings.translation.api_base)
        self.model = settings.translation.model
        self.thinking_enabled = settings.translation.thinking_enabled
        self.max_length = settings.translation.max_length
        self.timeout = settings.translation.timeout

    async def translate(self, text: str, target_lang: str = "zh") -> Optional[str]:
        """
        Translate text to target language

        Args:
            text: Original text to translate
            target_lang: Target language (default: zh for Chinese)

        Returns:
            Translated text or None if translation fails
        """
        if not self.enabled or not self.api_key:
            logger.warning("Translation disabled or API key not configured")
            return None

        if not text or len(text) > self.max_length:
            logger.warning(f"Text too long or empty: {len(text) if text else 0} chars")
            return None

        # Check if text is already Chinese
        if self._is_chinese(text):
            logger.debug("Text is already Chinese, skip translation")
            return None

        try:
            # Build request body
            request_body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate the following text to Chinese. Keep the original meaning and style. Only output the translated text, no explanations."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.3,
            }

            # Enable thinking mode if configured
            if self.thinking_enabled:
                request_body["enable_thinking"] = True
                logger.debug("Translation with thinking mode enabled")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_body
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # Extract thinking content if present (wrapped in <think> tags)
                    if self.thinking_enabled and "<think>" in content:
                        # Extract actual translation after thinking section
                        import re
                        match = re.search(r'</think>\s*(.+)', content, re.DOTALL)
                        if match:
                            translated = match.group(1).strip()
                        else:
                            translated = content.replace("<think>", "").replace("</think>", "").strip()
                    else:
                        translated = content.strip()

                    logger.info(f"Translated {len(text)} chars to {len(translated)} chars")
                    return translated
                else:
                    logger.error(f"Translation API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return None

    def _is_chinese(self, text: str) -> bool:
        """Check if text is predominantly Chinese"""
        chinese_chars = sum(1 for char in text if '一' <= char <= '鿿')
        total_chars = len(text.strip())

        if total_chars == 0:
            return False

        # If more than 60% Chinese characters, consider it Chinese
        return chinese_chars / total_chars > 0.6


# Global instance
translation_service = TranslationService()