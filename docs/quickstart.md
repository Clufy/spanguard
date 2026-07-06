# Quickstart

`Redactor` takes a `Policy` (what to detect, how to transform it, and
optionally a key) and turns raw text into a `RedactionResult` — the redacted
`text`, the detected `spans`, and a leak-free `audit` record. The walkthrough
below runs all four redaction modes over the same input string.

!!! tip "Every mode below shares one guarantee"
    Whichever mode you pick, `result.audit.counts` only ever holds
    entity-type counts — never the raw matched values. It's always safe to
    log or ship `result.audit` to a compliance sink.

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

This exact block is executed verbatim by the test suite (and mirrored in
`README.md`), so it can't silently drift out of sync with the library.

## Walking through the four modes

=== "mask"

    Replaces every matched character with `mask_char` (default `█`), so the
    redacted text keeps the original length and word-break structure but
    reveals nothing about the value:

    ```python
    mask_policy = Policy(mode="mask", entities=("EMAIL", "PHONE"))  # (1)!
    mask_result = Redactor(mask_policy).redact(text)
    ```

    1. `entities` is a tuple (or list — coerced to a tuple by `Policy`) of
       the entity types this policy should redact; anything not listed is
       left untouched.

=== "placeholder"

    Replaces the match with a `[TYPE]` tag — useful when downstream
    processing (or a human reader) needs to know *what kind* of thing was
    removed, but not its value or length.

=== "hash"

    Replaces the match with a deterministic `[TYPE:digest]` tag, computed as
    an HMAC over the matched value and a key. The same input and key always
    produce the same digest, so hashed output is stable and joinable across
    redaction runs without ever storing the original value.

=== "tokenize"

    Replaces the match with a `⟦TYPE_digest⟧` token and records the mapping
    in a `Keyring`. Unlike `hash`, this is **reversible**:
    `Redactor.reveal(text)` looks the tokens back up and restores the
    original value — but only within the process that holds the keyring (or
    one initialized with the same key).

## Notes

- `entities` accepts a tuple (shown above) or a list — a list is coerced to a
  tuple by `Policy`.
- `result.audit` is an `AuditRecord` with `counts`, `policy_hash`, and `ts`
  (timestamp) — it never contains raw matched text, so it is always safe to
  log or ship to a compliance sink.
- `result.spans` gives you the raw `Span(type, start, end)` list if you need
  the detected regions directly instead of (or alongside) the transformed text.

!!! warning "The ephemeral-key warning"
    `hash` and `tokenize` modes need a key to produce reproducible output.
    Pass `hmac_key=...` / `tokenize_key=...` explicitly (as above), or set
    the `SPANGUARD_HMAC_KEY` / `SPANGUARD_TOKENIZE_KEY` environment
    variables. If neither is provided, spanguard falls back to a **fresh
    random key per process** and emits a `UserWarning` — the output is then
    usable only within that process. See
    [Known limitations](known-limitations.md#the-ephemeral-key-warning) for
    the full explanation.
