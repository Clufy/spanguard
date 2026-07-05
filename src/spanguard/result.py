"""Value types for redaction results and leak-free audit records."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class Span:
    """A detected sensitive region: entity `type` over half-open [start, end).

    `type` is a fixed entity label (e.g. ``"EMAIL"``), never the matched
    value — it appears verbatim in the audit record's ``counts`` and in
    placeholder output.
    """

    type: str
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Per-operation audit trail. Contains counts only — never raw values."""

    counts: dict[str, int]
    policy_hash: str
    ts: str

    @classmethod
    def from_spans(cls, spans: list[Span], policy_hash: str) -> AuditRecord:
        counts = dict(Counter(s.type for s in spans))
        ts = datetime.now(UTC).isoformat()
        return cls(counts=counts, policy_hash=policy_hash, ts=ts)


@dataclass(frozen=True, slots=True)
class RedactionResult:
    """Result of a redaction: transformed `text`, the `spans`, and `audit`."""

    text: str
    spans: list[Span] = field(default_factory=list)
    audit: AuditRecord | None = None
