# CLI

spanguard installs a `spanguard` command with two subcommands: `scan`
(report what would be redacted, without ever printing raw values) and
`redact` (write the redacted text).

Given a file `notes.txt`:

```text
Patient contacted via jane@example.com or 555-123-4567.
SSN on file: 123-45-6789.
```

## `spanguard scan`

Reports entity-type counts only — never the matched raw values.

```console
$ spanguard scan notes.txt
EMAIL: 1
PHONE: 1
SSN: 1
```

Restrict to specific entity types with `--entities` (comma-separated):

```console
$ spanguard scan notes.txt --entities EMAIL,PHONE
EMAIL: 1
PHONE: 1
```

Emit the audit record as JSON with `--json`:

```console
$ spanguard scan notes.txt --json
{"counts": {"EMAIL": 1, "PHONE": 1, "SSN": 1}, "policy_hash": "e064cd5139c733ed", "ts": "2026-07-06T00:55:46.523122+00:00"}
```

## `spanguard redact`

Writes redacted text to stdout (or a file with `--out`).

```console
$ spanguard redact notes.txt --mode placeholder
Patient contacted via [EMAIL] or [PHONE].
SSN on file: [SSN].
```

`--mode` accepts `mask` (default), `placeholder`, `hash`, or `tokenize`.
`--entities` filters which entity types are redacted, same as `scan`:

```console
$ spanguard redact notes.txt --mode mask --entities EMAIL,PHONE
Patient contacted via ████████████████ or ████████████.
SSN on file: 123-45-6789.
```

Write to a file instead of stdout:

```console
$ spanguard redact notes.txt --mode placeholder --out redacted.txt
```

Emit the audit record as JSON to **stderr** (so it never mixes with the
redacted text on stdout) with `--audit-json`:

```console
$ spanguard redact notes.txt --mode placeholder --audit-json > redacted.txt
```

## Reading from stdin

Pass `-` as the file to read standard input, so spanguard can sit in a
pipeline:

```console
$ cat notes.txt | spanguard redact - --mode placeholder > redacted.txt
$ some-transcriber --live | spanguard scan - --json
```

## Exit codes and errors

| Code | Meaning |
|---|---|
| `0` | Success. |
| `2` | Usage or input error, printed as `error: ...` on stderr. Nothing is written to stdout. |

Error messages name the path or entity label involved and **never** echo any
input content:

```console
$ spanguard redact notes.txt --entities EMIAL
error: unknown entity type(s): EMIAL; choose from EMAIL, PHONE, SSN, MRN, DOB, CREDIT_CARD, API_KEY
$ spanguard scan latin1.txt
error: cannot decode latin1.txt as UTF-8
$ spanguard scan missing.txt
error: file not found: missing.txt
```

An unknown `--entities` name is an error rather than being skipped, because
silently ignoring a typo would leave that entity type unredacted. `PERSON`
and `LOCATION` (spaCy NER) are library-only; see
[Recognizers](recognizers.md).

## Notes

- Both commands read their input (file or stdin) as UTF-8.
- `scan` always resolves an internal `placeholder` policy to compute counts;
  it never writes the redacted text anywhere.
- The CLI forces its stdout/stderr streams to UTF-8 so `mask` mode's
  `█` mask character never crashes on a non-UTF-8 console.
