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
    policy = Policy(mode="placeholder", entities=["EMAIL", "PHONE"])
    one_shot = Redactor(policy).redact(text).text
    streamed = _stream(text, [4, 4, 4, 4], policy)
    assert streamed == one_shot
    assert "jane@x.com" not in streamed
    assert "555-123-4567" not in streamed


def test_stream_entity_split_mid_token_is_redacted() -> None:
    # Email split right in the middle across a boundary.
    text = "mail jane@example.com now"
    policy = Policy(mode="placeholder", entities=["EMAIL"])
    r = Redactor(policy)
    sr = StreamRedactor(r)
    out = sr.feed("mail jane@ex") + sr.feed("ample.com now") + sr.flush()
    assert out == r.redact(text).text
    assert "jane@example.com" not in out
    assert "[EMAIL]" in out


def test_stream_equals_one_shot_property_random_splits() -> None:
    text = "SSN 123-45-6789 card 4111 1111 1111 1111 mail a.b@sub.example.co end"
    policy = Policy(mode="mask", entities=["SSN", "CREDIT_CARD", "EMAIL"])
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
    policy = Policy(mode="tokenize", entities=["EMAIL", "PHONE"])
    key = b"streamkey"
    one_shot_r = Redactor(policy, tokenize_key=key)
    one_shot = one_shot_r.redact(text).text
    streamed = _stream(text, [3, 5, 2, 9], policy, tokenize_key=key)
    assert streamed == one_shot            # same tokens for same key


def test_flush_drains_and_resets() -> None:
    r = Redactor(Policy(mode="placeholder", entities=["EMAIL"]))
    sr = StreamRedactor(r)
    sr.feed("partial no entity yet")
    sr.flush()
    assert sr.pending == 0
    # after flush, a fresh feed works independently
    out = sr.feed("x jane@x.com") + sr.flush()
    assert "[EMAIL]" in out


def test_empty_feed_and_flush() -> None:
    r = Redactor(Policy(mode="mask", entities=["EMAIL"]))
    sr = StreamRedactor(r)
    assert sr.feed("") == ""
    assert sr.flush() == ""
