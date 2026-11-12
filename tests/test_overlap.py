from spanguard._overlap import resolve_overlaps
from spanguard.result import Span


def test_no_overlap_sorted_by_start() -> None:
    spans = [Span("EMAIL", 10, 20), Span("PHONE", 0, 5)]
    out = resolve_overlaps(spans)
    assert [(s.type, s.start) for s in out] == [("PHONE", 0), ("EMAIL", 10)]


def test_longest_span_wins() -> None:
    # A 12-char PHONE overlapping a 4-char DOB -> PHONE survives.
    spans = [Span("DOB", 5, 9), Span("PHONE", 0, 12)]
    out = resolve_overlaps(spans)
    assert [(s.type, s.start, s.end) for s in out] == [("PHONE", 0, 12)]


def test_equal_length_priority_tiebreak() -> None:
    # Same span, EMAIL (pri 1) vs SSN (pri 0) -> SSN wins.
    spans = [Span("EMAIL", 0, 11), Span("SSN", 0, 11)]
    out = resolve_overlaps(spans)
    assert [s.type for s in out] == ["SSN"]


def test_chain_of_overlaps_keeps_non_overlapping_survivors() -> None:
    # DOB[0,4) and API_KEY[12,40) do NOT overlap each other; PHONE[2,14)
    # overlaps both. API_KEY beats PHONE (longer), so PHONE is discarded.
    # DOB overlapped only the discarded PHONE, not the surviving API_KEY,
    # so DOB is an independent real detection and MUST be kept.
    spans = [
        Span("DOB", 0, 4),
        Span("PHONE", 2, 14),
        Span("API_KEY", 12, 40),
    ]
    out = resolve_overlaps(spans)
    assert [(s.type, s.start, s.end) for s in out] == [("DOB", 0, 4), ("API_KEY", 12, 40)]


def test_empty() -> None:
    assert resolve_overlaps([]) == []


def _reference_resolve(spans: list[Span]) -> list[Span]:
    """The 0.1.0 quadratic algorithm, kept verbatim as a differential oracle."""
    from spanguard._overlap import _rank

    chosen: list[Span] = []
    for span in sorted(spans, key=_rank):
        if any(span.start < c.end and c.start < span.end for c in chosen):
            continue
        chosen.append(span)
    return sorted(chosen, key=lambda s: s.start)


def test_resolve_overlaps_matches_reference_random() -> None:
    import random

    rng = random.Random(1234)
    types = ["SSN", "CREDIT_CARD", "API_KEY", "EMAIL", "PHONE", "MRN", "DOB", "PERSON", "ZIP"]
    for _ in range(2000):
        spans = []
        for _ in range(rng.randint(0, 60)):
            start = rng.randint(0, 80)
            spans.append(Span(rng.choice(types), start, start + rng.randint(0, 15)))
        assert resolve_overlaps(spans) == _reference_resolve(spans)


def test_resolve_overlaps_scales() -> None:
    import time

    spans = [Span("EMAIL", i * 10, i * 10 + 5) for i in range(50_000)]
    t0 = time.perf_counter()
    out = resolve_overlaps(spans)
    assert time.perf_counter() - t0 < 2.0
    assert len(out) == 50_000
