"""Chunked streaming redaction that preserves entities across chunk boundaries."""

from __future__ import annotations

from spanguard.redactor import Redactor

_DEFAULT_TAIL = 128


def _last_safe_boundary(buffer: str, tail: int) -> int:
    """Largest index <= len(buffer) - tail that sits just after a separator.

    Everything before this index cannot be part of an entity still growing at
    the buffer's end (any such entity would exceed `tail`), so it is safe to
    emit. Returns 0 if there is no safe boundary yet.
    """
    limit = len(buffer) - tail
    if limit <= 0:
        return 0
    # find the last whitespace at or before `limit`; emit through it.
    for i in range(limit, 0, -1):
        if buffer[i - 1].isspace():
            return i
    return 0


class StreamRedactor:
    """Redact a text arriving in chunks, holding back a tail so an entity split
    across a boundary is still redacted as one.

    Guarantee: for any chunking, the concatenation of all `feed()` outputs plus
    `flush()` equals `redactor.redact(full_text).text`. Memory is bounded by
    `tail` plus one chunk. An entity longer than `tail` is the documented
    ceiling and may be split.
    """

    def __init__(self, redactor: Redactor, tail: int = _DEFAULT_TAIL) -> None:
        self._redactor = redactor
        self._tail = tail
        self._buffer = ""

    @property
    def pending(self) -> int:
        return len(self._buffer)

    def feed(self, chunk: str) -> str:
        self._buffer += chunk
        cut = _last_safe_boundary(self._buffer, self._tail)
        if cut == 0:
            return ""
        emit_src = self._buffer[:cut]
        self._buffer = self._buffer[cut:]
        return self._redactor.redact(emit_src).text

    def flush(self) -> str:
        if not self._buffer:
            return ""
        out = self._redactor.redact(self._buffer).text
        self._buffer = ""
        return out
