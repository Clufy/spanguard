"""Deterministic HMAC hashing and reversible tokenization with a keyring."""

from __future__ import annotations

import hmac
from hashlib import sha256

_DIGEST_LEN = 16


def hmac_digest(key: bytes, entity_type: str, raw: str) -> str:
    """Deterministic HMAC-SHA256 digest (first 16 hex chars) over type:raw."""
    msg = f"{entity_type}:{raw}".encode()
    return hmac.new(key, msg, sha256).hexdigest()[:_DIGEST_LEN]


def make_token(entity_type: str, digest: str) -> str:
    """Stable token wrapper for a digest."""
    return f"⟦{entity_type}_{digest}⟧"


class Keyring:
    """Holds the tokenize key and an in-memory token->raw map for reveal().

    The key and the map are never exposed via repr/str, so a Keyring can be
    logged without leaking secrets or raw values.
    """

    def __init__(self, tokenize_key: bytes) -> None:
        self._key = tokenize_key
        self._map: dict[str, str] = {}

    def tokenize(self, entity_type: str, raw: str) -> str:
        digest = hmac_digest(self._key, entity_type, raw)
        token = make_token(entity_type, digest)
        self._map[token] = raw
        return token

    def reveal_token(self, token: str) -> str | None:
        return self._map.get(token)

    def reveal(self, text: str) -> str:
        """Replace every token this keyring issued with its original value."""
        result = text
        for token, raw in self._map.items():
            result = result.replace(token, raw)
        return result

    @property
    def tokens(self) -> frozenset[str]:
        return frozenset(self._map)

    def __repr__(self) -> str:
        return f"Keyring(tokens={len(self._map)})"
