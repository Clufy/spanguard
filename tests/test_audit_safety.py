"""The load-bearing guarantee: audit records never contain raw sensitive values."""

import json

from spanguard.policy import Policy
from spanguard.redactor import Redactor

RAW_VALUES = ["555-123-4567", "jane@x.com", "123-45-6789", "4111 1111 1111 1111"]
SAMPLE = f"call {RAW_VALUES[0]} mail {RAW_VALUES[1]} ssn {RAW_VALUES[2]} card {RAW_VALUES[3]}"


def test_audit_record_contains_no_raw_values() -> None:
    for mode in ("mask", "placeholder"):
        res = Redactor(Policy(mode=mode)).redact(SAMPLE)
        assert res.audit is not None
        blob = json.dumps(
            {"counts": res.audit.counts, "policy_hash": res.audit.policy_hash, "ts": res.audit.ts}
        )
        for raw in RAW_VALUES:
            assert raw not in blob
            # also assert no substring longer than a few chars leaks
            assert raw.replace(" ", "") not in blob.replace(" ", "")


def test_redacted_text_contains_no_raw_values() -> None:
    res = Redactor(Policy(mode="mask")).redact(SAMPLE)
    for raw in RAW_VALUES:
        assert raw not in res.text


def test_entity_type_label_is_what_appears_in_output_and_audit() -> None:
    # Contract: a recognizer's entity_type is a LABEL and appears verbatim
    # in placeholder output and audit counts. This test documents that the
    # label — not the matched raw text — is what surfaces, so recognizer
    # authors must never place sensitive matched content in entity_type.
    from spanguard.result import Span

    class LabeledRecognizer:
        entity_type = "CUSTOM_TOKEN"

        def recognize(self, text: str) -> list[Span]:
            import re
            return [Span("CUSTOM_TOKEN", m.start(), m.end())
                    for m in re.finditer(r"SECRET-\d+", text)]

    r = Redactor(Policy(mode="placeholder", entities=["CUSTOM_TOKEN"]),
                 recognizers=[LabeledRecognizer()])
    res = r.redact("value SECRET-42 here")
    # the raw matched text is gone; only the label surfaces
    assert "SECRET-42" not in res.text
    assert res.text == "value [CUSTOM_TOKEN] here"
    # audit counts are keyed by the label, and contain no raw value
    assert res.audit is not None
    assert res.audit.counts == {"CUSTOM_TOKEN": 1}
    assert "SECRET-42" not in str(res.audit.counts)
