"""The Redactor: run recognizers, resolve overlaps, transform, audit."""

from __future__ import annotations

from spanguard._keys import resolve_key
from spanguard._overlap import resolve_overlaps
from spanguard._transform import apply_spans
from spanguard.policy import Policy
from spanguard.recognizers.base import Recognizer
from spanguard.recognizers.regex_recognizers import DEFAULT_RECOGNIZERS
from spanguard.result import AuditRecord, RedactionResult, Span
from spanguard.tokenize import Keyring, hmac_digest


class Redactor:
    """Detect and redact PII/PHI in text according to a `Policy`."""

    def __init__(
        self,
        policy: Policy,
        recognizers: list[Recognizer] | None = None,
        *,
        hmac_key: bytes | None = None,
        tokenize_key: bytes | None = None,
    ) -> None:
        self.policy = policy
        if recognizers is None:
            recognizers = [
                DEFAULT_RECOGNIZERS[e]  # type: ignore[misc]
                for e in policy.entities
                if e in DEFAULT_RECOGNIZERS
            ]
        self.recognizers = recognizers
        self._hmac_key_arg = hmac_key
        self._tokenize_key_arg = tokenize_key
        self._hmac_key_cached: bytes | None = None
        self._keyring_cached: Keyring | None = None

    @property
    def _hmac_key(self) -> bytes:
        if self._hmac_key_cached is None:
            self._hmac_key_cached = resolve_key(self._hmac_key_arg, "SPANGUARD_HMAC_KEY")
        return self._hmac_key_cached

    @property
    def keyring(self) -> Keyring:
        if self._keyring_cached is None:
            self._keyring_cached = Keyring(
                resolve_key(self._tokenize_key_arg, "SPANGUARD_TOKENIZE_KEY")
            )
        return self._keyring_cached

    def _detect(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for rec in self.recognizers:
            spans.extend(rec.recognize(text))
        return resolve_overlaps(spans)

    def _replace_raw(self, span: Span, raw: str) -> str:
        if self.policy.mode == "hash":
            return f"[{span.type}:{hmac_digest(self._hmac_key, span.type, raw)}]"
        if self.policy.mode == "tokenize":
            return self.keyring.tokenize(span.type, raw)
        raise ValueError(f"no raw replacement for mode {self.policy.mode!r}")

    def redact(self, text: str) -> RedactionResult:
        spans = self._detect(text)
        redacted = apply_spans(
            text,
            spans,
            mode=self.policy.mode,
            mask_char=self.policy.mask_char,
            replace_raw=self._replace_raw,
        )
        audit = AuditRecord.from_spans(spans, policy_hash=self.policy.policy_hash())
        return RedactionResult(text=redacted, spans=spans, audit=audit)

    def reveal(self, text: str, keyring: Keyring | None = None) -> str:
        """Restore tokenized values using `keyring` (defaults to this Redactor's)."""
        return (keyring or self.keyring).reveal(text)
