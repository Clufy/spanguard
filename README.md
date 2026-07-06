# spanguard

[![CI](https://github.com/Clufy/spanguard/actions/workflows/ci.yml/badge.svg)](https://github.com/Clufy/spanguard/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/spanguard.svg)](https://pypi.org/project/spanguard/)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen.svg)](https://github.com/Clufy/spanguard/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue.svg)](https://clufy.github.io/spanguard)

Detect and redact PII/PHI (personally identifiable information and protected
health information) in text and streaming transcripts, and produce a
**leak-free audit record** for every redaction. Every `Redactor.redact()`
call returns a `RedactionResult` whose `audit` field contains only
entity-type counts, a policy hash, and a timestamp — never the raw matched
values — so the audit trail itself can never become a second place where
sensitive data leaks out.

## 60-second quickstart

```python
from spanguard import Redactor, Policy

text = "Contact: jane@example.com or 555-123-4567."

# --- mask: replace each character with mask_char, preserving length ---
mask_policy = Policy(mode="mask", entities=("EMAIL", "PHONE"))
mask_result = Redactor(mask_policy).redact(text)
print(mask_result.text)
# Contact: ████████████████ or ████████████.
print(mask_result.audit.counts)
# {'EMAIL': 1, 'PHONE': 1}

# --- placeholder: replace with a [TYPE] tag ---
placeholder_policy = Policy(mode="placeholder", entities=("EMAIL", "PHONE"))
placeholder_result = Redactor(placeholder_policy).redact(text)
print(placeholder_result.text)
# Contact: [EMAIL] or [PHONE].

# --- hash: deterministic HMAC digest, reproducible with the same key ---
hash_policy = Policy(mode="hash", entities=("EMAIL", "PHONE"))
hash_redactor = Redactor(hash_policy, hmac_key=b"docs-example-key")
hash_result = hash_redactor.redact(text)
print(hash_result.text)
# Contact: [EMAIL:11d041e6c58a0530] or [PHONE:cbe886551f4e27ed].

# --- tokenize + reveal: reversible via an in-memory keyring ---
tokenize_policy = Policy(mode="tokenize", entities=("EMAIL", "PHONE"))
tokenize_redactor = Redactor(tokenize_policy, tokenize_key=b"docs-example-key")
tokenize_result = tokenize_redactor.redact(text)
print(tokenize_result.text)
# Contact: ⟦EMAIL_11d041e6c58a0530⟧ or ⟦PHONE_cbe886551f4e27ed⟧.

revealed = tokenize_redactor.reveal(tokenize_result.text)
print(revealed == text)
# True
```

See the [Quickstart docs](https://clufy.github.io/spanguard/quickstart/)
for notes on keys, the audit record, and `result.spans`.

## Built-in entity table

| Entity type   | Detector                          | Notes                                                             |
|---------------|------------------------------------|--------------------------------------------------------------------|
| `EMAIL`       | regex                              | Unicode local part and domain; requires a dotted TLD of >= 2 letters. |
| `PHONE`       | regex                              | NANP-style 3-3-4, optional `+country`, `-`/`.`/space/parens separators. |
| `SSN`         | regex                              | `###-##-####`.                                                     |
| `MRN`         | regex (context-anchored)           | Requires an `MRN` prefix; only the digit run is redacted.          |
| `DOB`         | regex                              | `mm/dd/yyyy` (1- or 2-digit month/day) or ISO `yyyy-mm-dd`.         |
| `CREDIT_CARD` | regex + Luhn checksum              | Contiguous 13-19 digits, or standard printed groupings; Luhn-validated. |
| `API_KEY`     | regex                              | Known prefixes (`sk-`, `AKIA`, `ghp_`) or a long high-entropy alnum run. |
| `PERSON`, `LOCATION` | spaCy NER (optional `[ner]` extra) | Requires `pip install spanguard[ner]` and a downloaded spaCy model. |

Four redaction modes are available on every `Policy`: `mask`, `placeholder`,
`hash`, and `tokenize` (reversible via `Redactor.reveal()`). See
[Recognizers](https://clufy.github.io/spanguard/recognizers/) for the
full detail and how to plug in a custom `Recognizer`.

## Install

```bash
pip install spanguard
```

For the optional NER (`PERSON`/`LOCATION`) recognizer:

```bash
pip install spanguard[ner]
python -m spacy download en_core_web_sm
```

## Docs

Full documentation, including streaming redaction and the CLI, is at
[clufy.github.io/spanguard](https://clufy.github.io/spanguard).

## License

MIT — see [LICENSE](LICENSE).
