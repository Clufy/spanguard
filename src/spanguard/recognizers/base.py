"""The Recognizer protocol: pluggable detectors."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from spanguard.result import Span


@runtime_checkable
class Recognizer(Protocol):
    """A detector for one entity type. Users implement this to add detectors."""

    entity_type: str

    def recognize(self, text: str) -> list[Span]:
        """Return non-overlapping spans of `entity_type` found in `text`."""
        ...
