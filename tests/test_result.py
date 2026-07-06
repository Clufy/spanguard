from spanguard.result import AuditRecord, RedactionResult, Span


def test_span_length() -> None:
    s = Span(type="EMAIL", start=4, end=10)
    assert s.length == 6


def test_span_is_frozen() -> None:
    s = Span(type="EMAIL", start=0, end=1)
    try:
        s.start = 5  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("Span should be immutable")


def test_audit_from_spans_counts_by_type() -> None:
    spans = [
        Span(type="EMAIL", start=0, end=5),
        Span(type="EMAIL", start=6, end=9),
        Span(type="PHONE", start=10, end=22),
    ]
    audit = AuditRecord.from_spans(spans, policy_hash="abc123")
    assert audit.counts == {"EMAIL": 2, "PHONE": 1}
    assert audit.policy_hash == "abc123"
    assert isinstance(audit.ts, str) and audit.ts


def test_audit_has_no_raw_value_fields() -> None:
    # The audit record must not expose raw text or offsets tied to content.
    audit = AuditRecord.from_spans([Span("EMAIL", 0, 5)], policy_hash="h")
    field_names = set(vars(audit)) if hasattr(audit, "__dict__") else set(audit.__slots__)
    assert field_names == {"counts", "policy_hash", "ts"}


def test_redaction_result_holds_parts() -> None:
    audit = AuditRecord.from_spans([], policy_hash="h")
    r = RedactionResult(text="x", audit=audit, spans=[])
    assert r.text == "x"
    assert r.spans == []
    assert r.audit is audit


def test_redaction_result_audit_required() -> None:
    try:
        RedactionResult(text="x", spans=[])  # type: ignore[call-arg]
    except TypeError:
        return
    raise AssertionError("RedactionResult should require audit")
