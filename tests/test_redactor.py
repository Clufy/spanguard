import re

from spanguard._transform import apply_spans
from spanguard.policy import Policy
from spanguard.redactor import Redactor, _trim_separators
from spanguard.result import RedactionResult, Span


def test_mask_replaces_each_char() -> None:
    text = "id jane@x.com!"
    spans = [Span("EMAIL", 3, 13)]
    out = apply_spans(text, spans, mode="mask", mask_char="█")
    assert out == "id ██████████!"
    assert len(out) == len(text)


def test_placeholder_replaces_with_type_tag() -> None:
    text = "id jane@x.com!"
    spans = [Span("EMAIL", 3, 13)]
    out = apply_spans(text, spans, mode="placeholder", mask_char="█")
    assert out == "id [EMAIL]!"


def test_apply_spans_handles_multiple_ordered() -> None:
    text = "a 555-123-4567 b jane@x.com"
    spans = [Span("PHONE", 2, 14), Span("EMAIL", 17, 27)]
    out = apply_spans(text, spans, mode="placeholder", mask_char="█")
    assert out == "a [PHONE] b [EMAIL]"


def test_redactor_masks_email_and_phone() -> None:
    r = Redactor(Policy(mode="placeholder", entities=["EMAIL", "PHONE"]))
    res = r.redact("Call me at 555-123-4567, jane@x.com")
    assert isinstance(res, RedactionResult)
    assert res.text == "Call me at [PHONE], [EMAIL]"
    assert res.audit is not None
    assert res.audit.counts == {"PHONE": 1, "EMAIL": 1}


def test_redactor_respects_entity_filter() -> None:
    # Only PHONE requested -> email left intact.
    r = Redactor(Policy(mode="placeholder", entities=["PHONE"]))
    res = r.redact("phone 555-123-4567 mail jane@x.com")
    assert res.text == "phone [PHONE] mail jane@x.com"
    assert res.audit is not None
    assert res.audit.counts == {"PHONE": 1}


def test_redactor_overlap_resolved_before_transform() -> None:
    # CREDIT_CARD (Luhn) vs any digit-run collision resolves deterministically.
    r = Redactor(Policy(mode="placeholder", entities=["CREDIT_CARD"]))
    res = r.redact("pay 4111 1111 1111 1111 now")
    assert res.text == "pay [CREDIT_CARD] now"


def test_redactor_trims_span_boundary_separators() -> None:
    # Regression: a regex candidate span (e.g. CREDIT_CARD) can over-consume
    # a trailing separator character next to a word boundary; the redactor
    # must trim it so the surrounding text/spacing is preserved exactly.
    text = "4111 1111 1111 1111 now"
    span = Span("CREDIT_CARD", 0, len(text) - len("now"))  # includes trailing space
    trimmed = _trim_separators(span, text)
    assert text[trimmed.start:trimmed.end] == "4111 1111 1111 1111"

    # Leading separator is trimmed symmetrically.
    text2 = " 4111111111111111"
    span2 = Span("CREDIT_CARD", 0, len(text2))
    trimmed2 = _trim_separators(span2, text2)
    assert text2[trimmed2.start:trimmed2.end] == "4111111111111111"

    # A clean span (no boundary separators) is returned unchanged (identity).
    text3 = "4111111111111111"
    span3 = Span("CREDIT_CARD", 0, len(text3))
    assert _trim_separators(span3, text3) is span3


def test_redactor_audit_policy_hash_matches_policy() -> None:
    p = Policy(mode="mask", entities=["EMAIL"])
    res = Redactor(p).redact("x jane@x.com")
    assert res.audit is not None
    assert res.audit.policy_hash == p.policy_hash()


def test_custom_recognizer_plugs_in() -> None:
    class Zip5Recognizer:
        entity_type = "ZIP"

        def recognize(self, text: str) -> list[Span]:
            return [Span("ZIP", m.start(), m.end()) for m in re.finditer(r"\b\d{5}\b", text)]

    r = Redactor(Policy(mode="placeholder", entities=["ZIP"]), recognizers=[Zip5Recognizer()])
    res = r.redact("zip 90210 end")
    assert res.text == "zip [ZIP] end"
    assert res.audit is not None
    assert res.audit.counts == {"ZIP": 1}
