"""Tests for the Profile Builder module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mooaid.profile.builder import ProfileBuilder, ProfileBuilderState, QuestionCategory
from mooaid.profile import ProfileData


class MockProvider:
    """Mock AI provider for testing."""

    async def generate(self, prompt: str, model: str | None = None):
        """Mock generate method."""
        from mooaid.core import GenerationResult

        # Return different responses based on prompt content
        if "Generate the next question" in prompt:
            if "Interests" in prompt:
                content = "What hobbies or activities do you enjoy in your free time?"
            elif "Values" in prompt:
                content = "What principles or beliefs are most important to you?"
            elif "Personality" in prompt:
                content = "How would you describe your approach to solving problems?"
            else:
                content = "Tell me about your work or daily environment."
        elif "Extract profile information" in prompt:
            # Return JSON analysis
            content = '''{
                "preferences": ["reading", "hiking"],
                "values": ["honesty", "creativity"],
                "personality": ["analytical", "curious"],
                "context": ["works in tech"],
                "summary": "Person enjoys intellectual and outdoor activities."
            }'''
        else:
            content = "Test response"

        return GenerationResult(
            content=content,
            model="test-model",
            provider="test-provider"
        )

    async def check_health(self) -> bool:
        """Mock health check."""
        return True


@pytest.fixture
def mock_provider():
    """Create a mock provider instance."""
    return MockProvider()


@pytest.fixture
def builder(mock_provider):
    """Create a ProfileBuilder instance for testing."""
    return ProfileBuilder(mock_provider)


class TestProfileBuilderState:
    """Tests for ProfileBuilderState dataclass."""

    def test_initial_state(self):
        """Test initial state creation."""
        state = ProfileBuilderState(profile_name="test")

        assert state.profile_name == "test"
        assert state.current_question == ""
        assert state.current_category == ""
        assert state.answers == []
        assert state.question_history == []
        assert state.is_complete is False
        assert state.profile_data is None


class TestProfileBuilderCategories:
    """Tests for ProfileBuilder categories."""

    def test_categories_defined(self, builder):
        """Test that categories are properly defined."""
        categories = builder.CATEGORIES

        assert len(categories) == 4

        # Check category names
        names = [cat.name for cat in categories]
        assert "Interests & Hobbies" in names
        assert "Core Values" in names
        assert "Personality Traits" in names
        assert "Life Context" in names

        # Check fields
        fields = [cat.field for cat in categories]
        assert "preferences" in fields
        assert "values" in fields
        assert "personality" in fields
        assert "context" in fields


class TestProfileBuilderSession:
    """Tests for ProfileBuilder session management."""

    @pytest.mark.asyncio
    async def test_start_session(self, builder):
        """Test starting a new session."""
        state = await builder.start_session("test_profile")

        assert state is not None
        assert state.profile_name == "test_profile"
        assert state.is_complete is False
        assert builder.state is not None

    @pytest.mark.asyncio
    async def test_generate_question_without_session(self, builder):
        """Test generating question without active session."""
        with pytest.raises(RuntimeError, match="No active session"):
            await builder.generate_question()

    @pytest.mark.asyncio
    async def test_submit_answer_without_session(self, builder):
        """Test submitting answer without active session."""
        with pytest.raises(RuntimeError, match="No active session"):
            await builder.submit_answer("test answer")

    @pytest.mark.asyncio
    async def test_complete_session_without_session(self, builder):
        """Test completing session without active session."""
        with pytest.raises(RuntimeError, match="No active session"):
            await builder.complete_session()


class TestProfileBuilderQuestions:
    """Tests for ProfileBuilder question generation."""

    @pytest.mark.asyncio
    async def test_generate_question(self, builder):
        """Test generating a question."""
        await builder.start_session("test_profile")
        question = await builder.generate_question()

        assert question is not None
        assert len(question) > 0
        assert builder.state.current_question == question

    @pytest.mark.asyncio
    async def test_question_progression(self, builder):
        """Test that questions progress through categories."""
        await builder.start_session("test_profile")

        # Generate multiple questions
        questions = []
        for _ in range(4):  # Should move to second category after 3 questions
            question = await builder.generate_question()
            questions.append(question)
            await builder.submit_answer(f"Answer to: {question}")

        # Check that we have questions
        assert len(questions) == 4
        assert all(len(q) > 0 for q in questions)


class TestProfileBuilderAnalysis:
    """Tests for ProfileBuilder answer analysis."""

    @pytest.mark.asyncio
    async def test_submit_answer(self, builder):
        """Test submitting an answer."""
        await builder.start_session("test_profile")
        await builder.generate_question()

        analysis = await builder.submit_answer("I love reading and hiking")

        assert analysis is not None
        assert "summary" in analysis
        assert "preferences" in analysis
        assert "values" in analysis
        assert "personality" in analysis
        assert "context" in analysis

    @pytest.mark.asyncio
    async def test_answer_stored(self, builder):
        """Test that answers are stored in state."""
        await builder.start_session("test_profile")
        await builder.generate_question()

        await builder.submit_answer("Test answer")

        assert len(builder.state.answers) == 1
        assert builder.state.answers[0] == "Test answer"


class TestProfileBuilderCompletion:
    """Tests for ProfileBuilder session completion."""

    @pytest.mark.asyncio
    async def test_complete_session(self, builder):
        """Test completing a session."""
        await builder.start_session("test_profile")

        # Generate and answer a few questions
        for _ in range(3):
            await builder.generate_question()
            await builder.submit_answer("Test answer")

        profile_data = await builder.complete_session()

        assert profile_data is not None
        assert isinstance(profile_data, ProfileData)
        assert builder.state.is_complete is True
        assert builder.state.profile_data == profile_data

    @pytest.mark.asyncio
    async def test_get_progress(self, builder):
        """Test getting session progress."""
        await builder.start_session("test_profile")

        # Initial progress
        progress = builder.get_progress()
        assert progress["complete"] is False
        assert progress["questions_answered"] == 0
        assert progress["total_questions"] == 11  # 3+3+3+2

        # After answering some questions
        await builder.generate_question()
        await builder.submit_answer("Answer 1")

        progress = builder.get_progress()
        assert progress["questions_answered"] == 1
        assert progress["progress_percent"] > 0


class TestProfileBuilderIntegration:
    """Integration tests for ProfileBuilder."""

    @pytest.mark.asyncio
    async def test_full_session(self, builder):
        """Test a complete profile building session."""
        # Start session
        state = await builder.start_session("integration_test")
        assert state.profile_name == "integration_test"

        # Answer all questions (11 total)
        for i in range(11):
            question = await builder.generate_question()
            assert question is not None
            assert len(question) > 0

            analysis = await builder.submit_answer(f"Answer {i + 1}")
            assert analysis is not None

        # Complete session
        profile_data = await builder.complete_session()

        assert profile_data is not None
        assert builder.state.is_complete is True

        # Check progress
        progress = builder.get_progress()
        assert progress["complete"] is True


class TestQuestionCategory:
    """Tests for QuestionCategory dataclass."""

    def test_category_creation(self):
        """Test creating a question category."""
        category = QuestionCategory(
            name="Test Category",
            description="Test description",
            field="preferences",
            question_count=3
        )

        assert category.name == "Test Category"
        assert category.description == "Test description"
        assert category.field == "preferences"
        assert category.question_count == 3
