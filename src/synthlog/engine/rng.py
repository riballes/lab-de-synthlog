"""Seeded RNG manager for deterministic generation."""

from __future__ import annotations

from random import Random


class SeededRNG:
    def __init__(self, seed: int = 42) -> None:
        self._seed = seed
        self._root = Random(seed)
        self._children: dict[str, Random] = {}

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def root(self) -> Random:
        return self._root

    def child(self, name: str) -> Random:
        if name not in self._children:
            child_seed = self._root.randint(0, 2**63)
            self._children[name] = Random(child_seed)
        return self._children[name]
