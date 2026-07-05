"""spanguard: detect and redact PII/PHI with leak-free audit records."""

from spanguard.policy import Policy
from spanguard.recognizers.base import Recognizer
from spanguard.redactor import Redactor
from spanguard.result import AuditRecord, RedactionResult, Span

__version__ = "0.1.0"
__all__ = [
    "AuditRecord",
    "Policy",
    "Recognizer",
    "RedactionResult",
    "Redactor",
    "Span",
]
