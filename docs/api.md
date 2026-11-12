# API reference

This page is generated directly from the docstrings in `spanguard`'s source,
so it never drifts out of sync with the code. All nine names below are
importable straight from the top-level package:

```python
from spanguard import (
    Redactor,
    Policy,
    RedactionResult,
    Span,
    AuditRecord,
    Recognizer,
    Keyring,
    StreamRedactor,
    StreamBufferFullError,
)
```

## Core

The three types you touch on nearly every call: configure a `Policy`, run it
through a `Redactor`, and get back a `RedactionResult`.

### `Redactor`

::: spanguard.Redactor

### `Policy`

::: spanguard.Policy

### `RedactionResult`

::: spanguard.RedactionResult

## Types

Value objects returned as part of a `RedactionResult`.

### `Span`

::: spanguard.Span

### `AuditRecord`

::: spanguard.AuditRecord

## Extensibility

Implement this protocol to plug a custom detector into a `Redactor` — see
[Recognizers](recognizers.md) for a full worked example.

### `Recognizer`

::: spanguard.Recognizer

## Reversible redaction

Backs `tokenize` mode's `Redactor.reveal()`.

### `Keyring`

::: spanguard.Keyring

## Streaming

Redacts text that arrives in chunks — see [Streaming](streaming.md) for the
split-equals-one-shot guarantee.

### `StreamRedactor`

::: spanguard.StreamRedactor

### `StreamBufferFullError`

::: spanguard.StreamBufferFullError
