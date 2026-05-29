"""CLI entry point for synthlog."""

from pathlib import Path
from random import Random

import typer
from rich.console import Console

from synthlog.clock import VirtualClock
from synthlog.emitter.protocols import create_emitter
from synthlog.engine.baseline import BaselineTraffic
from synthlog.engine.event_builder import EVENT_TYPE_REGISTRY
from synthlog.engine.protocols import Scenario
from synthlog.engine.scenario_loader import ScenarioLoader
from synthlog.engine.scheduler import EventScheduler
from synthlog.entities import EntityFactory

app = typer.Typer(name="synthlog", help="Synthetic identity provider log generator")
console = Console()


def _load_scenarios(scenario: list[str]) -> list[Scenario]:
    scenarios: list[Scenario] = [BaselineTraffic()]
    for s in scenario:
        path = Path(s)
        if path.exists() and path.suffix in (".yaml", ".yml"):
            scenarios.append(ScenarioLoader.load(path))
        else:
            scenarios.append(ScenarioLoader.load_builtin(s))
    return scenarios


@app.command()
def generate(
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed"),
    users: int = typer.Option(5, "--users", "-u", help="Number of synthetic users"),
    duration: int = typer.Option(8, "--duration", "-d", help="Hours of simulated time"),
    output: Path = typer.Option(
        "output/events.jsonl", "--output", "-o", help="Output file path"
    ),
    emitter_name: str = typer.Option(
        "jsonl", "--emitter", "-e", help="Emitter name (jsonl, console)"
    ),
    scenario: list[str] = typer.Option(
        [], "--scenario", help="Builtin scenario names or YAML file paths"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Generate synthetic log events in batch mode."""
    rng = Random(seed)
    pool = EntityFactory(seed=seed).create_pool(num_users=users)
    clock = VirtualClock.for_duration(duration_hours=duration)
    scenarios = _load_scenarios(scenario)

    emitter = create_emitter(emitter_name, output_path=output)
    scheduler = EventScheduler(scenarios, pool, clock, rng)

    if verbose:
        console.print(
            f"[bold]synthlog[/bold] generating {duration}h for {users} users "
            f"(seed={seed}, emitter={emitter_name})"
        )

    count = scheduler.run(emitter)
    emitter.close()

    console.print(f"[green]Done.[/green] {count} events written to {output}")


@app.command()
def stream(
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed"),
    users: int = typer.Option(5, "--users", "-u", help="Number of synthetic users"),
    duration: int = typer.Option(8, "--duration", "-d", help="Hours of simulated time"),
    speed: float = typer.Option(60.0, "--speed", help="Clock speed multiplier"),
    emitter_name: str = typer.Option(
        "console", "--emitter", "-e", help="Emitter name"
    ),
    output: Path = typer.Option(
        "output/events.jsonl", "--output", "-o", help="Output file (for jsonl)"
    ),
    scenario: list[str] = typer.Option(
        [], "--scenario", help="Builtin scenario names or YAML file paths"
    ),
) -> None:
    """Stream synthetic log events in real-time (paced by clock speed)."""
    from synthlog.engine.streaming import StreamingScheduler

    rng = Random(seed)
    pool = EntityFactory(seed=seed).create_pool(num_users=users)
    clock = VirtualClock.for_duration(duration_hours=duration, speed=speed)
    scenarios = _load_scenarios(scenario)

    emitter = create_emitter(emitter_name, output_path=output)

    console.print(
        f"[bold]synthlog stream[/bold] {duration}h at {speed}x speed "
        f"for {users} users (seed={seed})"
    )
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    scheduler = StreamingScheduler(scenarios, pool, clock, rng)
    try:
        count = scheduler.run_sync(emitter=emitter)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
        count = 0

    emitter.close()
    if count:
        console.print(f"[green]Done.[/green] {count} events streamed")


@app.command()
def serve(
    port: int = typer.Option(8080, "--port", "-p", help="HTTP server port"),
    host: str = typer.Option("0.0.0.0", "--host", help="Bind address"),
) -> None:
    """Start the REST API server."""
    import uvicorn

    from synthlog.api.app import create_app

    console.print(f"[bold]synthlog API[/bold] starting on {host}:{port}")
    console.print("[dim]Docs at http://localhost:{port}/docs[/dim]")

    api_app = create_app()
    uvicorn.run(api_app, host=host, port=port)


@app.command(name="init-pool")
def init_pool(
    output: Path = typer.Option(
        "pool.json", "--output", "-o", help="Output pool file"
    ),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed"),
    users: int = typer.Option(5, "--users", "-u", help="Number of users"),
) -> None:
    """Generate and persist a synthetic entity pool."""
    pool = EntityFactory(seed=seed).create_pool(num_users=users)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(pool.to_json())
    console.print(f"[green]Pool saved:[/green] {users} users -> {output}")


@app.command(name="list-events")
def list_events() -> None:
    """Print all supported event types."""
    console.print("[bold]Supported event types:[/bold]")
    for name, meta in sorted(EVENT_TYPE_REGISTRY.items()):
        console.print(
            f"  {name:40s} {meta.severity:5s}  {meta.display_message}"
        )
