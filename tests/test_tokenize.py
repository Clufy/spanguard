from spanguard.tokenize import Keyring, hmac_digest, make_token


def test_hmac_digest_deterministic_and_key_sensitive() -> None:
    a = hmac_digest(b"key1", "EMAIL", "jane@x.com")
    b = hmac_digest(b"key1", "EMAIL", "jane@x.com")
    c = hmac_digest(b"key2", "EMAIL", "jane@x.com")
    d = hmac_digest(b"key1", "PHONE", "jane@x.com")
    assert a == b            # deterministic
    assert a != c            # key-sensitive
    assert a != d            # type-namespaced
    assert len(a) == 16 and all(ch in "0123456789abcdef" for ch in a)


def test_make_token_shape() -> None:
    tok = make_token("EMAIL", "deadbeefdeadbeef")
    assert tok == "⟦EMAIL_deadbeefdeadbeef⟧"


def test_keyring_tokenize_is_deterministic() -> None:
    kr = Keyring(b"secret")
    t1 = kr.tokenize("EMAIL", "jane@x.com")
    t2 = kr.tokenize("EMAIL", "jane@x.com")
    assert t1 == t2                      # same input+key -> same token
    assert kr.reveal_token(t1) == "jane@x.com"


def test_keyring_reveal_restores_all_tokens() -> None:
    kr = Keyring(b"secret")
    t_email = kr.tokenize("EMAIL", "jane@x.com")
    t_phone = kr.tokenize("PHONE", "555-123-4567")
    text = f"call {t_phone} or {t_email}"
    assert kr.reveal(text) == "call 555-123-4567 or jane@x.com"


def test_keyring_reveal_unknown_token_left_intact() -> None:
    kr = Keyring(b"secret")
    # a token this keyring never issued is not revealed
    assert kr.reveal("⟦EMAIL_0000000000000000⟧") == "⟦EMAIL_0000000000000000⟧"


def test_keyring_repr_hides_secret_and_map() -> None:
    kr = Keyring(b"super-secret-key")
    kr.tokenize("EMAIL", "jane@x.com")
    r = repr(kr)
    assert "super-secret-key" not in r
    assert "jane@x.com" not in r
    assert r == "Keyring(tokens=1)"


def test_wrong_keyring_cannot_reveal() -> None:
    # A different keyring (different key, empty map) reveals nothing.
    kr1 = Keyring(b"key-one")
    tok = kr1.tokenize("EMAIL", "jane@x.com")
    kr2 = Keyring(b"key-two")
    assert kr2.reveal(f"here {tok}") == f"here {tok}"   # unchanged


def test_reveal_does_not_re_expand_tokens_embedded_in_raw_values() -> None:
    # Adversarial: token A's raw value literally contains token B's string,
    # and A is issued before B. A single-pass reveal must restore A's raw
    # exactly and must NOT re-expand the embedded B token (which would leak
    # B's raw value into a reveal of text that only contained token A).
    from spanguard.tokenize import hmac_digest, make_token

    kr = Keyring(b"secret")
    tok_b_pre = make_token("PHONE", hmac_digest(b"secret", "PHONE", "555-000-1111"))
    raw_a = "x" + tok_b_pre + "y"
    tok_a = kr.tokenize("EMAIL", raw_a)          # inserted first
    tok_b = kr.tokenize("PHONE", "555-000-1111")  # inserted second
    assert tok_b == tok_b_pre
    # revealing text that contains ONLY token A restores raw_a verbatim...
    revealed = kr.reveal(tok_a)
    assert revealed == raw_a
    # ...and does NOT leak B's raw value
    assert "555-000-1111" not in revealed


def test_reveal_scales_with_many_tokens() -> None:
    import time

    kr = Keyring(b"k")
    raws = [f"user{i}@example.com" for i in range(30_000)]
    text = " ".join(kr.tokenize("EMAIL", raw) for raw in raws)
    t0 = time.perf_counter()
    out = kr.reveal(text)
    assert time.perf_counter() - t0 < 4.0  # pre-release version: ~11 s
    assert out == " ".join(raws)


def test_reveal_bracketed_label_round_trips() -> None:
    kr = Keyring(b"k")
    tok = kr.tokenize("A⟧B", "secret-1")
    tok2 = kr.tokenize("⟦X", "secret-2")
    assert kr.reveal(f"<{tok}|{tok2}>") == "<secret-1|secret-2>"


def test_reveal_leaves_unissued_token_shapes() -> None:
    kr = Keyring(b"k")
    tok = kr.tokenize("EMAIL", "jane@x.com")
    fake = make_token("EMAIL", "0" * 16)
    assert kr.reveal(fake) == fake
    assert kr.reveal("⟦" + tok) == "⟦jane@x.com"
    assert kr.reveal(f"{fake}{tok}⟧") == f"{fake}jane@x.com⟧"


def test_reveal_matches_reference_random() -> None:
    import random
    import re

    rng = random.Random(99)
    for labels in (["EMAIL", "PHONE"], ["EMAIL", "A⟧B", "⟦"]):
        kr = Keyring(b"k")
        toks = [kr.tokenize(rng.choice(labels), f"v{i}") for i in range(20)]
        mp = {t: kr.reveal_token(t) or "" for t in toks}
        ref = re.compile("|".join(re.escape(t) for t in mp))

        def expected(text: str, ref: re.Pattern[str] = ref, mp: dict[str, str] = mp) -> str:
            return ref.sub(lambda m: mp[m[0]], text)

        pieces = [*toks, "⟦", "⟧", "x", " ", make_token("EMAIL", "0" * 16)]
        for _ in range(500):
            s = "".join(rng.choice(pieces) for _ in range(rng.randint(0, 12)))
            assert kr.reveal(s) == expected(s), repr(s)
