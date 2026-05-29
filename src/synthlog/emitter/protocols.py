"""Emitter protocol and plugin loader."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from synthlog.emitter.console import ConsoleEmitter
from synthlog.emitter.jsonl import JSONLEmitter
from synthlog.engine.protocols import Emitter

_BUILTIN: dict[str, type[Any]] = {
    "jsonl": JSONLEmitter,
    "console": ConsoleEmitter,
}


def load_emitter(name: str, **kwargs: Any) -> Emitter:
    """Load an emitter by name.

    Built-in: jsonl, console.
    External (via entry points): kafka, splunk, etc.
    """
    if name in _BUILTIN:
        return _BUILTIN[name](**kwargs)  # type: ignore[no-any-return]

    eps = entry_points(group="synthlog.emitters")
    for ep in eps:
        if ep.name == name:
            cls = ep.load()
            return cls(**kwargs)  # type: ignore[no-any-return]

    available = list(_BUILTIN) + [ep.name for ep in eps]
    msg = f"Unknown emitter: {name!r}. Available: {available}"
    raise ValueError(msg)


def create_emitter(name: str, output_path: Path | None = None) -> Emitter:
    """Convenience factory used by the CLI."""
    if name == "jsonl":
        path = output_path or Path("output/events.jsonl")
        return load_emitter("jsonl", path=path)
    return load_emitter(name)
