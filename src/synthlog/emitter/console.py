"""Console emitter — Rich-formatted table output for development."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from synthlog.schema.log_event import LogEvent


class ConsoleEmitter:
    def __init__(self) -> None:
        self._console = Console()
        self._count = 0

    def emit(self, event: LogEvent) -> None:
        self._count += 1
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="dim", width=5)
        table.add_column(width=30)
        table.add_row("Time", str(event.published))
        table.add_row("Type", f"[bold]{event.event_type}[/bold]")
        table.add_row("Actor", f"{event.actor.display_name} ({event.actor.alternate_id})")
        table.add_row("Result", self._style_outcome(event.outcome.result))
        if event.target:
            targets = ", ".join(
                f"{t.display_name} ({t.type})" for t in event.target
            )
            table.add_row("Target", targets)
        if event.client.ip_address:
            table.add_row("IP", event.client.ip_address)
        self._console.print(table)
        self._console.print()

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self._console.print(f"[dim]Total events: {self._count}[/dim]")

    @staticmethod
    def _style_outcome(result: str) -> str:
        styles = {
            "SUCCESS": "[green]SUCCESS[/green]",
            "FAILURE": "[red]FAILURE[/red]",
            "DENY": "[red]DENY[/red]",
            "WARN": "[yellow]WARN[/yellow]",
            "CHALLENGE": "[yellow]CHALLENGE[/yellow]",
        }
        return styles.get(result, result)
