"""Redaction policy: what to detect and how to transform it."""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict

RedactionMode = Literal["mask", "placeholder", "hash", "tokenize"]

DEFAULT_ENTITIES: list[str] = [
    "EMAIL",
    "PHONE",
    "SSN",
    "MRN",
    "DOB",
    "CREDIT_CARD",
    "API_KEY",
]


class Policy(BaseModel):
    """Immutable, serializable redaction policy."""

    model_config = ConfigDict(frozen=True)

    mode: RedactionMode = "mask"
    entities: list[str] = DEFAULT_ENTITIES
    mask_char: str = "█"

    def policy_hash(self) -> str:
        """Stable content-addressed hash of the policy for the audit record."""
        canonical = self.model_dump_json()
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
