<div class="sg-hero" markdown>
# spanguard

Detect and redact PII/PHI in text and streaming transcripts — and get a
**leak-free audit record** for every redaction, automatically.
</div>

**spanguard** finds personally identifiable information and protected health
information (PII/PHI) in plain text or in a live, chunked stream, and rewrites
it according to a `Policy` you control. Every result carries an `AuditRecord`
that proves *what* was redacted without ever repeating *the sensitive value
itself* — so the audit trail can never become a second place where the data
leaks out.

!!! tip "The leak-free-audit promise"
    Every call to `Redactor.redact()` returns a `RedactionResult` whose
    `audit` field (an `AuditRecord`) contains **only entity-type counts, a
    policy hash, and a timestamp** — never the raw matched values.

    ```python
    result = redactor.redact("mail jane@x.com")
    result.audit.counts        # {"EMAIL": 1}  -- never "jane@x.com"
    ```

    The same guarantee holds for the CLI's `--audit-json` output and for
    `StreamRedactor`, which redacts chunked text (e.g. a live transcript)
    while guaranteeing that the concatenation of its streamed output equals
    what a single one-shot `redact()` call would have produced.

## Why spanguard

<div class="grid cards" markdown>

-   :material-shield-lock-outline: __Four redaction modes__

    ---

    `mask`, `placeholder`, `hash`, and reversible `tokenize` — one mode
    per `Policy`.

    [:octicons-arrow-right-24: Quickstart](quickstart.md)

-   :material-clipboard-text-search-outline: __Built-in entity coverage__

    ---

    Regex/checksum recognizers for `EMAIL`, `PHONE`, `SSN`, `MRN`, `DOB`,
    `CREDIT_CARD` (Luhn-validated), and `API_KEY` — plus an opt-in spaCy
    NER recognizer for `PERSON`/`LOCATION`.

    [:octicons-arrow-right-24: Recognizers](recognizers.md)

-   :material-file-document-check-outline: __Leak-free audit records__

    ---

    `AuditRecord` carries entity counts, a policy hash, and a timestamp —
    never the raw matched text — so logging it is always safe.

    [:octicons-arrow-right-24: API reference](api.md)

-   :material-waveform: __Streaming-safe__

    ---

    `StreamRedactor` redacts chunked text (e.g. a live call transcript)
    without ever leaking a partial match across a chunk boundary.

    [:octicons-arrow-right-24: Streaming](streaming.md)

-   :material-console-line: __A real CLI__

    ---

    `spanguard scan` and `spanguard redact` cover ad-hoc and pipeline use
    without writing a line of Python.

    [:octicons-arrow-right-24: CLI](cli.md)

-   :material-puzzle-outline: __Pluggable by design__

    ---

    Ship your own detector by implementing the `Recognizer` protocol —
    combine it with, or fully replace, the built-ins.

    [:octicons-arrow-right-24: Writing a custom recognizer](recognizers.md#writing-a-custom-recognizer)

</div>

## Install

=== "pip"

    ```bash
    pip install spanguard
    ```

=== "uv"

    ```bash
    uv add spanguard
    ```

For the optional NER (`PERSON`/`LOCATION`) recognizer:

=== "pip"

    ```bash
    pip install spanguard[ner]
    python -m spacy download en_core_web_sm
    ```

=== "uv"

    ```bash
    uv add "spanguard[ner]"
    uv run python -m spacy download en_core_web_sm
    ```

## What it detects out of the box

Built-in regex/checksum recognizers cover `EMAIL`, `PHONE`, `SSN`, `MRN`,
`DOB`, `CREDIT_CARD` (Luhn-validated), and `API_KEY`. An opt-in spaCy-based
recognizer adds `PERSON`/`LOCATION` detection when you pass it to `Redactor`. See [Recognizers](recognizers.md)
for the full entity table and how to plug in your own detector.

## Where to go next

- [Quickstart](quickstart.md) — mask, placeholder, hash, and tokenize+reveal in a few lines.
- [Recognizers](recognizers.md) — the entity table and how to write a custom `Recognizer`.
- [Streaming](streaming.md) — redacting text that arrives in chunks.
- [CLI](cli.md) — the `spanguard scan` / `spanguard redact` commands.
- [API reference](api.md) — full generated reference for all public symbols.
- [Known limitations](known-limitations.md) — honest gaps and edge cases.
