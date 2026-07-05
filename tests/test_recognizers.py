from spanguard.recognizers.luhn import luhn_valid
from spanguard.recognizers.regex_recognizers import (
    DEFAULT_RECOGNIZERS,
    APIKeyRecognizer,
    CreditCardRecognizer,
    DOBRecognizer,
    EmailRecognizer,
    MRNRecognizer,
    PhoneRecognizer,
    SSNRecognizer,
)
from spanguard.result import Span


def test_luhn_valid_known_good() -> None:
    assert luhn_valid("4111111111111111")   # test Visa
    assert luhn_valid("5500005555555559")


def test_luhn_rejects_bad_checkdigit() -> None:
    assert not luhn_valid("4111111111111112")


def test_luhn_rejects_non_digits_and_empty() -> None:
    assert not luhn_valid("")
    assert not luhn_valid("4111-1111")  # caller must strip separators first


def _types(spans: list[Span]) -> list[tuple[str, int, int]]:
    return [(s.type, s.start, s.end) for s in spans]


def test_email_positive() -> None:
    r = EmailRecognizer()
    text = "reach a.b+tag@sub.example.co please"
    spans = r.recognize(text)
    assert len(spans) == 1
    s = spans[0]
    assert s.type == "EMAIL"
    assert text[s.start:s.end] == "a.b+tag@sub.example.co"


def test_email_negatives() -> None:
    r = EmailRecognizer()
    assert r.recognize("not@an@email") == []
    assert r.recognize("foo@ bar") == []
    assert r.recognize("just text, no at sign") == []


def test_phone_positive_formats() -> None:
    r = PhoneRecognizer()
    for t in ["555-123-4567", "(555) 123-4567", "+1 555 123 4567"]:
        spans = r.recognize(f"call {t} now")
        assert len(spans) == 1, t
        assert spans[0].type == "PHONE"


def test_phone_negatives() -> None:
    r = PhoneRecognizer()
    assert r.recognize("the year 2024 was fine") == []
    assert r.recognize("id 12345") == []


def test_ssn_positive_and_negative() -> None:
    r = SSNRecognizer()
    assert len(r.recognize("ssn 123-45-6789")) == 1
    assert r.recognize("phone 123-456-7890 here") == []  # wrong grouping


def test_mrn_requires_context() -> None:
    r = MRNRecognizer()
    assert len(r.recognize("MRN: 1234567")) == 1
    assert r.recognize("order 1234567 shipped") == []


def test_dob_positive_and_negative() -> None:
    r = DOBRecognizer()
    assert len(r.recognize("dob 01/02/1990")) == 1
    assert len(r.recognize("born 1990-02-01")) == 1
    assert r.recognize("score 99/99/9999 invalid") == []


def test_credit_card_luhn_gated() -> None:
    r = CreditCardRecognizer()
    assert len(r.recognize("card 4111 1111 1111 1111 ok")) == 1
    assert r.recognize("card 4111 1111 1111 1112 no") == []


def test_credit_card_span_excludes_trailing_separator() -> None:
    # Regression: the candidate regex must not consume a trailing space/dash.
    r = CreditCardRecognizer()
    text = "pay 4111 1111 1111 1111 now"
    spans = r.recognize(text)
    assert len(spans) == 1
    assert text[spans[0].start:spans[0].end] == "4111 1111 1111 1111"  # no trailing space
    # dash-separated, trailing punctuation:
    text2 = "card 4111-1111-1111-1111."
    spans2 = r.recognize(text2)
    assert len(spans2) == 1
    assert text2[spans2[0].start:spans2[0].end] == "4111-1111-1111-1111"


def test_api_key_positive_and_negative() -> None:
    r = APIKeyRecognizer()
    assert len(r.recognize("key sk-abcDEF0123456789abcDEF0123 end")) == 1
    assert len(r.recognize("aws AKIAIOSFODNN7EXAMPLE creds")) == 1
    assert r.recognize("this is a normal english sentence") == []


def test_default_recognizers_cover_all_types() -> None:
    assert set(DEFAULT_RECOGNIZERS) == {
        "EMAIL", "PHONE", "SSN", "MRN", "DOB", "CREDIT_CARD", "API_KEY",
    }
