"""The Recognizer protocol: pluggable detectors."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from spanguard.result import Span


@runtime_checkable
class Recognizer(Protocol):
    """A detector for one entity type. Users implement this to add detectors.

    Contract: `entity_type` (and the `type` field of every `Span` returned)
    MUST be a fixed, non-sensitive entity *label* (e.g. ``"EMAIL"``,
    ``"PHONE"``), never a value derived from the matched text. The label
    appears verbatim in placeholder output (``[EMAIL]``) and as a key in the
    audit record's ``counts``; putting matched content in it would leak raw
    data into redacted output and audit records.
    """

    entity_type: str
    """Fixed entity label for this recognizer. See class contract above:
    never derive this from matched text."""

    def recognize(self, text: str) -> list[Span]:
        """Return non-overlapping spans of `entity_type` found in `text`."""
        ...
