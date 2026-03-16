"""API module for MooAId REST API."""

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mooaid.config import Config, get_config
from mooaid.core.opinion_engine import OpinionResult
from mooaid.core.provider_factory import get_provider
from mooaid.profile import DatabaseManager, ProfileData
from mooaid.profile.service import ProfileService
from mooaid.core.opinion_engine import OpinionEngine

# Import providers to ensure they are registered
from mooaid.providers import (
    OpenRouterProvider,
    OllamaProvider,
    OpenAIProvider,
    GeminiProvider,
)


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
    openrouter_model: str | None = None
    openai_model: str | None = None
    gemini_model: str | None = None
    ollama_model: str | None = None
    openrouter_api_key: str | None = None  # Masked, only shows if set
    provider_status: dict[str, bool] | None = None


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""

    provider: str | None = None
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    ollama_host: str | None = None
    ollama_model: str | None = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    provider_status: dict[str, bool]


class ProfileBuilderStartRequest(BaseModel):
    """Request model for starting a profile builder session."""

    profile_name: str = Field(..., description="Name for the profile being created")


class ProfileBuilderQuestionResponse(BaseModel):
    """Response model for profile builder question."""

    question: str
    category: str
    question_number: int
    total_questions: int
    progress_percent: int


class ProfileBuilderAnswerRequest(BaseModel):
    """Request model for submitting an answer to the profile builder."""

    answer: str = Field(..., description="The user's answer")


class ProfileBuilderAnalysisResponse(BaseModel):
    """Response model for profile builder analysis."""

    summary: str
    extracted: dict[str, list[str]]
    progress: dict[str, Any]


class ProfileBuilderCompleteResponse(BaseModel):
    """Response model for completed profile builder session."""

    profile_name: str
    profile_data: dict[str, list[str]]
    summary: str


# Global services (initialized on startup)
db_manager: DatabaseManager | None = None
profile_service: ProfileService | None = None

# Profile builder sessions (in-memory store)
# Maps session_id -> (profile_name, ProfileBuilder instance)
profile_builder_sessions: dict[str, tuple[str, Any]] = {}


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

    # Mount static files for web UI
    webui_path = Path(__file__).parent.parent / "webui"
    if webui_path.exists():
        # Mount CSS directory
        css_path = webui_path / "css"
        if css_path.exists():
            app.mount("/css", StaticFiles(directory=str(css_path)), name="css")

        # Mount JS directory
        js_path = webui_path / "js"
        if js_path.exists():
            app.mount("/js", StaticFiles(directory=str(js_path)), name="js")

        # Mount root webui files
        app.mount("/static", StaticFiles(directory=str(webui_path)), name="static")

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register API routes.

    Args:
        app: The FastAPI application.
    """
    from fastapi.responses import FileResponse

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "name": "MooAId API",
            "description": "My Opinion AI Daemon",
            "docs": "/docs",
            "ui": "/static/index.html",
        }

    @app.get("/ui", tags=["Root"])
    async def web_ui() -> FileResponse:
        """Serve the web UI."""
        webui_path = Path(__file__).parent.parent / "webui" / "index.html"
        return FileResponse(str(webui_path))

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

        # Mask API key (show only if set)
        masked_key = None
        if config.openrouter.api_key and len(config.openrouter.api_key) > 10:
            masked_key = config.openrouter.api_key[:10] + "..." + config.openrouter.api_key[-4:]

        return ConfigResponse(
            provider=config.provider,
            available_providers=ProviderFactory.get_available_providers(),
            database_path=config.database.path,
            api_host=config.api.host,
            api_port=config.api.port,
            openrouter_model=config.openrouter.default_model,
            openai_model=config.openai.default_model,
            gemini_model=config.gemini.default_model,
            ollama_model=config.ollama.model,
            openrouter_api_key=masked_key,
            provider_status=None,  # Will be fetched separately by health endpoint
        )

    @app.put("/config", tags=["Configuration"])
    async def update_configuration(request: ConfigUpdateRequest) -> ConfigResponse:
        """Update configuration.

        Args:
            request: The configuration update request.

        Returns:
            ConfigResponse: The updated configuration.
        """
        from mooaid.config import ConfigManager, get_config
        from mooaid.core.provider_factory import ProviderFactory

        config = get_config()

        # Update provider
        if request.provider is not None:
            config.provider = request.provider

        # Update API keys and models
        if request.openrouter_api_key is not None:
            config.openrouter.api_key = request.openrouter_api_key
        if request.openrouter_model is not None:
            config.openrouter.default_model = request.openrouter_model
        if request.openai_api_key is not None:
            config.openai.api_key = request.openai_api_key
        if request.openai_model is not None:
            config.openai.default_model = request.openai_model
        if request.gemini_api_key is not None:
            config.gemini.api_key = request.gemini_api_key
        if request.gemini_model is not None:
            config.gemini.default_model = request.gemini_model

        # Update Ollama settings
        if request.ollama_host is not None:
            config.ollama.host = request.ollama_host
        if request.ollama_model is not None:
            config.ollama.model = request.ollama_model

        # Save configuration to file
        ConfigManager.save(config)

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

        # Get provider and create engine with correct model
        config = get_config()
        try:
            provider = get_provider(config.provider)

            # Get the correct model for the selected provider
            selected_model = None
            if config.provider == 'openrouter':
                selected_model = config.openrouter.default_model
            elif config.provider == 'openai':
                selected_model = config.openai.default_model
            elif config.provider == 'gemini':
                selected_model = config.gemini.default_model
            elif config.provider == 'ollama':
                selected_model = config.ollama.model

            # Create engine with selected model
            engine = OpinionEngine(provider, model=selected_model)

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

    @app.get("/history", tags=["History"])
    async def get_history(limit: int = 20) -> list[dict[str, Any]]:
        """Get opinion history.

        Args:
            limit: Maximum number of history items to return.

        Returns:
            list: List of opinion history items.
        """
        global db_manager

        if db_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        async with aiosqlite.connect(db_manager._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT id, profile_name, question, predicted_opinion,
                       reasoning, provider, model, created_at
                FROM opinion_history
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    @app.get("/models", tags=["Configuration"])
    async def get_models() -> dict[str, dict[str, list[dict[str, str]]]]:
        """Get available models for each provider.

        Returns:
            dict: Available models grouped by provider.
        """
        import logging
        from mooaid.core.provider_factory import get_provider

        models = {
            "openrouter": [],
            "openai": [],
            "gemini": [],
            "ollama": [],
        }

        # Try to fetch OpenRouter models
        try:
            provider = get_provider("openrouter")
            logging.info(f"Got OpenRouter provider: {provider}")
            if hasattr(provider, "get_models"):
                openrouter_models = await provider.get_models()
                logging.info(f"Fetched {len(openrouter_models)} models from OpenRouter")
                models["openrouter"] = openrouter_models
        except Exception as e:
            logging.error(f"Failed to fetch OpenRouter models: {e}")
            # Return default models if API call fails
            models["openrouter"] = [
                {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku"},
                {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"},
                {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
                {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "openai/gpt-4o", "name": "GPT-4o"},
                {"id": "meta-llama/llama-3-70b-instruct", "name": "Llama 3 70B"},
                {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5"},
                {"id": "mistralai/mistral-large", "name": "Mistral Large"},
            ]

        # Default models for other providers
        models["openai"] = [
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "gpt-4o", "name": "GPT-4o"},
        ]
        models["gemini"] = [
            {"id": "gemini-pro", "name": "Gemini Pro"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
        ]
        models["ollama"] = [
            {"id": "llama3", "name": "Llama 3"},
            {"id": "llama2", "name": "Llama 2"},
            {"id": "mistral", "name": "Mistral"},
            {"id": "gemma", "name": "Gemma"},
        ]

        return {"models": models}

    # Profile Builder Endpoints
    @app.post("/profile-builder/start", response_model=dict, tags=["Profile Builder"])
    async def start_profile_builder(request: ProfileBuilderStartRequest) -> dict:
        """Start a new profile builder session.

        Args:
            request: The profile builder start request.

        Returns:
            dict: Session ID and initial info.
        """
        import uuid
        from mooaid.profile.builder import ProfileBuilder

        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Get provider and create builder
        config = get_config()
        provider = get_provider(config.provider)

        # Get model for provider
        selected_model = None
        if config.provider == 'openrouter':
            selected_model = config.openrouter.default_model
        elif config.provider == 'openai':
            selected_model = config.openai.default_model
        elif config.provider == 'gemini':
            selected_model = config.gemini.default_model
        elif config.provider == 'ollama':
            selected_model = config.ollama.model

        builder = ProfileBuilder(provider, model=selected_model)
        await builder.start_session(request.profile_name)

        # Store session
        profile_builder_sessions[session_id] = (request.profile_name, builder)

        return {
            "session_id": session_id,
            "profile_name": request.profile_name,
        }

    @app.post("/profile-builder/{session_id}/question", response_model=ProfileBuilderQuestionResponse, tags=["Profile Builder"])
    async def get_next_question(session_id: str) -> ProfileBuilderQuestionResponse:
        """Get the next question in the profile builder session.

        Args:
            session_id: The session ID.

        Returns:
            ProfileBuilderQuestionResponse: The next question.

        Raises:
            HTTPException: If session not found or complete.
        """
        from mooaid.profile.builder import ProfileBuilder

        if session_id not in profile_builder_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        profile_name, builder = profile_builder_sessions[session_id]

        if builder.state and builder.state.is_complete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is complete",
            )

        # Generate next question
        question = await builder.generate_question()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No more questions",
            )

        # Get progress
        progress = builder.get_progress()

        return ProfileBuilderQuestionResponse(
            question=question,
            category=progress["current_category"] or "",
            question_number=progress["questions_answered"] + 1,
            total_questions=progress["total_questions"],
            progress_percent=progress["progress_percent"],
        )

    @app.post("/profile-builder/{session_id}/answer", response_model=ProfileBuilderAnalysisResponse, tags=["Profile Builder"])
    async def submit_answer(
        session_id: str,
        request: ProfileBuilderAnswerRequest
    ) -> ProfileBuilderAnalysisResponse:
        """Submit an answer to the current question.

        Args:
            session_id: The session ID.
            request: The answer request.

        Returns:
            ProfileBuilderAnalysisResponse: Analysis of the answer.

        Raises:
            HTTPException: If session not found.
        """
        from mooaid.profile.builder import ProfileBuilder

        if session_id not in profile_builder_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        profile_name, builder = profile_builder_sessions[session_id]

        # Submit answer and get analysis
        analysis = await builder.submit_answer(request.answer)

        # Get progress
        progress = builder.get_progress()

        return ProfileBuilderAnalysisResponse(
            summary=analysis.get("summary", ""),
            extracted={
                "preferences": analysis.get("preferences", []),
                "values": analysis.get("values", []),
                "personality": analysis.get("personality", []),
                "context": analysis.get("context", []),
            },
            progress=progress,
        )

    @app.post("/profile-builder/{session_id}/complete", response_model=ProfileBuilderCompleteResponse, tags=["Profile Builder"])
    async def complete_profile_builder(session_id: str) -> ProfileBuilderCompleteResponse:
        """Complete the profile builder session and save the profile.

        Args:
            session_id: The session ID.

        Returns:
            ProfileBuilderCompleteResponse: The completed profile.

        Raises:
            HTTPException: If session not found.
        """
        from mooaid.profile.builder import ProfileBuilder

        global profile_service

        if profile_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not initialized",
            )

        if session_id not in profile_builder_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        profile_name, builder = profile_builder_sessions[session_id]

        # Complete session and get profile data
        profile_data = await builder.complete_session()

        # Save to database
        if profile_data.preferences:
            await profile_service.add_preferences(profile_name, profile_data.preferences)
        if profile_data.values:
            await profile_service.add_values(profile_name, profile_data.values)
        if profile_data.personality:
            await profile_service.add_personality(profile_name, profile_data.personality)
        if profile_data.context:
            await profile_service.add_context(profile_name, profile_data.context)

        # Clean up session
        del profile_builder_sessions[session_id]

        return ProfileBuilderCompleteResponse(
            profile_name=profile_name,
            profile_data=profile_data.to_dict(),
            summary=f"Profile built with {len(profile_data.preferences)} preferences, {len(profile_data.values)} values, {len(profile_data.personality)} personality traits, and {len(profile_data.context)} context items",
        )

    @app.delete("/profile-builder/{session_id}", tags=["Profile Builder"])
    async def cancel_profile_builder(session_id: str) -> dict[str, str]:
        """Cancel a profile builder session.

        Args:
            session_id: The session ID.

        Returns:
            dict: Success message.
        """
        if session_id not in profile_builder_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        del profile_builder_sessions[session_id]

        return {"message": "Session cancelled"}


# Create the app instance
app = create_app()
