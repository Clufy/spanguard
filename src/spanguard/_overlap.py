"""Deterministic overlap resolution: longest-wins, priority tiebreak."""

from __future__ import annotations

from bisect import bisect_left

from spanguard.result import Span

PRIORITY: dict[str, int] = {
    "SSN": 0,
    "CREDIT_CARD": 0,
    "API_KEY": 0,
    "EMAIL": 1,
    "PHONE": 1,
    "MRN": 1,
    "DOB": 1,
    "PERSON": 2,
    "LOCATION": 2,
}
_DEFAULT_PRIORITY = 3


def _rank(span: Span) -> tuple[int, int, int]:
    """Sort key for 'best' span: longer first, then higher priority, then earlier."""
    return (-span.length, PRIORITY.get(span.type, _DEFAULT_PRIORITY), span.start)


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """Greedily keep the best span, rejecting any that overlap a chosen one.

    Best = longest; ties broken by priority (lower rank wins), then start.
    Overlap is direct/pairwise (half-open [start, end) intervals), NOT
    transitive: a span that overlaps only an already-rejected span is still
    kept. Returns the surviving spans sorted by start.
    """
    # Index the chosen non-empty spans as parallel start/end lists sorted by
    # start. They are pairwise disjoint, so their ends are sorted too, and a
    # candidate [s, e) overlaps one of them iff the last one starting before e
    # ends after s: one bisect per span, O(n log n) instead of O(n^2).
    # Empty spans rank last (shortest) and can only be followed by other empty
    # spans, which they never overlap, so they are never indexed.
    starts: list[int] = []
    ends: list[int] = []
    chosen: list[Span] = []
    for span in sorted(spans, key=_rank):
        i = bisect_left(starts, span.end)
        if i and ends[i - 1] > span.start:
            continue  # overlaps an already-chosen (better) span
        chosen.append(span)
        if span.end > span.start:
            starts.insert(i, span.start)
            ends.insert(i, span.end)
    return sorted(chosen, key=lambda s: s.start)
