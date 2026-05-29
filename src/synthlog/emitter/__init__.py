"""Emitter layer — pluggable event sinks."""

from synthlog.emitter.console import ConsoleEmitter
from synthlog.emitter.jsonl import JSONLEmitter
from synthlog.emitter.protocols import create_emitter, load_emitter

__all__ = [
    "ConsoleEmitter",
    "JSONLEmitter",
    "create_emitter",
    "load_emitter",
]
