# Quickstart

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

## Notes

- `entities` accepts a tuple (shown above) or a list — a list is coerced to a
  tuple by `Policy`.
- `hash` and `tokenize` modes need a key to produce reproducible output. Pass
  `hmac_key=...` / `tokenize_key=...` explicitly (as above), or set the
  `SPANGUARD_HMAC_KEY` / `SPANGUARD_TOKENIZE_KEY` environment variables. If
  neither is provided, spanguard falls back to a fresh random key per process
  and emits a `UserWarning` — the output is then usable only within that
  process (see [Known limitations](known-limitations.md)).
- `result.audit` is an `AuditRecord` with `counts`, `policy_hash`, and `ts`
  (timestamp) — it never contains raw matched text, so it is always safe to
  log or ship to a compliance sink.
- `result.spans` gives you the raw `Span(type, start, end)` list if you need
  the detected regions directly instead of (or alongside) the transformed text.
