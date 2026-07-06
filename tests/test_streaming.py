import random

from spanguard.policy import Policy
from spanguard.redactor import Redactor
from spanguard.streaming import StreamRedactor


def _stream(text: str, chunks: list[int], policy: Policy, **keys: bytes) -> str:
    r = Redactor(policy, **keys)  # type: ignore[arg-type]
    sr = StreamRedactor(r)
    out: list[str] = []
    i = 0
    for size in chunks:
        out.append(sr.feed(text[i : i + size]))
        i += size
    out.append(sr.feed(text[i:]))  # remainder as one more chunk
    out.append(sr.flush())
    return "".join(out)


def test_stream_equals_one_shot_simple() -> None:
    text = "Call me at 555-123-4567, jane@x.com"
    policy = Policy(mode="placeholder", entities=("EMAIL", "PHONE"))
    one_shot = Redactor(policy).redact(text).text
    streamed = _stream(text, [4, 4, 4, 4], policy)
    assert streamed == one_shot
    assert "jane@x.com" not in streamed
    assert "555-123-4567" not in streamed


def test_stream_entity_split_mid_token_is_redacted() -> None:
    # Email split right in the middle across a boundary.
    text = "mail jane@example.com now"
    policy = Policy(mode="placeholder", entities=("EMAIL",))
    r = Redactor(policy)
    sr = StreamRedactor(r)
    out = sr.feed("mail jane@ex") + sr.feed("ample.com now") + sr.flush()
    assert out == r.redact(text).text
    assert "jane@example.com" not in out
    assert "[EMAIL]" in out


def test_stream_equals_one_shot_property_random_splits() -> None:
    text = "SSN 123-45-6789 card 4111 1111 1111 1111 mail a.b@sub.example.co end"
    policy = Policy(mode="mask", entities=("SSN", "CREDIT_CARD", "EMAIL"))
    one_shot = Redactor(policy).redact(text).text
    rnd = random.Random(1234)  # deterministic
    for _ in range(50):
        # random chunk sizes 1..7
        sizes: list[int] = []
        remaining = len(text)
        while remaining > 0:
            s = rnd.randint(1, 7)
            sizes.append(s)
            remaining -= s
        assert _stream(text, sizes, policy) == one_shot


def test_stream_tokenize_matches_one_shot_and_reveals() -> None:
    text = "call 555-123-4567 or mail jane@x.com"
    policy = Policy(mode="tokenize", entities=("EMAIL", "PHONE"))
    key = b"streamkey"
    one_shot_r = Redactor(policy, tokenize_key=key)
    one_shot = one_shot_r.redact(text).text
    streamed = _stream(text, [3, 5, 2, 9], policy, tokenize_key=key)
    assert streamed == one_shot            # same tokens for same key


def test_flush_drains_and_resets() -> None:
    r = Redactor(Policy(mode="placeholder", entities=("EMAIL",)))
    sr = StreamRedactor(r)
    sr.feed("partial no entity yet")
    sr.flush()
    assert sr.pending == 0
    # after flush, a fresh feed works independently
    out = sr.feed("x jane@x.com") + sr.flush()
    assert "[EMAIL]" in out


def test_empty_feed_and_flush() -> None:
    r = Redactor(Policy(mode="mask", entities=("EMAIL",)))
    sr = StreamRedactor(r)
    assert sr.feed("") == ""
    assert sr.flush() == ""


def test_stream_phone_with_internal_spaces_not_leaked() -> None:
    # Regression: a PHONE containing internal spaces, followed by a long
    # unbroken token within one tail-length of the end, must NOT be cut on its
    # internal space (which would leak the raw number).
    text = "start " + "555 123 4567" + "y" * 120
    policy = Policy(mode="placeholder", entities=("PHONE",))
    r = Redactor(policy)
    sr = StreamRedactor(r)
    streamed = sr.feed(text) + sr.flush()
    assert streamed == r.redact(text).text
    assert "555 123 4567" not in streamed
    assert "[PHONE]" in streamed


def test_stream_mrn_left_context_preserved() -> None:
    # Regression: MRN detection needs the "MRN:" prefix; the emitted span covers
    # only the digits. A cut must not separate the prefix from the digits.
    text = "note MRN: 1234567 " + "z" * 130
    policy = Policy(mode="placeholder", entities=("MRN",))
    r = Redactor(policy)
    sr = StreamRedactor(r)
    streamed = sr.feed(text) + sr.flush()
    assert streamed == r.redact(text).text
    assert "1234567" not in streamed


def test_small_tail_is_rejected() -> None:
    # A tail below the floor must raise, not silently leak.
    import pytest

    r = Redactor(Policy(mode="mask", entities=("CREDIT_CARD",)))
    with pytest.raises(ValueError, match="tail must be >= 64"):
        StreamRedactor(r, tail=8)


def test_min_tail_boundary_accepted_and_safe() -> None:
    # tail == 64 is the floor: accepted, and must not leak a spaced credit card
    # fed one character at a time.
    text = "card 4111 1111 1111 1111 end"
    policy = Policy(mode="mask", entities=("CREDIT_CARD",))
    r = Redactor(policy)
    sr = StreamRedactor(r, tail=64)
    out = [sr.feed(ch) for ch in text]
    out.append(sr.flush())
    streamed = "".join(out)
    assert streamed == r.redact(text).text
    assert "4111 1111 1111 1111" not in streamed


def test_stream_property_all_modes_internal_separators() -> None:
    import random

    text = (
        "ph 555 123 4567 card 4111 1111 1111 1111 MRN: 1234567 "
        "mail a.b@sub.example.co end" + "z" * 150
    )
    for mode in ("mask", "placeholder", "hash", "tokenize"):
        policy = Policy(mode=mode, entities=("PHONE", "CREDIT_CARD", "MRN", "EMAIL"))
        keys = {"hmac_key": b"k", "tokenize_key": b"k"}
        one_shot = Redactor(policy, **keys).redact(text).text  # type: ignore[arg-type]
        rnd = random.Random(20260706)
        for _ in range(100):
            r = Redactor(policy, **keys)  # type: ignore[arg-type]
            sr = StreamRedactor(r)
            out: list[str] = []
            i = 0
            while i < len(text):
                step = rnd.randint(1, 9)
                out.append(sr.feed(text[i : i + step]))
                i += step
            out.append(sr.flush())
            assert "".join(out) == one_shot
