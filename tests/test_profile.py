"""Tests for MooAId profile system."""

import pytest
import asyncio
import tempfile
from pathlib import Path

from mooaid.profile import DatabaseManager, ProfileData
from mooaid.profile.service import ProfileService


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager instance."""
    db = DatabaseManager(temp_db_path)
    asyncio.get_event_loop().run_until_complete(db.init_db())
    yield db
    asyncio.get_event_loop().run_until_complete(db.close())


@pytest.fixture
def profile_service(db_manager):
    """Create a profile service instance."""
    return ProfileService(db_manager)


class TestProfileData:
    """Tests for ProfileData model."""

    def test_default_values(self):
        """Test default values for ProfileData."""
        profile = ProfileData()
        assert profile.preferences == []
        assert profile.values == []
        assert profile.personality == []
        assert profile.context == []

    def test_to_dict(self):
        """Test converting ProfileData to dictionary."""
        profile = ProfileData(
            preferences=["pref1"],
            values=["value1"],
            personality=["trait1"],
            context=["ctx1"],
        )
        data = profile.to_dict()
        assert data["preferences"] == ["pref1"]
        assert data["values"] == ["value1"]
        assert data["personality"] == ["trait1"]
        assert data["context"] == ["ctx1"]

    def test_from_dict(self):
        """Test creating ProfileData from dictionary."""
        data = {
            "preferences": ["pref1", "pref2"],
            "values": ["value1"],
        }
        profile = ProfileData.from_dict(data)
        assert profile.preferences == ["pref1", "pref2"]
        assert profile.values == ["value1"]
        assert profile.personality == []
        assert profile.context == []

    def test_format_for_prompt_empty(self):
        """Test formatting empty profile for prompt."""
        profile = ProfileData()
        formatted = profile.format_for_prompt()
        assert "No profile data available" in formatted

    def test_format_for_prompt_with_data(self):
        """Test formatting profile with data for prompt."""
        profile = ProfileData(
            preferences=["likes open source"],
            values=["privacy"],
        )
        formatted = profile.format_for_prompt()
        assert "Preferences:" in formatted
        assert "likes open source" in formatted
        assert "Values:" in formatted
        assert "privacy" in formatted


class TestDatabaseManager:
    """Tests for DatabaseManager."""

    @pytest.mark.asyncio
    async def test_init_db(self, db_manager):
        """Test database initialization."""
        # Should not raise any exceptions
        assert db_manager.db_path.endswith(".db")

    @pytest.mark.asyncio
    async def test_create_profile(self, db_manager):
        """Test creating a profile."""
        profile = await db_manager.create_profile("test_profile")
        assert isinstance(profile, ProfileData)

        # Verify it can be retrieved
        retrieved = await db_manager.get_profile("test_profile")
        assert retrieved is not None
        assert retrieved.preferences == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(self, db_manager):
        """Test getting a non-existent profile."""
        profile = await db_manager.get_profile("nonexistent")
        assert profile is None

    @pytest.mark.asyncio
    async def test_update_profile(self, db_manager):
        """Test updating a profile."""
        await db_manager.create_profile("test_update")
        profile = ProfileData(
            preferences=["updated pref"],
            values=["updated value"],
        )
        await db_manager.update_profile("test_update", profile)

        retrieved = await db_manager.get_profile("test_update")
        assert retrieved.preferences == ["updated pref"]
        assert retrieved.values == ["updated value"]

    @pytest.mark.asyncio
    async def test_add_to_profile(self, db_manager):
        """Test adding items to a profile."""
        await db_manager.add_to_profile("test_add", "preferences", ["pref1"])
        await db_manager.add_to_profile("test_add", "preferences", ["pref2"])

        profile = await db_manager.get_profile("test_add")
        assert "pref1" in profile.preferences
        assert "pref2" in profile.preferences

    @pytest.mark.asyncio
    async def test_add_unique_items(self, db_manager):
        """Test that adding items maintains uniqueness."""
        await db_manager.add_to_profile("test_unique", "preferences", ["pref1"])
        await db_manager.add_to_profile("test_unique", "preferences", ["pref1"])

        profile = await db_manager.get_profile("test_unique")
        assert profile.preferences.count("pref1") == 1

    @pytest.mark.asyncio
    async def test_remove_from_profile(self, db_manager):
        """Test removing items from a profile."""
        await db_manager.add_to_profile("test_remove", "preferences", ["pref1", "pref2"])
        await db_manager.remove_from_profile("test_remove", "preferences", ["pref1"])

        profile = await db_manager.get_profile("test_remove")
        assert "pref1" not in profile.preferences
        assert "pref2" in profile.preferences

    @pytest.mark.asyncio
    async def test_delete_profile(self, db_manager):
        """Test deleting a profile."""
        await db_manager.create_profile("test_delete")
        deleted = await db_manager.delete_profile("test_delete")
        assert deleted is True

        retrieved = await db_manager.get_profile("test_delete")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_profile(self, db_manager):
        """Test deleting a non-existent profile."""
        deleted = await db_manager.delete_profile("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_profiles(self, db_manager):
        """Test listing profiles."""
        await db_manager.create_profile("profile_a")
        await db_manager.create_profile("profile_b")

        profiles = await db_manager.list_profiles()
        assert "profile_a" in profiles
        assert "profile_b" in profiles

    @pytest.mark.asyncio
    async def test_save_opinion(self, db_manager):
        """Test saving opinion history."""
        await db_manager.create_profile("test_history")
        opinion_id = await db_manager.save_opinion(
            profile_name="test_history",
            question="Test question?",
            predicted_opinion="Test opinion",
            reasoning="Test reasoning",
            provider="test_provider",
            model="test_model",
        )
        assert opinion_id is not None

    @pytest.mark.asyncio
    async def test_get_opinion_history(self, db_manager):
        """Test getting opinion history."""
        await db_manager.create_profile("test_history")
        await db_manager.save_opinion(
            profile_name="test_history",
            question="Question 1?",
            predicted_opinion="Opinion 1",
            reasoning="Reasoning 1",
            provider="test",
            model="test",
        )
        await db_manager.save_opinion(
            profile_name="test_history",
            question="Question 2?",
            predicted_opinion="Opinion 2",
            reasoning="Reasoning 2",
            provider="test",
            model="test",
        )

        history = await db_manager.get_opinion_history("test_history")
        assert len(history) == 2


class TestProfileService:
    """Tests for ProfileService."""

    @pytest.mark.asyncio
    async def test_create_profile(self, profile_service):
        """Test creating a profile via service."""
        profile = await profile_service.create_profile("service_test")
        assert isinstance(profile, ProfileData)

    @pytest.mark.asyncio
    async def test_create_duplicate_profile(self, profile_service):
        """Test creating a duplicate profile raises error."""
        await profile_service.create_profile("duplicate_test")
        with pytest.raises(ValueError):
            await profile_service.create_profile("duplicate_test")

    @pytest.mark.asyncio
    async def test_add_preferences(self, profile_service):
        """Test adding preferences via service."""
        profile = await profile_service.add_preferences(
            "pref_test", ["pref1", "pref2"]
        )
        assert "pref1" in profile.preferences
        assert "pref2" in profile.preferences

    @pytest.mark.asyncio
    async def test_add_values(self, profile_service):
        """Test adding values via service."""
        profile = await profile_service.add_values(
            "value_test", ["privacy", "transparency"]
        )
        assert "privacy" in profile.values
        assert "transparency" in profile.values

    @pytest.mark.asyncio
    async def test_add_personality(self, profile_service):
        """Test adding personality traits via service."""
        profile = await profile_service.add_personality(
            "personality_test", ["analytical", "pragmatic"]
        )
        assert "analytical" in profile.personality
        assert "pragmatic" in profile.personality

    @pytest.mark.asyncio
    async def test_add_context(self, profile_service):
        """Test adding context via service."""
        profile = await profile_service.add_context(
            "context_test", ["works in tech"]
        )
        assert "works in tech" in profile.context

    @pytest.mark.asyncio
    async def test_get_full_profile(self, profile_service):
        """Test getting full profile info."""
        await profile_service.add_preferences("full_test", ["pref1"])
        full = await profile_service.get_full_profile("full_test")

        assert full is not None
        assert full["name"] == "full_test"
        assert "data" in full
        assert "formatted" in full
