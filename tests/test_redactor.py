import re

from spanguard._transform import apply_spans
from spanguard.policy import Policy
from spanguard.redactor import Redactor
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
