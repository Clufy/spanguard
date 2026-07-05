"""The Redactor: run recognizers, resolve overlaps, transform, audit."""

from __future__ import annotations

from spanguard._overlap import resolve_overlaps
from spanguard._transform import apply_spans
from spanguard.policy import Policy
from spanguard.recognizers.base import Recognizer
from spanguard.recognizers.regex_recognizers import DEFAULT_RECOGNIZERS
from spanguard.result import AuditRecord, RedactionResult, Span


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
            spans.extend(rec.recognize(text))
        return resolve_overlaps(spans)

    def redact(self, text: str) -> RedactionResult:
        spans = self._detect(text)
        redacted = apply_spans(
            text, spans, mode=self.policy.mode, mask_char=self.policy.mask_char
        )
        audit = AuditRecord.from_spans(spans, policy_hash=self.policy.policy_hash())
        return RedactionResult(text=redacted, spans=spans, audit=audit)
