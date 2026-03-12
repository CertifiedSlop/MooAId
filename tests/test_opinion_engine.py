"""Tests for MooAId opinion engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mooaid.core.opinion_engine import OpinionEngine, OpinionResult
from mooaid.core import GenerationResult, AIProvider
from mooaid.profile import ProfileData
from mooaid.config import Config


class MockProvider(AIProvider):
    """Mock AI provider for testing."""

    name = "mock"

    def __init__(self, response: str = "") -> None:
        self.response = response
        self.config = MagicMock()

    async def generate(self, prompt: str) -> GenerationResult:
        return GenerationResult(
            content=self.response,
            model="test-model",
            provider=self.name,
        )

    async def check_health(self) -> bool:
        return True


class TestOpinionResult:
    """Tests for OpinionResult dataclass."""

    def test_opinion_result_creation(self):
        """Test creating an OpinionResult."""
        result = OpinionResult(
            predicted_opinion="Test opinion",
            reasoning="Test reasoning",
            model="test-model",
            provider="test-provider",
            profile_used="default",
        )
        assert result.predicted_opinion == "Test opinion"
        assert result.reasoning == "Test reasoning"
        assert result.model == "test-model"
        assert result.provider == "test-provider"
        assert result.profile_used == "default"


class TestOpinionEngine:
    """Tests for OpinionEngine."""

    def test_build_prompt(self):
        """Test building prompt from profile and question."""
        provider = MockProvider()
        engine = OpinionEngine(provider)

        profile = ProfileData(
            preferences=["likes open source"],
            values=["privacy"],
            personality=["analytical"],
        )

        prompt = engine.build_prompt(profile, "Is Rust better than Python?")

        assert "Person Profile" in prompt
        assert "likes open source" in prompt
        assert "privacy" in prompt
        assert "analytical" in prompt
        assert "Is Rust better than Python?" in prompt

    def test_build_prompt_empty_profile(self):
        """Test building prompt with empty profile."""
        provider = MockProvider()
        engine = OpinionEngine(provider)

        profile = ProfileData()
        prompt = engine.build_prompt(profile, "Test question?")

        assert "No profile data available" in prompt
        assert "Test question?" in prompt

    def test_parse_response_structured(self):
        """Test parsing structured response."""
        provider = MockProvider()
        engine = OpinionEngine(provider)

        response = """PREDICTED OPINION:
Based on what I know about you, your likely opinion is that Rust is better.

REASONING:
Your preference for performance and systems programming suggests this."""

        opinion, reasoning = engine.parse_response(response)

        assert "Rust is better" in opinion
        assert "performance" in reasoning

    def test_parse_response_unstructured(self):
        """Test parsing unstructured response."""
        provider = MockProvider()
        engine = OpinionEngine(provider)

        response = "Based on what I know about you, your likely opinion is yes.\n\nBecause you value efficiency."

        opinion, reasoning = engine.parse_response(response)

        assert "your likely opinion is yes" in opinion.lower()
        assert "efficiency" in reasoning

    def test_parse_response_adds_prefix(self):
        """Test that parser adds expected prefix if missing."""
        provider = MockProvider()
        engine = OpinionEngine(provider)

        response = "Rust is better than Python."

        opinion, _ = engine.parse_response(response)

        assert "Based on what I know about you" in opinion

    @pytest.mark.asyncio
    async def test_predict(self):
        """Test opinion prediction."""
        response_text = """PREDICTED OPINION:
Based on what I know about you, your likely opinion is that open source is superior.

REASONING:
Your profile indicates strong preference for open source tools."""

        provider = MockProvider(response_text)
        engine = OpinionEngine(provider)

        profile = ProfileData(
            preferences=["likes open source"],
            values=["transparency"],
        )

        result = await engine.predict(
            question="Is open source better?",
            profile=profile,
            profile_name="test",
        )

        assert isinstance(result, OpinionResult)
        assert result.provider == "mock"
        assert result.model == "test-model"
        assert result.profile_used == "test"
        assert "open source" in result.predicted_opinion

    @pytest.mark.asyncio
    async def test_predict_with_context(self):
        """Test opinion prediction with additional context."""
        response_text = """PREDICTED OPINION:
Based on what I know about you, your likely opinion is yes.

REASONING:
Given your preferences and the additional context provided."""

        provider = MockProvider(response_text)
        engine = OpinionEngine(provider)

        profile = ProfileData(
            preferences=["likes performance"],
        )

        result = await engine.predict_with_context(
            question="Should I use Rust?",
            profile=profile,
            additional_context=["working on performance-critical project"],
            profile_name="test",
        )

        assert isinstance(result, OpinionResult)
        assert "performance-critical" in result.reasoning or "additional context" in result.reasoning
