"""Resolve secret keys from explicit args, env, or a fresh random fallback."""

from __future__ import annotations

import os
import secrets


def resolve_key(explicit: bytes | None, env_var: str) -> bytes:
    """Return the explicit key, else the env var's bytes, else a random key.

    The key is never logged. A random fallback is ephemeral (per process),
    which makes tokenize/hash reversible/comparable only within that process
    unless a stable key is supplied.
    """
    if explicit is not None:
        return explicit
    env = os.environ.get(env_var)
    if env:
        return env.encode()
    return secrets.token_bytes(32)
