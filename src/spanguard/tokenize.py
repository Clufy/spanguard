"""Deterministic HMAC hashing and reversible tokenization with a keyring."""

from __future__ import annotations

import hmac
import re
from hashlib import sha256

_DIGEST_LEN = 16
_TOKEN_SHAPE = re.compile("⟦[^⟦⟧]*⟧")


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
        # Set when a label contains a token bracket, which defeats the
        # bracket-delimited fast path in reveal().
        self._bracketed_label = False
        self._alternation: re.Pattern[str] | None = None

    def tokenize(self, entity_type: str, raw: str) -> str:
        digest = hmac_digest(self._key, entity_type, raw)
        token = make_token(entity_type, digest)
        if token not in self._map:
            self._alternation = None
            if "⟦" in entity_type or "⟧" in entity_type:
                self._bracketed_label = True
        self._map[token] = raw
        return token

    def reveal_token(self, token: str) -> str | None:
        return self._map.get(token)

    def reveal(self, text: str) -> str:
        """Replace every token this keyring issued with its original value.

        Substitution is a single left-to-right pass (one re.sub over an
        alternation of all issued tokens), so a raw value that happens to
        contain another issued token's string is never re-expanded.
        """
        if not self._map:
            return text
        if not self._bracketed_label:
            # Every issued token is ⟦...⟧ with no inner brackets, so scanning
            # bracket-delimited candidates and looking each up is equivalent
            # to the alternation below, in O(len(text)) regardless of map size.
            return _TOKEN_SHAPE.sub(lambda m: self._map.get(m[0], m[0]), text)
        if self._alternation is None:
            self._alternation = re.compile("|".join(re.escape(tok) for tok in self._map))
        return self._alternation.sub(lambda m: self._map[m[0]], text)

    @property
    def tokens(self) -> frozenset[str]:
        return frozenset(self._map)

    def __repr__(self) -> str:
        return f"Keyring(tokens={len(self._map)})"
