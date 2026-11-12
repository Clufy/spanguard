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

!!! note "Chunking never changes the output"
    For any way you choose to split a text into chunks, the concatenation of
    every `feed()` call's return value plus the final `flush()` equals
    exactly what `redactor.redact(full_text).text` would have produced — for
    every mode (`mask`, `placeholder`, `hash`, `tokenize`), given the same
    keys.

This holds even when an entity is split across a chunk boundary (e.g. an
email cut right after the `@`) or when an entity needs left context that
arrived in an earlier chunk (e.g. an `MRN:` prefix).

## The `tail` floor (>= 64) and why it exists

`StreamRedactor(redactor, tail=128)` holds back `tail` characters at the end
of the buffer before considering a cut safe.

!!! warning "`tail` must be >= 64"
    Passing a smaller value raises `ValueError` immediately — this floor is
    not a tunable performance knob, it's a correctness requirement.

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
one chunk's worth of characters.

## Memory and `max_buffer`

Output is emitted only up to a whitespace character that no entity
straddles. While the stream keeps supplying such separators, as ordinary
prose and transcripts do, the buffer stays near `tail` plus one chunk.

A stream that never supplies one is held in full until it does, or until
you call `flush()`. Examples are a long base64 blob, or text whose only
whitespace sits inside a phone number. Cutting such a stream anyway could
emit half of an email address unredacted, so spanguard never does it on its
own.

To cap memory, pass `max_buffer`. When a `feed()` leaves more than
`max_buffer` characters held and nothing could be emitted, it raises
`StreamBufferFullError`. The message gives sizes only, never content:

```python
from spanguard import Policy, Redactor, StreamBufferFullError, StreamRedactor

stream = StreamRedactor(Redactor(Policy(mode="placeholder")), max_buffer=1_000_000)
try:
    out = stream.feed(chunk)
except StreamBufferFullError:
    # Nothing was dropped. Either emit what is held (an entity still
    # arriving may then be split at this point) or abandon the stream.
    out = stream.flush()
```

`max_buffer` must be greater than `tail`. It defaults to `None` (no cap), so
existing callers behave as before.
