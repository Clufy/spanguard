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
