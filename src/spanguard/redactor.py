"""The Redactor: run recognizers, resolve overlaps, transform, audit."""

from __future__ import annotations

from spanguard._overlap import resolve_overlaps
from spanguard._transform import apply_spans
from spanguard.policy import Policy
from spanguard.recognizers.base import Recognizer
from spanguard.recognizers.regex_recognizers import DEFAULT_RECOGNIZERS
from spanguard.result import AuditRecord, RedactionResult, Span

# Separator characters some regex recognizers may greedily over-consume at a
# span boundary (e.g. a trailing " " or "-" after the last digit of a
# candidate number). Trimming defends the audit/transform layer against a
# recognizer reporting a span that is one character wider than the entity.
_BOUNDARY_SEPARATORS = " -"


def _trim_separators(span: Span, text: str) -> Span:
    """Shrink `span` so it never starts/ends on a boundary separator char.

    Recognizers are expected to return exactly the entity's extent, but a
    regex with an optional trailing separator inside a repeated group (as
    used for credit-card digit runs) can match one extra trailing/leading
    separator when it happens to sit next to word boundaries. Trimming here
    keeps the redaction/audit guarantees intact regardless of recognizer
    implementation quirks.
    """
    start, end = span.start, span.end
    while end > start and text[end - 1] in _BOUNDARY_SEPARATORS:
        end -= 1
    while start < end and text[start] in _BOUNDARY_SEPARATORS:
        start += 1
    if start == span.start and end == span.end:
        return span
    return Span(type=span.type, start=start, end=end)


class Redactor:
    """Detect and redact PII/PHI in text according to a `Policy`."""

    def __init__(
        self, policy: Policy, recognizers: list[Recognizer] | None = None
    ) -> None:
        self.policy = policy
        if recognizers is None:
            recognizers = [
                DEFAULT_RECOGNIZERS[e]  # type: ignore[misc]
                for e in policy.entities
                if e in DEFAULT_RECOGNIZERS
            ]
        self.recognizers = recognizers

    def _detect(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for rec in self.recognizers:
            spans.extend(_trim_separators(s, text) for s in rec.recognize(text))
        return resolve_overlaps(spans)

    def redact(self, text: str) -> RedactionResult:
        spans = self._detect(text)
        redacted = apply_spans(
            text, spans, mode=self.policy.mode, mask_char=self.policy.mask_char
        )
        audit = AuditRecord.from_spans(spans, policy_hash=self.policy.policy_hash())
        return RedactionResult(text=redacted, spans=spans, audit=audit)
