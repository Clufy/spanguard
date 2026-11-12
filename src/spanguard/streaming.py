"""Chunked streaming redaction that preserves entities across chunk boundaries."""

from __future__ import annotations

import re

from spanguard.redactor import Redactor
from spanguard.result import Span

_DEFAULT_TAIL = 128
_MIN_TAIL = 64
_WHITESPACE = re.compile(r"\s")


class StreamRedactor:
    """Redact a text arriving in chunks, holding back a tail so an entity split
    across a boundary is still redacted as one.

    Guarantee: for any chunking, the concatenation of all ``feed()`` outputs
    plus ``flush()`` equals ``redactor.redact(full_text).text`` -- for every
    mode (mask, placeholder, hash, tokenize) with the same keys. Memory is
    bounded by ``tail`` plus one chunk. ``tail`` must be >= ``_MIN_TAIL`` (64),
    which is enforced. An entity longer than ``tail`` with no internal
    separators (e.g. an email or an API key) degrades gracefully to a
    word-boundary split. The floor exists specifically to prevent a
    sub-threshold leak of entities that DO contain internal separators (e.g.
    a spaced credit card number): below the floor, the buffer never holds
    enough of the entity for detection to fire, so every whitespace cut looks
    safe and the raw value streams out unmasked in pieces.
    """

    def __init__(self, redactor: Redactor, tail: int = _DEFAULT_TAIL) -> None:
        if tail < _MIN_TAIL:
            raise ValueError(
                f"tail must be >= {_MIN_TAIL} to guarantee no raw value leaks; "
                f"a smaller tail can let a multi-token entity (e.g. a credit card) "
                f"stream out in sub-threshold pieces that never match. Got tail={tail}."
            )
        self._redactor = redactor
        self._tail = tail
        self._buffer = ""
        self._ws_free_upto = 0  # buffer[:_ws_free_upto] has no whitespace

    @property
    def pending(self) -> int:
        return len(self._buffer)

    def _safe_cut(self) -> tuple[int, list[Span]]:
        """Largest separator index that provably reproduces the one-shot result.

        A cut at ``c`` (just after a whitespace char, ``c <= len - tail``) is
        safe iff detecting the prefix ``buffer[:c]`` yields exactly the
        whole-buffer spans ending at or before ``c``, AND detecting the suffix
        ``buffer[c:]`` yields exactly the whole-buffer spans starting at or
        after ``c`` (offsets shifted by ``-c``). This behavioral check -- not a
        positional guess -- is what makes "split == whole" hold even for
        entities that contain internal separators or need left context.

        Returns ``(cut, prefix_spans)`` -- the verified detection result for
        ``buffer[:cut]``, so the caller can emit without re-detecting -- or
        ``(0, [])`` when no cut is safe yet (nothing may be emitted).
        """
        buffer = self._buffer
        limit = len(buffer) - self._tail
        # Cut points sit just after a whitespace char, latest first. `\s` is
        # exactly str.isspace(); the C-level scan keeps whitespace-free
        # streams cheap.
        # The buffer only grows between cuts, so the known whitespace-free
        # prefix is never rescanned: a separator-free stream costs O(n) total.
        limit = max(limit, 0)
        if _WHITESPACE.search(buffer, self._ws_free_upto, limit) is None:
            self._ws_free_upto = limit
            return 0, []  # no cut candidate: skip detection entirely
        candidates = [m.end() for m in _WHITESPACE.finditer(buffer, 0, limit)][::-1]
        full = self._redactor._detect(buffer)
        # ponytail: ~O(tail^2 * recognizers) worst case — re-detects prefix and
        # suffix per candidate separator; in practice the first candidate that
        # no span straddles is accepted, so a feed costs ~3 detection passes.
        for c in candidates:
            if any(s.start < c < s.end for s in full):
                continue  # a span straddles this cut
            pre_expected = [s for s in full if s.end <= c]
            suf_expected = [Span(s.type, s.start - c, s.end - c) for s in full if s.start >= c]
            if self._redactor._detect(buffer[:c]) != pre_expected:
                continue
            if self._redactor._detect(buffer[c:]) != suf_expected:
                continue
            return c, pre_expected
        return 0, []

    def feed(self, chunk: str) -> str:
        self._buffer += chunk
        cut, spans = self._safe_cut()
        if cut == 0:
            return ""
        emit_src = self._buffer[:cut]
        self._buffer = self._buffer[cut:]
        self._ws_free_upto = 0
        return self._redactor._redact_with_spans(emit_src, spans).text

    def flush(self) -> str:
        if not self._buffer:
            return ""
        out = self._redactor.redact(self._buffer).text
        self._buffer = ""
        self._ws_free_upto = 0
        return out
