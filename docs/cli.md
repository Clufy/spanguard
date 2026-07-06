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

## Notes

- Both commands read the input file as UTF-8.
- `scan` always resolves an internal `placeholder` policy to compute counts;
  it never writes the redacted text anywhere.
- The CLI forces its stdout/stderr streams to UTF-8 so `mask` mode's
  `█` mask character never crashes on a non-UTF-8 console.
- A missing input file exits with code `2` and an `error: file not found: ...`
  message on stderr.
