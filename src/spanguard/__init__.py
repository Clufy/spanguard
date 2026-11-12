"""spanguard: detect and redact PII/PHI with leak-free audit records."""

from spanguard.policy import Policy
from spanguard.recognizers.base import Recognizer
from spanguard.redactor import Redactor
from spanguard.result import AuditRecord, RedactionResult, Span
from spanguard.streaming import StreamBufferFullError, StreamRedactor
from spanguard.tokenize import Keyring

__version__ = "0.1.0"
__all__ = [
    "AuditRecord",
    "Keyring",
    "Policy",
    "Recognizer",
    "RedactionResult",
    "Redactor",
    "Span",
    "StreamBufferFullError",
    "StreamRedactor",
]
