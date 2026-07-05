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


def test_chain_of_overlaps_keeps_best_each_region() -> None:
    spans = [
        Span("DOB", 0, 4),
        Span("PHONE", 2, 14),   # longest, overlaps DOB and API_KEY start
        Span("API_KEY", 12, 40),
    ]
    out = resolve_overlaps(spans)
    # PHONE beats DOB (longer); API_KEY starts at 12 which PHONE covers up to 14,
    # so API_KEY (12-40) overlaps PHONE -> longest wins: API_KEY (28) > PHONE (12).
    assert [(s.type) for s in out] == ["API_KEY"]


def test_empty() -> None:
    assert resolve_overlaps([]) == []
