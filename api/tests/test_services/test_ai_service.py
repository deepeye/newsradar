"""Test AI service prompt building"""
import pytest
from app.services.ai_service import AIService


def test_build_recommendation_prompt():
    service = AIService(api_key="test-key")
    prompt = service._build_recommendation_prompt(
        domains=["财经", "民生"],
        style=["客观", "严谨"],
        clues_text="1. 全球气候峰会达成协议 (热度: 5892341)\n2. 房贷利率再下调 (热度: 4215678)",
    )
    assert "财经" in prompt
    assert "客观" in prompt
    assert "全球气候峰会" in prompt


def test_build_outline_prompt():
    service = AIService(api_key="test-key")
    prompt = service._build_outline_prompt(
        domains=["财经", "民生"],
        style=["客观", "严谨"],
        clues_text="线索内容...",
        additional_context="关注政策影响",
    )
    assert "财经" in prompt
    assert "关注政策影响" in prompt