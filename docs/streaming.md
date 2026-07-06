# Streaming

`StreamRedactor` redacts text that arrives in chunks — e.g. a live call
transcript or a log tail — without buffering the whole document and without
letting an entity that straddles a chunk boundary leak out unredacted.

## Usage

```python
from spanguard import Redactor, Policy, StreamRedactor

policy = Policy(mode="placeholder", entities=("EMAIL", "PHONE"))
redactor = Redactor(policy)
stream = StreamRedactor(redactor)

output = []
for chunk in ["mail jane@ex", "ample.com or call ", "555-123-4567 now"]:
    output.append(stream.feed(chunk))
output.append(stream.flush())

print("".join(output))
# mail [EMAIL] or call [PHONE] now
```

`feed(chunk)` appends `chunk` to an internal buffer and returns as much
redacted text as it can safely emit right now; anything still pending
(because an entity might extend into the next chunk) is held back.
`flush()` must be called at the end of the stream to redact and emit
whatever remains in the buffer.

## The split-equals-one-shot guarantee

For any way you choose to split a text into chunks, the concatenation of
every `feed()` call's return value plus the final `flush()` equals exactly
what `redactor.redact(full_text).text` would have produced — for every mode
(`mask`, `placeholder`, `hash`, `tokenize`), given the same keys. This holds
even when an entity is split across a chunk boundary (e.g. an email cut
right after the `@`) or when an entity needs left context that arrived in an
earlier chunk (e.g. an `MRN:` prefix).

## The `tail` floor (>= 64) and why it exists

`StreamRedactor(redactor, tail=128)` holds back `tail` characters at the end
of the buffer before considering a cut safe. `tail` must be `>= 64` — passing
a smaller value raises `ValueError` immediately.

The floor exists to prevent a specific leak: an entity that **contains
internal separators** (e.g. a spaced credit card number, `4111 1111 1111
1111`) is emitted piece by piece if the buffer never holds enough of it at
once for detection to fire. Below the floor, every whitespace character can
look like a "safe" cut point even though the full entity would have matched
across it — so the raw digits stream out in sub-threshold fragments that
never trigger a match. Keeping at least 64 characters in reserve guarantees
enough of the buffer is re-checked as a whole before any cut is made.

## The long-entity ceiling

An entity **longer than `tail`** with no internal separators the cutter can
anchor on (e.g. a very long, unbroken email address or API key) degrades
gracefully: `StreamRedactor` falls back to the nearest safe word-boundary
split rather than holding the buffer forever. In practice this means such an
entity is still fully redacted (never leaked in pieces), but the boundary
where redacted output is emitted may lag by up to roughly `tail` +
one chunk's worth of characters. Memory usage is bounded by `tail` plus one
chunk at all times — `StreamRedactor` never buffers an entire unbounded
stream.
