"""Database module for MooAId profile storage."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic import BaseModel, Field


class ProfileData(BaseModel):
    """Model for profile data."""

    preferences: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    personality: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary."""
        return {
            "preferences": self.preferences,
            "values": self.values,
            "personality": self.personality,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileData":
        """Create from dictionary."""
        return cls(
            preferences=data.get("preferences", []),
            values=data.get("values", []),
            personality=data.get("personality", []),
            context=data.get("context", []),
        )

    def format_for_prompt(self) -> str:
        """Format profile data for AI prompt."""
        sections = []

        if self.preferences:
            sections.append("Preferences:")
            for pref in self.preferences:
                sections.append(f"  - {pref}")

        if self.values:
            sections.append("Values:")
            for value in self.values:
                sections.append(f"  - {value}")

        if self.personality:
            sections.append("Personality Traits:")
            for trait in self.personality:
                sections.append(f"  - {trait}")

        if self.context:
            sections.append("Additional Context:")
            for ctx in self.context:
                sections.append(f"  - {ctx}")

        return "\n".join(sections) if sections else "No profile data available."


class DatabaseManager:
    """Manages SQLite database operations."""

    _instance: "DatabaseManager | None" = None
    _db_path: str = "./mooaid.db"

    def __new__(cls, db_path: str | None = None) -> "DatabaseManager":
        """Singleton pattern for database manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if db_path:
                cls._db_path = db_path
        return cls._instance

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize the database manager."""
        if db_path:
            self._db_path = db_path

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._db_path

    @db_path.setter
    def db_path(self, path: str) -> None:
        """Set the database path."""
        self._db_path = path

    async def init_db(self) -> None:
        """Initialize the database schema."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    preferences TEXT DEFAULT '[]',
                    "values" TEXT DEFAULT '[]',
                    personality TEXT DEFAULT '[]',
                    context TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS opinion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_name TEXT NOT NULL,
                    question TEXT NOT NULL,
                    predicted_opinion TEXT NOT NULL,
                    reasoning TEXT,
                    provider TEXT NOT NULL,
                    model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (profile_name) REFERENCES profiles(name)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_opinion_history_profile 
                ON opinion_history(profile_name)
            """)

            await db.commit()

    async def get_profile(self, name: str) -> ProfileData | None:
        """Get a profile by name.

        Args:
            name: The profile name.

        Returns:
            ProfileData if found, None otherwise.
        """
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM profiles WHERE name = ?", (name,)
            ) as cursor:
                row = await cursor.fetchone()

                if row is None:
                    return None

                return ProfileData(
                    preferences=json.loads(row["preferences"]),
                    values=json.loads(row["values"]),
                    personality=json.loads(row["personality"]),
                    context=json.loads(row["context"]),
                )

    async def create_profile(self, name: str) -> ProfileData:
        """Create a new profile.

        Args:
            name: The profile name.

        Returns:
            ProfileData: The created profile data.
        """
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO profiles (name, preferences, "values", personality, context)
                VALUES (?, '[]', '[]', '[]', '[]')
                """,
                (name,),
            )
            await db.commit()

        return ProfileData()

    async def update_profile(self, name: str, data: ProfileData) -> None:
        """Update a profile.

        Args:
            name: The profile name.
            data: The profile data to update.
        """
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                UPDATE profiles
                SET preferences = ?, "values" = ?, personality = ?, context = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
                """,
                (
                    json.dumps(data.preferences),
                    json.dumps(data.values),
                    json.dumps(data.personality),
                    json.dumps(data.context),
                    name,
                ),
            )
            await db.commit()

    async def add_to_profile(
        self, name: str, field: str, items: list[str]
    ) -> ProfileData:
        """Add items to a profile field.

        Args:
            name: The profile name.
            field: The field to add to (preferences, values, personality, context).
            items: Items to add.

        Returns:
            ProfileData: The updated profile data.
        """
        profile = await self.get_profile(name)

        if profile is None:
            profile = await self.create_profile(name)

        current_items: list[str] = getattr(profile, field, [])

        # Add only unique items
        for item in items:
            if item not in current_items:
                current_items.append(item)

        setattr(profile, field, current_items)
        await self.update_profile(name, profile)

        return profile

    async def remove_from_profile(
        self, name: str, field: str, items: list[str]
    ) -> ProfileData:
        """Remove items from a profile field.

        Args:
            name: The profile name.
            field: The field to remove from.
            items: Items to remove.

        Returns:
            ProfileData: The updated profile data.
        """
        profile = await self.get_profile(name)

        if profile is None:
            raise ValueError(f"Profile '{name}' not found")

        current_items: list[str] = getattr(profile, field, [])

        for item in items:
            if item in current_items:
                current_items.remove(item)

        setattr(profile, field, current_items)
        await self.update_profile(name, profile)

        return profile

    async def delete_profile(self, name: str) -> bool:
        """Delete a profile.

        Args:
            name: The profile name.

        Returns:
            bool: True if deleted, False if not found.
        """
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "DELETE FROM profiles WHERE name = ?", (name,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def list_profiles(self) -> list[str]:
        """List all profile names.

        Returns:
            list[str]: List of profile names.
        """
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT name FROM profiles ORDER BY name") as cursor:
                rows = await cursor.fetchall()
                return [row["name"] for row in rows]

    async def save_opinion(
        self,
        profile_name: str,
        question: str,
        predicted_opinion: str,
        reasoning: str,
        provider: str,
        model: str | None = None,
    ) -> int:
        """Save an opinion prediction to history.

        Args:
            profile_name: The profile name.
            question: The question asked.
            predicted_opinion: The predicted opinion.
            reasoning: The reasoning provided.
            provider: The AI provider used.
            model: The model used.

        Returns:
            int: The ID of the saved opinion.
        """
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO opinion_history 
                (profile_name, question, predicted_opinion, reasoning, provider, model)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_name, question, predicted_opinion, reasoning, provider, model),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_opinion_history(
        self, profile_name: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get opinion history.

        Args:
            profile_name: Optional profile name to filter by.
            limit: Maximum number of results.

        Returns:
            list[dict]: List of opinion history records.
        """
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row

            if profile_name:
                query = """
                    SELECT * FROM opinion_history 
                    WHERE profile_name = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                params: tuple = (profile_name, limit)
            else:
                query = """
                    SELECT * FROM opinion_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                params = (limit,)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def close(self) -> None:
        """Close database connections (cleanup)."""
        # aiosqlite handles connection closing automatically
        pass


async def get_db(db_path: str | None = None) -> DatabaseManager:
    """Get the database manager instance.

    Args:
        db_path: Optional database path.

    Returns:
        DatabaseManager: The database manager instance.
    """
    db = DatabaseManager(db_path)
    await db.init_db()
    return db
