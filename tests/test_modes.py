from spanguard.policy import Policy
from spanguard.redactor import Redactor
from spanguard.tokenize import Keyring


def test_hash_mode_is_deterministic_and_labeled() -> None:
    r = Redactor(Policy(mode="hash", entities=["EMAIL"]), hmac_key=b"k")
    a = r.redact("x jane@x.com")
    r2 = Redactor(Policy(mode="hash", entities=["EMAIL"]), hmac_key=b"k")
    b = r2.redact("x jane@x.com")
    assert a.text == b.text                       # deterministic across instances w/ same key
    assert "jane@x.com" not in a.text
    assert a.text.startswith("x [EMAIL:") and a.text.endswith("]")


def test_hash_mode_differs_by_key() -> None:
    a = Redactor(Policy(mode="hash", entities=["EMAIL"]), hmac_key=b"k1").redact("x jane@x.com")
    b = Redactor(Policy(mode="hash", entities=["EMAIL"]), hmac_key=b"k2").redact("x jane@x.com")
    assert a.text != b.text


def test_tokenize_then_reveal_round_trips() -> None:
    r = Redactor(Policy(mode="tokenize", entities=["EMAIL", "PHONE"]), tokenize_key=b"k")
    original = "call 555-123-4567, jane@x.com"
    tok = r.redact(original)
    assert "555-123-4567" not in tok.text
    assert "jane@x.com" not in tok.text
    restored = r.reveal(tok.text, keyring=r.keyring)
    assert restored == original


def test_reveal_without_correct_keyring_fails_to_restore() -> None:
    r = Redactor(Policy(mode="tokenize", entities=["EMAIL"]), tokenize_key=b"k")
    tok = r.redact("mail jane@x.com")
    empty = Keyring(b"other-key")           # wrong key, empty map
    assert r.reveal(tok.text, keyring=empty) == tok.text     # nothing restored
    assert "jane@x.com" not in r.reveal(tok.text, keyring=empty)


def test_tokenize_deterministic_same_key() -> None:
    r1 = Redactor(Policy(mode="tokenize", entities=["EMAIL"]), tokenize_key=b"same")
    r2 = Redactor(Policy(mode="tokenize", entities=["EMAIL"]), tokenize_key=b"same")
    assert r1.redact("x jane@x.com").text == r2.redact("x jane@x.com").text


def test_key_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SPANGUARD_TOKENIZE_KEY", "env-key")
    r = Redactor(Policy(mode="tokenize", entities=["EMAIL"]))
    explicit = Redactor(Policy(mode="tokenize", entities=["EMAIL"]), tokenize_key=b"env-key")
    assert r.redact("x jane@x.com").text == explicit.redact("x jane@x.com").text


def test_audit_still_leak_free_for_hash_and_tokenize() -> None:
    import json
    raw = "jane@x.com"
    for mode, kwargs in (("hash", {"hmac_key": b"k"}), ("tokenize", {"tokenize_key": b"k"})):
        r = Redactor(Policy(mode=mode, entities=["EMAIL"]), **kwargs)  # type: ignore[arg-type]
        res = r.redact(f"mail {raw}")
        assert res.audit is not None
        blob = json.dumps(
            {"counts": res.audit.counts, "policy_hash": res.audit.policy_hash, "ts": res.audit.ts}
        )
        assert raw not in blob
