"""Tests for JSONL emitter."""

import json
from datetime import UTC, datetime
from pathlib import Path
from random import Random

from synthlog.emitter.jsonl import JSONLEmitter
from synthlog.engine.event_builder import EventBuilder
from synthlog.entities import EntityFactory
from synthlog.schema import LogEvent


class TestJSONLEmitter:
    def test_writes_valid_jsonl(self, tmp_path: Path) -> None:
        out = tmp_path / "events.jsonl"
        emitter = JSONLEmitter(path=out)

        pool = EntityFactory(seed=42).create_pool(num_users=3)
        builder = EventBuilder(Random(42))
        user = pool.users[0]
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        for i in range(5):
            event = builder.build(
                "user.session.start",
                ts,
                user,
                targets=[user],
            )
            emitter.emit(event)

        emitter.close()

        lines = out.read_text().strip().split("\n")
        assert len(lines) == 5

        for line in lines:
            data = json.loads(line)
            assert "eventType" in data
            assert data["eventType"] == "user.session.start"

    def test_roundtrip_via_pydantic(self, tmp_path: Path) -> None:
        out = tmp_path / "events.jsonl"
        emitter = JSONLEmitter(path=out)

        pool = EntityFactory(seed=42).create_pool(num_users=3)
        builder = EventBuilder(Random(42))
        user = pool.users[0]
        net = pool.get_network(user.primary_network_id)
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        original = builder.build(
            "user.session.start", ts, user,
            network=net, targets=[user],
        )
        emitter.emit(original)
        emitter.close()

        line = out.read_text().strip()
        restored = LogEvent.model_validate_json(line)
        assert restored.uuid == original.uuid
        assert restored.event_type == original.event_type
        assert restored.actor.id == original.actor.id

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "dir" / "events.jsonl"
        emitter = JSONLEmitter(path=out)
        emitter.close()
        assert out.parent.exists()

    def test_plugin_loader_finds_builtin(self) -> None:
        from synthlog.emitter.protocols import load_emitter
        try:
            load_emitter("nonexistent")
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "nonexistent" in str(e)

    def test_plugin_loader_jsonl(self, tmp_path: Path) -> None:
        from synthlog.emitter.protocols import load_emitter
        emitter = load_emitter("jsonl", path=tmp_path / "test.jsonl")
        assert hasattr(emitter, "emit")
        emitter.close()  # type: ignore[attr-defined]
