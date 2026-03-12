"""CLI module for MooAId."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mooaid.config import Config, ConfigManager, get_config, load_config
from mooaid.core.opinion_engine import OpinionEngine
from mooaid.core.provider_factory import ProviderFactory, get_provider
from mooaid.profile import DatabaseManager, ProfileData
from mooaid.profile.service import ProfileService

app = typer.Typer(
    name="mooaid",
    help="MooAId - My Opinion AI Daemon: Predicts what your opinion would likely be",
    add_completion=False,
)
console = Console()


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create event loop for async operations."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def init_services(config: Config) -> tuple[DatabaseManager, ProfileService]:
    """Initialize database and profile services.

    Args:
        config: The application configuration.

    Returns:
        tuple: (db_manager, profile_service)
    """
    db = DatabaseManager(config.database.path)
    asyncio.get_event_loop().run_until_complete(db.init_db())
    service = ProfileService(db)
    return db, service


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold blue]MooAId[/bold blue] v0.1.0")
    console.print("My Opinion AI Daemon")


@app.command()
def serve(
    host: Annotated[
        str | None, typer.Option("--host", "-h", help="Host to bind to")
    ] = None,
    port: Annotated[
        int | None, typer.Option("--port", "-p", help="Port to bind to")
    ] = None,
    reload: Annotated[
        bool, typer.Option("--reload", help="Enable auto-reload")
    ] = False,
) -> None:
    """Start the REST API server."""
    import uvicorn

    config = get_config()

    host = host or config.api.host
    port = port or config.api.port

    console.print(Panel.fit(
        "[bold blue]Starting MooAId API Server[/bold blue]\n\n"
        f"Host: [cyan]{host}[/cyan]\n"
        f"Port: [cyan]{port}[/cyan]\n"
        f"Provider: [cyan]{config.provider}[/cyan]\n\n"
        f"Docs: [link=http://{host}:{port}/docs]http://{host}:{port}/docs[/link]",
        title="MooAId",
    ))

    uvicorn.run(
        "mooaid.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.group()
def opinion() -> None:
    """Opinion prediction commands."""
    pass


@opinion.command()
def ask(
    question: Annotated[str, typer.Argument(help="The question to ask")],
    profile: Annotated[
        str | None, typer.Option("--profile", "-p", help="Profile to use")
    ] = None,
) -> None:
    """Ask MooAId for a predicted opinion."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        # Get profile
        profile_name = profile or "default"
        profile_data = loop.run_until_complete(profile_service.get_profile(profile_name))

        if profile_data is None:
            if profile_name == "default":
                console.print(
                    "[yellow]No profile found. Creating default profile...[/yellow]"
                )
                profile_data = loop.run_until_complete(
                    profile_service.create_profile(profile_name)
                )
            else:
                console.print(
                    f"[red]Profile '{profile_name}' not found.[/red]\n"
                    f"Create it with: [bold]mooaid profile create {profile_name}[/bold]"
                )
                raise typer.Exit(1)

        # Get provider and predict
        console.print(f"[dim]Thinking about your question...[/dim]\n")
        provider = get_provider(config.provider)
        engine = OpinionEngine(provider)

        result = loop.run_until_complete(
            engine.predict(question, profile_data, profile_name)
        )

        # Display result
        console.print(
            Panel(
                f"[bold]{result.predicted_opinion}[/bold]\n\n"
                f"[dim]{result.reasoning}[/dim]",
                title=f"Predicted Opinion (via {result.provider}/{result.model})",
                border_style="blue",
            )
        )

    finally:
        loop.run_until_complete(db.close())


@app.group()
def profile() -> None:
    """Profile management commands."""
    pass


@profile.command("list")
def list_profiles() -> None:
    """List all profiles."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        profiles = loop.run_until_complete(profile_service.list_profiles())

        if not profiles:
            console.print("[yellow]No profiles found.[/yellow]")
            console.print("\nCreate one with: [bold]mooaid profile create <name>[/bold]")
            return

        table = Table(title="Profiles")
        table.add_column("Name", style="cyan")

        for name in profiles:
            table.add_row(name)

        console.print(table)

    finally:
        loop.run_until_complete(db.close())


@profile.command("create")
def create_profile(
    name: Annotated[str, typer.Argument(help="Profile name")],
) -> None:
    """Create a new profile."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        profile = loop.run_until_complete(profile_service.create_profile(name))
        console.print(f"[green]✓ Profile '{name}' created successfully![/green]")
        console.print("\nAdd traits with:")
        console.print(f"  [bold]mooaid profile add preferences \"likes open source\"[/bold]")
        console.print(f"  [bold]mooaid profile add values \"privacy\"[/bold]")
        console.print(f"  [bold]mooaid profile add personality \"analytical\"[/bold]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        loop.run_until_complete(db.close())


@profile.command("show")
def show_profile(
    name: Annotated[str, typer.Argument(help="Profile name")],
) -> None:
    """Show a profile's details."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        profile = loop.run_until_complete(profile_service.get_profile(name))

        if profile is None:
            console.print(f"[red]Profile '{name}' not found.[/red]")
            raise typer.Exit(1)

        table = Table(title=f"Profile: {name}")
        table.add_column("Field", style="cyan")
        table.add_column("Values", style="white")

        if profile.preferences:
            table.add_row("Preferences", "\n".join(f"• {p}" for p in profile.preferences))
        if profile.values:
            table.add_row("Values", "\n".join(f"• {v}" for v in profile.values))
        if profile.personality:
            table.add_row("Personality", "\n".join(f"• {p}" for p in profile.personality))
        if profile.context:
            table.add_row("Context", "\n".join(f"• {c}" for c in profile.context))

        if not any([profile.preferences, profile.values, profile.personality, profile.context]):
            table.add_row("", "[dim]No traits added yet[/dim]")

        console.print(table)

    finally:
        loop.run_until_complete(db.close())


@profile.command("add")
def add_to_profile(
    field: Annotated[
        str, typer.Argument(help="Field to add to (preferences, values, personality, context)")
    ],
    items: Annotated[
        list[str], typer.Argument(help="Items to add")
    ],
    profile: Annotated[
        str | None, typer.Option("--profile", "-p", help="Profile to update")
    ] = None,
) -> None:
    """Add items to a profile field."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        profile_name = profile or "default"
        valid_fields = ["preferences", "values", "personality", "context"]

        if field not in valid_fields:
            console.print(
                f"[red]Invalid field '{field}'.[/red]\n"
                f"Valid fields: [cyan]{', '.join(valid_fields)}[/cyan]"
            )
            raise typer.Exit(1)

        # Create default profile if needed
        existing = loop.run_until_complete(profile_service.get_profile(profile_name))
        if existing is None:
            if profile_name == "default":
                console.print(
                    "[yellow]Creating default profile...[/yellow]"
                )
                loop.run_until_complete(profile_service.create_profile(profile_name))
            else:
                console.print(f"[red]Profile '{profile_name}' not found.[/red]")
                raise typer.Exit(1)

        add_method = getattr(profile_service, f"add_{field}")
        updated = loop.run_until_complete(add_method(profile_name, items))

        console.print(
            f"[green]✓ Added {len(items)} item(s) to '{field}' in profile '{profile_name}'[/green]"
        )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        loop.run_until_complete(db.close())


@profile.command("remove")
def remove_from_profile(
    field: Annotated[
        str, typer.Argument(help="Field to remove from")
    ],
    items: Annotated[
        list[str], typer.Argument(help="Items to remove")
    ],
    profile: Annotated[
        str | None, typer.Option("--profile", "-p", help="Profile to update")
    ] = None,
) -> None:
    """Remove items from a profile field."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        profile_name = profile or "default"
        valid_fields = ["preferences", "values", "personality", "context"]

        if field not in valid_fields:
            console.print(
                f"[red]Invalid field '{field}'.[/red]\n"
                f"Valid fields: [cyan]{', '.join(valid_fields)}[/cyan]"
            )
            raise typer.Exit(1)

        remove_method = getattr(profile_service, f"remove_{field}")
        updated = loop.run_until_complete(remove_method(profile_name, items))

        console.print(
            f"[green]✓ Removed {len(items)} item(s) from '{field}' in profile '{profile_name}'[/green]"
        )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        loop.run_until_complete(db.close())


@profile.command("delete")
def delete_profile(
    name: Annotated[str, typer.Argument(help="Profile name to delete")],
) -> None:
    """Delete a profile."""
    loop = asyncio.get_event_loop()
    config = get_config()
    db, profile_service = init_services(config)

    try:
        deleted = loop.run_until_complete(profile_service.delete_profile(name))

        if deleted:
            console.print(f"[green]✓ Profile '{name}' deleted successfully.[/green]")
        else:
            console.print(f"[red]Profile '{name}' not found.[/red]")
            raise typer.Exit(1)

    finally:
        loop.run_until_complete(db.close())


@app.group()
def config_cmd() -> None:
    """Configuration commands."""
    pass


@config_cmd.command("show")
def show_config() -> None:
    """Show current configuration."""
    config = get_config()

    table = Table(title="MooAId Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Provider", config.provider)
    table.add_row("Database Path", config.database.path)
    table.add_row("API Host", config.api.host)
    table.add_row("API Port", str(config.api.port))
    table.add_row("Log Level", config.logging.level)

    # Provider-specific settings
    if config.provider == "openrouter":
        table.add_row("OpenRouter Model", config.openrouter.default_model)
    elif config.provider == "ollama":
        table.add_row("Ollama Host", config.ollama.host)
        table.add_row("Ollama Model", config.ollama.model)
    elif config.provider == "openai":
        table.add_row("OpenAI Model", config.openai.default_model)
    elif config.provider == "gemini":
        table.add_row("Gemini Model", config.gemini.default_model)

    console.print(table)


@config_cmd.command("provider")
def set_provider(
    provider: Annotated[
        str, typer.Argument(help="Provider to use (openrouter, ollama, openai, gemini)")
    ],
) -> None:
    """Set the default AI provider."""
    valid_providers = ProviderFactory.get_available_providers()

    if provider.lower() not in valid_providers:
        console.print(
            f"[red]Invalid provider '{provider}'.[/red]\n"
            f"Valid providers: [cyan]{', '.join(valid_providers)}[/cyan]"
        )
        raise typer.Exit(1)

    config = get_config()
    config.provider = provider.lower()
    ConfigManager.save(config)

    console.print(f"[green]✓ Default provider set to '{provider}'[/green]")


@config_cmd.command("model")
def set_model(
    model: Annotated[str, typer.Argument(help="Model name to use")],
    provider: Annotated[
        str | None, typer.Option("--provider", "-p", help="Provider to configure")
    ] = None,
) -> None:
    """Set the default model for a provider."""
    config = get_config()
    provider = provider or config.provider

    if provider == "ollama":
        config.ollama.model = model
    elif provider == "openrouter":
        config.openrouter.default_model = model
    elif provider == "openai":
        config.openai.default_model = model
    elif provider == "gemini":
        config.gemini.default_model = model
    else:
        console.print(f"[red]Unknown provider '{provider}'[/red]")
        raise typer.Exit(1)

    ConfigManager.save(config)
    console.print(f"[green]✓ Model set to '{model}' for provider '{provider}'[/green]")


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
