# spanguard

**Redact PII/PHI from text and streams — with an audit trail that can never leak the data it's auditing.**

[![CI](https://github.com/Clufy/spanguard/actions/workflows/ci.yml/badge.svg)](https://github.com/Clufy/spanguard/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/spanguard.svg)](https://pypi.org/project/spanguard/)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen.svg)](https://github.com/Clufy/spanguard/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue.svg)](https://clufy.github.io/spanguard)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Typed](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/Clufy/spanguard/blob/master/LICENSE)

spanguard detects and redacts PII/PHI (personally identifiable information and
protected health information) in text and streaming transcripts. Every
`Redactor.redact()` call returns a `RedactionResult` whose `audit` field holds
only entity-type counts, a policy hash, and a timestamp — **never the raw
matched values** — so the audit trail itself can never become a second place
where sensitive data leaks out. That guarantee is enforced by the test suite,
not just documented.

## Contents

- [Why spanguard](#why-spanguard)
- [Install](#install)
- [60-second quickstart](#60-second-quickstart)
- [Streaming](#streaming)
- [CLI](#cli)
- [Built-in entity table](#built-in-entity-table)
- [Compliance / audit guarantee](#compliance--audit-guarantee)
- [Docs](#docs)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Why spanguard

- **Leak-free audit record** — `result.audit` carries entity-type counts, a
  policy hash, and a timestamp only; raw matches never enter it, and tests
  verify this holds across every mode.
- **Four redaction modes** — `mask`, `placeholder`, `hash` (deterministic
  HMAC), and `tokenize` (reversible).
- **Reversible tokenization** — turn tokens back into the original text with
  `Redactor.reveal()` and an in-memory `Keyring`, scoped to a single process.
- **Built-in detectors** — email (Unicode-aware), phone, SSN, MRN, DOB, and
  Luhn-validated credit card numbers, plus API key patterns.
- **Optional NER** — spaCy-backed `PERSON`/`LOCATION` detection behind the
  `[ner]` extra, off by default so the core install stays light.
- **Streaming-safe** — `StreamRedactor` redacts chunked input (e.g. a live
  transcript) so the output matches a one-shot redaction, even when an entity
  straddles a chunk boundary.
- **Pluggable recognizers** — register a custom `Recognizer` for domain-specific
  entities without forking the library.
- **Typed and tested** — mypy `--strict` and ruff clean, 128 tests, 97.9%
  coverage.
- **CLI included** — `spanguard scan` / `spanguard redact` for one-off files
  and shell pipelines.

## Install

```bash
pip install spanguard
```

For the optional NER (`PERSON`/`LOCATION`) recognizer:

```bash
pip install "spanguard[ner]"
python -m spacy download en_core_web_sm
```

NER is opt-in per `Redactor`: pass the recognizer alongside the built-ins.

```python
from spanguard import Policy, Redactor
from spanguard.recognizers import DEFAULT_RECOGNIZERS, SpacyRecognizer

redactor = Redactor(Policy(), recognizers=[*DEFAULT_RECOGNIZERS.values(), SpacyRecognizer()])
```

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

## Streaming

```python
from spanguard import Redactor, Policy, StreamRedactor

redactor = Redactor(Policy(mode="mask", entities=("EMAIL", "PHONE")))
stream = StreamRedactor(redactor)

output = stream.feed("Contact: jane@example.com ") + stream.feed("or 555-123-4567.")
output += stream.flush()
```

`StreamRedactor` holds back a tail of the buffer (minimum 64 characters) so an
entity split across a chunk boundary is still detected as one; the
concatenation of every `feed()` plus the final `flush()` is guaranteed to
equal a one-shot `redactor.redact(full_text).text`.

Text is emitted only up to a safe split point (whitespace outside any
entity), so a stream with none, such as a long base64 blob, is held in memory.
Pass `StreamRedactor(redactor, max_buffer=N)` to get a `StreamBufferFullError`
instead of unbounded growth. See
[Streaming](https://clufy.github.io/spanguard/streaming/).

## CLI

```bash
spanguard scan file.txt
spanguard redact file.txt --mode mask
spanguard redact file.txt --mode tokenize --out redacted.txt
cat file.txt | spanguard redact - --mode placeholder   # '-' reads stdin
```

`scan` reports entity-type counts only (no raw values); `redact` writes the
redacted text and, with `--audit-json`, the audit record to stderr. Bad input
(an unknown `--entities` name, a missing or non-UTF-8 file) exits with code 2
and a one-line `error:` message that never echoes input content. See
[CLI](https://clufy.github.io/spanguard/cli/).

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
| `PERSON`, `LOCATION` | spaCy NER (optional `[ner]` extra) | Requires the `[ner]` extra, a spaCy model, and passing `SpacyRecognizer()` (see [Install](#install)). |

Four redaction modes are available on every `Policy`: `mask`, `placeholder`,
`hash`, and `tokenize` (reversible via `Redactor.reveal()`). See
[Recognizers](https://clufy.github.io/spanguard/recognizers/) for the
full detail and how to plug in a custom `Recognizer`.

## Compliance / audit guarantee

`result.audit` (an `AuditRecord`) is designed to be safe to log, ship to a
SIEM, or hand to an auditor without a second review: it contains entity-type
**counts**, a **policy hash** (so you can prove which redaction policy ran),
and a **timestamp** — and structurally nothing else. No raw matched value, no
span offsets, no context window. The test suite asserts this property directly
so a future change that widens the audit record would fail CI, not just review.

## Docs

Full documentation, including the API reference, streaming redaction, and the
CLI, is at [clufy.github.io/spanguard](https://clufy.github.io/spanguard).

## Contributing

Bug reports and pull requests are welcome — see
[CONTRIBUTING.md](https://github.com/Clufy/spanguard/blob/master/CONTRIBUTING.md) for how to set up a dev environment and
run the test suite.

## Security

To report a vulnerability, please see [SECURITY.md](https://github.com/Clufy/spanguard/blob/master/SECURITY.md) rather than
opening a public issue.

## License

MIT — see [LICENSE](https://github.com/Clufy/spanguard/blob/master/LICENSE).
