# Known limitations

An honest list of gaps and edge cases. If a limitation here affects your use
case, prefer a custom `Recognizer` (see [Recognizers](recognizers.md)) or an
additional post-processing pass over relying on spanguard alone for a
compliance-critical guarantee it does not make.

## Credit-card detection matches standard groupings only

`CREDIT_CARD` matches a contiguous 13-19 digit run, or one of the standard
printed groupings (4-4-4-4, 4-4-4-3, or 4-6-5) separated by a single space or
dash, each validated with a Luhn checksum. A card number embedded as
undelimited digits **inside a longer number** (e.g. concatenated directly
against an adjacent unrelated digit string with no boundary) can be missed,
because the recognizer requires a non-digit/non-dash boundary before and
after the candidate run to avoid merging unrelated numbers together. This is
a deliberate precision/recall trade-off: without the boundary requirement,
a phone number immediately followed by a card number would be misdetected
as one bogus digit blob.

## `API_KEY`'s generic branch may over-match long hex strings

Beyond known-prefix formats (`sk-...`, `AKIA...`, `ghp_...`), `API_KEY` also
matches any bare run of 32+ alphanumeric characters as a heuristic catch-all
for high-entropy secrets. This means long hex strings, hashes, or other
opaque identifiers that are **not** actually API keys (e.g. a SHA-256 hex
digest, a UUID with dashes stripped, a git commit hash concatenated with
other text) can be flagged and redacted as `API_KEY` even though they carry
no sensitive data. If this over-matches in your corpus, pass a narrower
custom `Recognizer` for `API_KEY` (or omit `"API_KEY"` from `Policy.entities`
and add your own prefix-anchored pattern).

## `EMAIL` may over-match `@`-bearing non-email tokens

`EMAIL` accepts Unicode local parts and a dotted, letters-only TLD, matching
any `local@domain.tld`-shaped token bounded by whitespace or brackets. This
deliberately errs toward redaction, so it can also flag `@`-bearing tokens
that are not email addresses: the userinfo of a URL (`user:pw@host.example`),
an SSH remote (`git@github.com`), a `name@2x.png`-style asset filename, or a
config value like `key=val@host.io`. As with `API_KEY`, every such case
over-redacts rather than leaking, so it is a precision cost, not a privacy
gap. If it over-matches in your corpus, pass a narrower custom `Recognizer`
for `EMAIL` or drop `"EMAIL"` from `Policy.entities` and add your own pattern.

## NER (`PERSON`/`LOCATION`) requires the `[ner]` extra and a downloaded model

`SpacyRecognizer` is not part of the default recognizer set and is not
installed by a plain `pip install spanguard`. To use it you need:

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

spaCy is imported lazily specifically so `import spanguard` stays fast and
dependency-light without the extra. If the extra isn't installed,
instantiating `SpacyRecognizer` and calling `.recognize()` raises an
`ImportError` with install instructions, rather than failing at import time.
NER quality also depends entirely on the underlying spaCy model — like any
statistical NER, it can miss unusual names/locations or misclassify
ambiguous tokens, and its precision/recall differs by domain and language
from the model's training data.

## The ephemeral-key warning

!!! warning "Set an explicit key in production"
    `hash` and `tokenize` modes need an HMAC key to produce output that is
    reproducible across runs (and, for `tokenize`, reversible via
    `Redactor.reveal()`). If you don't pass `hmac_key=...` /
    `tokenize_key=...` explicitly and don't set the `SPANGUARD_HMAC_KEY` /
    `SPANGUARD_TOKENIZE_KEY` environment variables, spanguard falls back to
    a **fresh random key generated per process** and emits:

    ```text
    UserWarning: No key provided and SPANGUARD_HMAC_KEY is unset; using an
    ephemeral random key. Hashes/tokens will not be reproducible across
    processes and reveal() will only work within this process. Set the key
    explicitly or via the env var for stable output.
    ```

This means: hash digests or tokens produced by two separate process runs
(or two separate `Redactor` instances without a shared explicit key) will
**not** match each other, and a `Keyring` built during one process cannot
`reveal()` tokens produced by a different process's ephemeral key. This is
intentional — spanguard never persists a randomly generated key on your
behalf — but it means production deployments that need stable hashes across
restarts, or that need to reveal tokens in a different process than the one
that created them, **must** supply an explicit, persisted key.
