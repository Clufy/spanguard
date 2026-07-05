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
