"""Apply resolved spans to text according to the redaction mode."""

from __future__ import annotations

from spanguard.result import Span


def _replacement(span: Span, mode: str, mask_char: str) -> str:
    if mode == "mask":
        return mask_char * span.length
    if mode == "placeholder":
        return f"[{span.type}]"
    raise NotImplementedError(f"mode {mode!r} is not available in M1")


def apply_spans(text: str, spans: list[Span], mode: str, mask_char: str) -> str:
    """Rebuild `text` with each span replaced per `mode`. Spans must not overlap."""
    if not spans:
        return text
    ordered = sorted(spans, key=lambda s: s.start)
    out: list[str] = []
    cursor = 0
    for span in ordered:
        out.append(text[cursor:span.start])
        out.append(_replacement(span, mode, mask_char))
        cursor = span.end
    out.append(text[cursor:])
    return "".join(out)
