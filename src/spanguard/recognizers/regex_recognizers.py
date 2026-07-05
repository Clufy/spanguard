"""Regex- and checksum-based recognizers for common PII/PHI entity types."""

from __future__ import annotations

import re
from typing import ClassVar

from spanguard.result import Span

from .luhn import luhn_valid

# --- patterns -------------------------------------------------------------

_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
# NANP-style: optional +country, 3-3-4 with -, ., space, or parens on area code.
_PHONE = re.compile(
    r"(?<!\d)(?:\+\d{1,2}[ .\-]?)?(?:\(\d{3}\)|\d{3})[ .\-]\d{3}[ .\-]\d{4}(?!\d)"
)
_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_MRN = re.compile(r"\bMRN\s*:?\s*(\d{6,})\b", re.IGNORECASE)
# DOB: mm/dd/yyyy (01-12 / 01-31) or ISO yyyy-mm-dd; validated loosely by ranges.
_DOB = re.compile(
    r"(?<!\d)(?:(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(\d{4})"
    r"|(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))(?!\d)"
)
_CC_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
# API keys: known prefixes, or a long high-entropy alnum run.
_API_KEY = re.compile(
    r"\b(?:sk-[A-Za-z0-9]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|ghp_[A-Za-z0-9]{36}"
    r"|[A-Za-z0-9]{32,})\b"
)


class _RegexRecognizer:
    """Shared base: emit one Span per full-match of `pattern`."""

    entity_type: ClassVar[str]
    pattern: ClassVar[re.Pattern[str]]

    def recognize(self, text: str) -> list[Span]:
        return [
            Span(type=self.entity_type, start=m.start(), end=m.end())
            for m in self.pattern.finditer(text)
        ]


class EmailRecognizer(_RegexRecognizer):
    entity_type = "EMAIL"
    pattern = _EMAIL


class PhoneRecognizer(_RegexRecognizer):
    entity_type = "PHONE"
    pattern = _PHONE


class SSNRecognizer(_RegexRecognizer):
    entity_type = "SSN"
    pattern = _SSN


class DOBRecognizer(_RegexRecognizer):
    entity_type = "DOB"
    pattern = _DOB


class MRNRecognizer:
    """MRN needs the 'MRN' context word; redact only the digit run."""

    entity_type = "MRN"

    def recognize(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for m in _MRN.finditer(text):
            spans.append(Span(type="MRN", start=m.start(1), end=m.end(1)))
        return spans


class APIKeyRecognizer(_RegexRecognizer):
    entity_type = "API_KEY"
    pattern = _API_KEY


class CreditCardRecognizer:
    """Digit runs 13-19 long that pass Luhn after stripping separators."""

    entity_type = "CREDIT_CARD"

    def recognize(self, text: str) -> list[Span]:
        spans: list[Span] = []
        for m in _CC_CANDIDATE.finditer(text):
            digits = re.sub(r"[ -]", "", m.group())
            if 13 <= len(digits) <= 19 and luhn_valid(digits):
                spans.append(Span(type="CREDIT_CARD", start=m.start(), end=m.end()))
        return spans


DEFAULT_RECOGNIZERS: dict[str, object] = {
    "EMAIL": EmailRecognizer(),
    "PHONE": PhoneRecognizer(),
    "SSN": SSNRecognizer(),
    "MRN": MRNRecognizer(),
    "DOB": DOBRecognizer(),
    "CREDIT_CARD": CreditCardRecognizer(),
    "API_KEY": APIKeyRecognizer(),
}
