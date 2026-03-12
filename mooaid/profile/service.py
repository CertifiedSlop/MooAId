"""Profile management service for MooAId."""

from typing import Any

from mooaid.profile import DatabaseManager, ProfileData


class ProfileService:
    """Service for managing user profiles."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize the profile service.

        Args:
            db: The database manager instance.
        """
        self.db = db

    async def get_profile(self, name: str) -> ProfileData | None:
        """Get a profile by name.

        Args:
            name: The profile name.

        Returns:
            ProfileData if found, None otherwise.
        """
        return await self.db.get_profile(name)

    async def create_profile(self, name: str) -> ProfileData:
        """Create a new profile.

        Args:
            name: The profile name.

        Returns:
            ProfileData: The created profile data.

        Raises:
            ValueError: If profile already exists.
        """
        existing = await self.db.get_profile(name)
        if existing is not None:
            raise ValueError(f"Profile '{name}' already exists")

        return await self.db.create_profile(name)

    async def update_profile(self, name: str, data: ProfileData) -> ProfileData:
        """Update a profile.

        Args:
            name: The profile name.
            data: The profile data.

        Returns:
            ProfileData: The updated profile data.

        Raises:
            ValueError: If profile doesn't exist.
        """
        existing = await self.db.get_profile(name)
        if existing is None:
            raise ValueError(f"Profile '{name}' not found")

        await self.db.update_profile(name, data)
        return data

    async def add_preferences(self, name: str, items: list[str]) -> ProfileData:
        """Add preferences to a profile.

        Args:
            name: The profile name.
            items: Preferences to add.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.add_to_profile(name, "preferences", items)

    async def add_values(self, name: str, items: list[str]) -> ProfileData:
        """Add values to a profile.

        Args:
            name: The profile name.
            items: Values to add.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.add_to_profile(name, "values", items)

    async def add_personality(self, name: str, items: list[str]) -> ProfileData:
        """Add personality traits to a profile.

        Args:
            name: The profile name.
            items: Personality traits to add.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.add_to_profile(name, "personality", items)

    async def add_context(self, name: str, items: list[str]) -> ProfileData:
        """Add context to a profile.

        Args:
            name: The profile name.
            items: Context items to add.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.add_to_profile(name, "context", items)

    async def remove_preferences(self, name: str, items: list[str]) -> ProfileData:
        """Remove preferences from a profile.

        Args:
            name: The profile name.
            items: Preferences to remove.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.remove_from_profile(name, "preferences", items)

    async def remove_values(self, name: str, items: list[str]) -> ProfileData:
        """Remove values from a profile.

        Args:
            name: The profile name.
            items: Values to remove.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.remove_from_profile(name, "values", items)

    async def remove_personality(self, name: str, items: list[str]) -> ProfileData:
        """Remove personality traits from a profile.

        Args:
            name: The profile name.
            items: Personality traits to remove.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.remove_from_profile(name, "personality", items)

    async def remove_context(self, name: str, items: list[str]) -> ProfileData:
        """Remove context from a profile.

        Args:
            name: The profile name.
            items: Context items to remove.

        Returns:
            ProfileData: The updated profile data.
        """
        return await self.db.remove_from_profile(name, "context", items)

    async def delete_profile(self, name: str) -> bool:
        """Delete a profile.

        Args:
            name: The profile name.

        Returns:
            bool: True if deleted, False if not found.
        """
        return await self.db.delete_profile(name)

    async def list_profiles(self) -> list[str]:
        """List all profile names.

        Returns:
            list[str]: List of profile names.
        """
        return await self.db.list_profiles()

    async def get_full_profile(self, name: str) -> dict[str, Any] | None:
        """Get full profile information including metadata.

        Args:
            name: The profile name.

        Returns:
            dict: Full profile information or None if not found.
        """
        profile = await self.db.get_profile(name)
        if profile is None:
            return None

        return {
            "name": name,
            "data": profile.to_dict(),
            "formatted": profile.format_for_prompt(),
        }
