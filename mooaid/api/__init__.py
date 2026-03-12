"""API module for MooAId REST API."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mooaid.config import Config, get_config
from mooaid.core.opinion_engine import OpinionResult
from mooaid.core.provider_factory import get_provider
from mooaid.profile import DatabaseManager, ProfileData
from mooaid.profile.service import ProfileService
from mooaid.core.opinion_engine import OpinionEngine


# Request/Response Models
class OpinionRequest(BaseModel):
    """Request model for opinion prediction."""

    question: str = Field(..., description="The question to predict opinion on")
    profile_name: str | None = Field(
        None, description="Profile name to use (defaults to 'default')"
    )
    additional_context: list[str] = Field(
        default_factory=list, description="Additional context for this prediction"
    )


class OpinionResponse(BaseModel):
    """Response model for opinion prediction."""

    predicted_opinion: str
    reasoning: str
    model: str
    provider: str
    profile_used: str | None = None


class ProfileCreateRequest(BaseModel):
    """Request model for creating a profile."""

    name: str = Field(..., description="Profile name")


class ProfileUpdateRequest(BaseModel):
    """Request model for updating profile fields."""

    preferences: list[str] | None = None
    values: list[str] | None = None
    personality: list[str] | None = None
    context: list[str] | None = None


class ProfileAddRequest(BaseModel):
    """Request model for adding items to profile."""

    items: list[str] = Field(..., description="Items to add")
    field: str = Field(..., description="Field to add to (preferences, values, etc.)")


class ProfileResponse(BaseModel):
    """Response model for profile data."""

    name: str
    preferences: list[str]
    values: list[str]
    personality: list[str]
    context: list[str]


class ConfigResponse(BaseModel):
    """Response model for configuration."""

    provider: str
    available_providers: list[str]
    database_path: str
    api_host: str
    api_port: int


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    provider_status: dict[str, bool]


# Global services (initialized on startup)
db_manager: DatabaseManager | None = None
profile_service: ProfileService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global db_manager, profile_service

    # Startup
    config = get_config()
    db_manager = DatabaseManager(config.database.path)
    await db_manager.init_db()
    profile_service = ProfileService(db_manager)

    yield

    # Shutdown
    if db_manager:
        await db_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application.
    """
    app = FastAPI(
        title="MooAId API",
        description="My Opinion AI Daemon - Predicts what your opinion would likely be",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register API routes.

    Args:
        app: The FastAPI application.
    """

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "name": "MooAId API",
            "description": "My Opinion AI Daemon",
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        config = get_config()
        provider_status = {}

        # Check configured provider
        try:
            provider = get_provider(config.provider)
            is_healthy = await provider.check_health()
            provider_status[config.provider] = is_healthy
        except Exception:
            provider_status[config.provider] = False

        return HealthResponse(
            status="healthy" if provider_status.get(config.provider, False) else "degraded",
            provider_status=provider_status,
        )

    @app.get("/config", response_model=ConfigResponse, tags=["Configuration"])
    async def get_configuration() -> ConfigResponse:
        """Get current configuration."""
        config = get_config()
        from mooaid.core.provider_factory import ProviderFactory

        return ConfigResponse(
            provider=config.provider,
            available_providers=ProviderFactory.get_available_providers(),
            database_path=config.database.path,
            api_host=config.api.host,
            api_port=config.api.port,
        )

    @app.post("/opinion", response_model=OpinionResponse, tags=["Opinion"])
    async def predict_opinion(request: OpinionRequest) -> OpinionResponse:
        """Predict an opinion for the given question.

        Args:
            request: The opinion request.

        Returns:
            OpinionResponse: The predicted opinion.

        Raises:
            HTTPException: If profile not found or prediction fails.
        """
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        # Determine profile name
        profile_name = request.profile_name or "default"

        # Get profile
        profile = await profile_service.get_profile(profile_name)
        if profile is None:
            # Create default profile if it doesn't exist and name is 'default'
            if profile_name == "default":
                profile = await profile_service.create_profile(profile_name)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Profile '{profile_name}' not found",
                )

        # Get provider and create engine
        config = get_config()
        try:
            provider = get_provider(config.provider)
            engine = OpinionEngine(provider)

            # Predict opinion
            result: OpinionResult
            if request.additional_context:
                result = await engine.predict_with_context(
                    question=request.question,
                    profile=profile,
                    additional_context=request.additional_context,
                    profile_name=profile_name,
                )
            else:
                result = await engine.predict(
                    question=request.question,
                    profile=profile,
                    profile_name=profile_name,
                )

            # Save to history
            await db_manager.save_opinion(
                profile_name=profile_name,
                question=request.question,
                predicted_opinion=result.predicted_opinion,
                reasoning=result.reasoning,
                provider=result.provider,
                model=result.model,
            )

            return OpinionResponse(
                predicted_opinion=result.predicted_opinion,
                reasoning=result.reasoning,
                model=result.model,
                provider=result.provider,
                profile_used=result.profile_used,
            )

        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prediction failed: {str(e)}",
            ) from e

    @app.get("/profile", response_model=list[str], tags=["Profile"])
    async def list_profiles() -> list[str]:
        """List all profile names."""
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        return await profile_service.list_profiles()

    @app.get("/profile/{profile_name}", response_model=ProfileResponse, tags=["Profile"])
    async def get_profile(profile_name: str) -> ProfileResponse:
        """Get a specific profile.

        Args:
            profile_name: The profile name.

        Returns:
            ProfileResponse: The profile data.

        Raises:
            HTTPException: If profile not found.
        """
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        profile = await profile_service.get_profile(profile_name)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found",
            )

        return ProfileResponse(
            name=profile_name,
            preferences=profile.preferences,
            values=profile.values,
            personality=profile.personality,
            context=profile.context,
        )

    @app.post("/profile", response_model=ProfileResponse, tags=["Profile"])
    async def create_profile(request: ProfileCreateRequest) -> ProfileResponse:
        """Create a new profile.

        Args:
            request: The profile creation request.

        Returns:
            ProfileResponse: The created profile.

        Raises:
            HTTPException: If profile already exists.
        """
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        try:
            profile = await profile_service.create_profile(request.name)
            return ProfileResponse(
                name=request.name,
                preferences=profile.preferences,
                values=profile.values,
                personality=profile.personality,
                context=profile.context,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e

    @app.put("/profile/{profile_name}", response_model=ProfileResponse, tags=["Profile"])
    async def update_profile(
        profile_name: str, request: ProfileUpdateRequest
    ) -> ProfileResponse:
        """Update a profile's fields.

        Args:
            profile_name: The profile name.
            request: The update request.

        Returns:
            ProfileResponse: The updated profile.

        Raises:
            HTTPException: If profile not found.
        """
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        profile = await profile_service.get_profile(profile_name)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found",
            )

        # Update fields
        if request.preferences is not None:
            profile.preferences = request.preferences
        if request.values is not None:
            profile.values = request.values
        if request.personality is not None:
            profile.personality = request.personality
        if request.context is not None:
            profile.context = request.context

        await profile_service.update_profile(profile_name, profile)

        return ProfileResponse(
            name=profile_name,
            preferences=profile.preferences,
            values=profile.values,
            personality=profile.personality,
            context=profile.context,
        )

    @app.post(
        "/profile/{profile_name}/add", response_model=ProfileResponse, tags=["Profile"]
    )
    async def add_to_profile(profile_name: str, request: ProfileAddRequest) -> ProfileResponse:
        """Add items to a profile field.

        Args:
            profile_name: The profile name.
            request: The add request.

        Returns:
            ProfileResponse: The updated profile.

        Raises:
            HTTPException: If profile not found or invalid field.
        """
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        valid_fields = ["preferences", "values", "personality", "context"]
        if request.field not in valid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid field. Must be one of: {valid_fields}",
            )

        try:
            profile = await getattr(profile_service, f"add_{request.field}")(
                profile_name, request.items
            )
            return ProfileResponse(
                name=profile_name,
                preferences=profile.preferences,
                values=profile.values,
                personality=profile.personality,
                context=profile.context,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e

    @app.delete("/profile/{profile_name}", tags=["Profile"])
    async def delete_profile(profile_name: str) -> dict[str, str]:
        """Delete a profile.

        Args:
            profile_name: The profile name.

        Returns:
            dict: Success message.

        Raises:
            HTTPException: If profile not found.
        """
        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        deleted = await profile_service.delete_profile(profile_name)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found",
            )

        return {"message": f"Profile '{profile_name}' deleted successfully"}


# Create the app instance
app = create_app()
