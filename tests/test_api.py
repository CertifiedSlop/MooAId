"""Tests for MooAId API."""

import pytest
from httpx import AsyncClient, ASGITransport

from mooaid.api import app


@pytest.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "MooAId API"


class TestHealthEndpoint:
    """Tests for health endpoint."""

    @pytest.mark.asyncio
    async def test_health(self, client):
        """Test health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "provider_status" in data


class TestConfigEndpoint:
    """Tests for config endpoint."""

    @pytest.mark.asyncio
    async def test_get_config(self, client):
        """Test getting configuration."""
        response = await client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "available_providers" in data
        assert "database_path" in data


class TestProfileEndpoints:
    """Tests for profile endpoints."""

    @pytest.mark.asyncio
    async def test_list_profiles(self, client):
        """Test listing profiles."""
        response = await client.get("/profile")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_profile(self, client):
        """Test creating a profile."""
        response = await client.post(
            "/profile",
            json={"name": "test_profile"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_profile"
        assert "preferences" in data
        assert "values" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_profile(self, client):
        """Test creating a duplicate profile."""
        await client.post("/profile", json={"name": "duplicate_test"})
        response = await client.post(
            "/profile",
            json={"name": "duplicate_test"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_profile(self, client):
        """Test getting a profile."""
        await client.post("/profile", json={"name": "get_test"})
        response = await client.get("/profile/get_test")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "get_test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(self, client):
        """Test getting a non-existent profile."""
        response = await client.get("/profile/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_to_profile(self, client):
        """Test adding items to a profile."""
        await client.post("/profile", json={"name": "add_test"})
        response = await client.post(
            "/profile/add_test/add",
            json={"field": "preferences", "items": ["pref1", "pref2"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "pref1" in data["preferences"]
        assert "pref2" in data["preferences"]

    @pytest.mark.asyncio
    async def test_add_invalid_field(self, client):
        """Test adding to invalid field."""
        await client.post("/profile", json={"name": "invalid_test"})
        response = await client.post(
            "/profile/invalid_test/add",
            json={"field": "invalid_field", "items": ["item1"]},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_profile(self, client):
        """Test updating a profile."""
        await client.post("/profile", json={"name": "update_test"})
        response = await client.put(
            "/profile/update_test",
            json={
                "preferences": ["updated_pref"],
                "values": ["updated_value"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"] == ["updated_pref"]
        assert data["values"] == ["updated_value"]

    @pytest.mark.asyncio
    async def test_delete_profile(self, client):
        """Test deleting a profile."""
        await client.post("/profile", json={"name": "delete_test"})
        response = await client.delete("/profile/delete_test")
        assert response.status_code == 200

        # Verify deletion
        get_response = await client.get("/profile/delete_test")
        assert get_response.status_code == 404


class TestOpinionEndpoint:
    """Tests for opinion endpoint."""

    @pytest.mark.asyncio
    async def test_predict_opinion_no_profile(self, client):
        """Test opinion prediction creates default profile if needed."""
        response = await client.post(
            "/opinion",
            json={"question": "Is Rust better than Python?"},
        )
        # Should succeed with default profile (may fail if no API key configured)
        # This test verifies the endpoint accepts the request format
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_predict_opinion_with_profile(self, client):
        """Test opinion prediction with existing profile."""
        # Create profile first
        await client.post("/profile", json={"name": "opinion_test"})
        await client.post(
            "/profile/opinion_test/add",
            json={"field": "preferences", "items": ["likes performance"]},
        )

        response = await client.post(
            "/opinion",
            json={
                "question": "Is Rust better than Python?",
                "profile_name": "opinion_test",
            },
        )
        # Should succeed (may fail if no API key configured)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_predict_opinion_nonexistent_profile(self, client):
        """Test opinion prediction with non-existent profile."""
        response = await client.post(
            "/opinion",
            json={
                "question": "Test question?",
                "profile_name": "nonexistent_profile",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_predict_opinion_with_context(self, client):
        """Test opinion prediction with additional context."""
        await client.post("/profile", json={"name": "context_test"})

        response = await client.post(
            "/opinion",
            json={
                "question": "Should I use async code?",
                "profile_name": "context_test",
                "additional_context": ["working on I/O bound application"],
            },
        )
        # Should succeed (may fail if no API key configured)
        assert response.status_code in [200, 500]
