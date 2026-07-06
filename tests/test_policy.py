from spanguard.policy import DEFAULT_ENTITIES, Policy


def test_defaults() -> None:
    p = Policy()
    assert p.mode == "mask"
    assert p.entities == DEFAULT_ENTITIES
    assert isinstance(p.entities, tuple)
    assert p.mask_char == "█"


def test_policy_hash_is_stable_and_content_addressed() -> None:
    a = Policy(mode="placeholder", entities=("EMAIL",))
    b = Policy(mode="placeholder", entities=("EMAIL",))
    c = Policy(mode="mask", entities=("EMAIL",))
    assert a.policy_hash() == b.policy_hash()
    assert a.policy_hash() != c.policy_hash()
    assert len(a.policy_hash()) == 16


def test_policy_is_frozen() -> None:
    p = Policy()
    try:
        p.mode = "hash"
    except (ValueError, AttributeError, TypeError):
        return
    raise AssertionError("Policy should be immutable")


def test_invalid_mode_rejected() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Policy(mode="nonsense")  # type: ignore[arg-type]
