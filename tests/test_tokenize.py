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
