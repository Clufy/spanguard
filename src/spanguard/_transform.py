"""Apply resolved spans to text according to the redaction mode."""

from __future__ import annotations

from collections.abc import Callable

from spanguard.result import Span

# Modes that require the raw matched text to compute their replacement.
_RAW_MODES = frozenset({"hash", "tokenize"})


def _replacement(
    span: Span,
    raw: str | None,
    mode: str,
    mask_char: str,
    replace_raw: Callable[[Span, str], str] | None,
) -> str:
    if mode == "mask":
        return mask_char * span.length
    if mode == "placeholder":
        return f"[{span.type}]"
    if mode in _RAW_MODES:
        if replace_raw is None or raw is None:  # pragma: no cover - guarded by caller
            raise ValueError(f"mode {mode!r} requires a replace_raw callback")
        return replace_raw(span, raw)
    raise NotImplementedError(f"unknown mode {mode!r}")


def apply_spans(
    text: str,
    spans: list[Span],
    mode: str,
    mask_char: str,
    replace_raw: Callable[[Span, str], str] | None = None,
) -> str:
    """Rebuild `text` with each span replaced per `mode`. Spans must not overlap.

    The raw matched slice is passed to `replace_raw` ONLY for raw-requiring
    modes (hash/tokenize); mask/placeholder never receive raw text.
    """
    if not spans:
        return text
    ordered = sorted(spans, key=lambda s: s.start)
    out: list[str] = []
    cursor = 0
    for span in ordered:
        out.append(text[cursor : span.start])
        raw = text[span.start : span.end] if mode in _RAW_MODES else None
        out.append(_replacement(span, raw, mode, mask_char, replace_raw))
        cursor = span.end
    out.append(text[cursor:])
    return "".join(out)
