# spanguard

**spanguard** detects and redacts PII/PHI (personally identifiable information
and protected health information) in text and streaming transcripts, and
produces a **leak-free audit record** for every redaction.

## The leak-free-audit promise

Every call to `Redactor.redact()` returns a `RedactionResult` whose `audit`
field (an `AuditRecord`) contains **only entity-type counts, a policy hash,
and a timestamp** — never the raw matched values. You can log, store, or
ship the audit record anywhere a compliance trail is needed without it ever
becoming a second place where sensitive data leaks out.

```python
result = redactor.redact("mail jane@x.com")
result.audit.counts        # {"EMAIL": 1}  -- never "jane@x.com"
```

The same guarantee holds for the CLI's `--audit-json` output and for
`StreamRedactor`, which redacts chunked text (e.g. a live transcript) while
guaranteeing that the concatenation of its streamed output equals what a
single one-shot `redact()` call would have produced.

## What it detects out of the box

Built-in regex/checksum recognizers cover `EMAIL`, `PHONE`, `SSN`, `MRN`,
`DOB`, `CREDIT_CARD` (Luhn-validated), and `API_KEY`. An optional spaCy-based
recognizer adds `PERSON`/`LOCATION` detection. See [Recognizers](recognizers.md)
for the full entity table and how to plug in your own detector.

## Install

```bash
pip install spanguard
```

For the optional NER (`PERSON`/`LOCATION`) recognizer:

```bash
pip install spanguard[ner]
python -m spacy download en_core_web_sm
```

## Where to go next

- [Quickstart](quickstart.md) — mask, placeholder, hash, and tokenize+reveal in a few lines.
- [Recognizers](recognizers.md) — the entity table and how to write a custom `Recognizer`.
- [Streaming](streaming.md) — redacting text that arrives in chunks.
- [CLI](cli.md) — the `spanguard scan` / `spanguard redact` commands.
- [Known limitations](known-limitations.md) — honest gaps and edge cases.
