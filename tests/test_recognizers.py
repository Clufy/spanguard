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


def test_luhn_valid_known_good() -> None:
    assert luhn_valid("4111111111111111")   # test Visa
    assert luhn_valid("5500005555555559")


def test_luhn_rejects_bad_checkdigit() -> None:
    assert not luhn_valid("4111111111111112")


def test_luhn_rejects_non_digits_and_empty() -> None:
    assert not luhn_valid("")
    assert not luhn_valid("4111-1111")  # caller must strip separators first


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


def test_email_unicode_local_part() -> None:
    r = EmailRecognizer()
    text = "write café@example.com now"
    spans = r.recognize(text)
    assert len(spans) == 1
    assert text[spans[0].start : spans[0].end] == "café@example.com"


def test_email_still_rejects_non_emails() -> None:
    r = EmailRecognizer()
    assert r.recognize("not@an@email") == []
    assert r.recognize("just words here") == []


def test_email_glued_after_closing_bracket_is_detected() -> None:
    # Regression: an email glued directly after ')' or ']' must not be dropped
    # (the old lookbehind silently suppressed the whole match -> PII leak).
    r = EmailRecognizer()
    for text, want in [
        ("x)jane@x.com", "jane@x.com"),
        ("(note)bob@y.org", "bob@y.org"),
        ('"jane@x.com"', "jane@x.com"),
        ("see[ref]amy@z.net", "amy@z.net"),
    ]:
        spans = r.recognize(text)
        assert len(spans) == 1, f"{text!r} -> {spans}"
        assert text[spans[0].start : spans[0].end] == want


def test_email_still_rejects_non_emails_after_fix() -> None:
    r = EmailRecognizer()
    for text in ["http://example.com/x", "python3.12", "3.14159", "example.com",
                 "user@localhost", "192.168.1.1", "not@an@email", "trailing@dot."]:
        assert r.recognize(text) == [], text


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


def test_dob_unpadded_month_day() -> None:
    r = DOBRecognizer()
    assert len(r.recognize("dob 1/2/1990")) == 1
    assert len(r.recognize("dob 01/02/1990")) == 1
    assert r.recognize("score 99/99/9999 invalid") == []


def test_credit_card_groupings_and_luhn() -> None:
    r = CreditCardRecognizer()

    def one(text: str) -> str:
        spans = r.recognize(text)
        assert len(spans) == 1, f"{text!r} -> {spans}"
        return text[spans[0].start : spans[0].end]

    # contiguous, spaced, dashed, amex (4-6-5 and contiguous)
    assert one("card 4111111111111111 end") == "4111111111111111"
    assert one("card 4111 1111 1111 1111 end") == "4111 1111 1111 1111"
    assert one("card 4111-1111-1111-1111 end") == "4111-1111-1111-1111"
    assert one("amex 3782 822463 10005 end") == "3782 822463 10005"
    assert one("amex 378282246310005 end") == "378282246310005"


def test_credit_card_back_to_back_with_phone_detected() -> None:
    # Regression: a phone immediately followed by a card must not merge into one
    # over-long digit run that fails Luhn; the card must be detected.
    r = CreditCardRecognizer()
    text = "call 555-123-4567 4111 1111 1111 1111 end"
    spans = r.recognize(text)
    assert len(spans) == 1
    assert text[spans[0].start : spans[0].end] == "4111 1111 1111 1111"


def test_credit_card_negatives() -> None:
    r = CreditCardRecognizer()
    assert r.recognize("num 4111 1111 1111 1112 x") == []      # bad Luhn
    assert r.recognize("id 994111111111111100 x") == []        # not card-grouped digit soup
    assert r.recognize("short 4111 1111 x") == []              # too few digits


def test_two_cards_in_one_string() -> None:
    r = CreditCardRecognizer()
    text = "a 4111 1111 1111 1111 and 5500 0055 5555 5559 b"
    spans = r.recognize(text)
    assert len(spans) == 2


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
