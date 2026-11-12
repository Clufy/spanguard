# Changelog

All notable changes to spanguard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-11-12

### Fixed

- Install instructions quote the extra (`pip install "spanguard[ner]"`), so
  the command also works in zsh, the default macOS shell, where the unquoted
  form fails with "no matches found". No code changes.

## [0.1.0] - 2026-11-12

Initial release.

### Added

- **Entity detection** for `EMAIL` (Unicode-aware local part and domain),
  `PHONE` (NANP-style, multiple separator conventions), `SSN`, `MRN`
  (context-anchored on an `MRN` prefix), `DOB` (`mm/dd/yyyy` and ISO
  `yyyy-mm-dd`), `CREDIT_CARD` (regex plus Luhn checksum validation across
  standard printed groupings), and `API_KEY` (known-prefix formats such as
  `sk-`, `AKIA`, `ghp_`, plus a high-entropy generic fallback).
- **Four redaction modes** on every `Policy`: `mask` (fixed-character
  replacement, length-preserving), `placeholder` (`[TYPE]` tags), `hash`
  (deterministic HMAC digest, reproducible with a shared key), and
  `tokenize` (reversible placeholder tokens).
- **Reversible tokenization and reveal** — `Redactor.reveal()` restores the
  original text from `tokenize`-mode output via an in-memory `Keyring`,
  scoped to a single process/key.
- **`StreamRedactor`** for chunked/streaming input (e.g. live call
  transcripts or log tails), with a documented split-equals-one-shot
  guarantee: concatenating every `feed()` call's output plus a final
  `flush()` equals exactly what a one-shot `redact()` on the full text would
  produce, even when an entity straddles a chunk boundary. Enforces a
  minimum `tail` buffer of 64 characters to prevent sub-threshold entity
  leakage.
- **Optional NER extra** (`pip install spanguard[ner]`) adding a
  spaCy-backed `SpacyRecognizer` for `PERSON` and `LOCATION` detection,
  imported lazily so the core install stays dependency-light and fast to
  import.
- **`spanguard` CLI** with `scan` (report entity-type counts only, never raw
  values) and `redact` (write redacted text to stdout or a file, with an
  optional `--audit-json` audit record on stderr) subcommands.
  `-` reads stdin as UTF-8. An unknown `--entities` name, an unreadable,
  undecodable or missing input (including closed stdin), or an unwritable
  `--out` path exits with code 2 and a one-line `error:` message that names
  only the path or label, never input content.
- **Unknown-entity warning**: `Redactor` warns (`UserWarning`, entity labels
  only) when `Policy.entities` names a type with no recognizer, such as
  `PERSON` without `SpacyRecognizer` or a typo like `EMIAL`, instead of
  silently detecting nothing for it.
- **`StreamRedactor(max_buffer=N)`** and `StreamBufferFullError`: an opt-in
  cap on held-back text for streams that never offer a safe split point.
  Uncapped by default.
- **Leak-free audit records** — every `RedactionResult.audit` contains only
  entity-type counts, a policy hash, and a timestamp, never a raw matched
  value or span text; this guarantee is enforced directly by the test suite
  (`tests/test_audit_safety.py`), not just documented.
- **Pluggable `Recognizer` protocol** for adding custom, domain-specific
  detectors without forking the library.
- Full documentation site (mkdocs-material) covering quickstart, streaming,
  the CLI, recognizers, and an honest known-limitations page, published to
  [clufy.github.io/spanguard](https://clufy.github.io/spanguard).
- CI pipeline (ruff, mypy `--strict`, pytest with a 90% coverage gate) on
  every push and pull request; 128 tests at 97.92% coverage as of this
  release. Published to PyPI from GitHub Actions via OIDC Trusted
  Publishing on `v*` tags; no PyPI token is stored anywhere.

### Performance

Measured against the July 2026 pre-release build. Redaction output is
byte-identical; each change is pinned by a differential test against the
earlier algorithm.

| Path | Pre-release | 0.1.0 |
|---|---|---|
| `Redactor.redact`, 40k spans | 84.6 s | 0.84 s |
| `EmailRecognizer`, 8k-char token with no spaces | 844 ms (quadratic) | 0.6 ms (linear) |
| `Keyring.reveal`, 30k issued tokens | 11.2 s | 44 ms |
| `StreamRedactor`, 200 KB in 4 KB chunks | 304 ms | 194 ms |
| `StreamRedactor`, 1 MB with no whitespace | quadratic | linear |
| `StreamRedactor`, 200 KB whose only whitespace is inside a phone number | 8.49 s | 0.08 s |
| `benchmarks/throughput.py` (1 MB corpus) | 1.54 MB/s | 2.15 MB/s |

Overlap resolution is O(n log n), email detection cannot backtrack
quadratically on long whitespace-free runs (a denial-of-service vector),
`Keyring.reveal` is linear in the text, and `StreamRedactor` never re-detects
text it has already verified or split points it has already tried.

[unreleased]: https://github.com/Clufy/spanguard/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/Clufy/spanguard/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Clufy/spanguard/releases/tag/v0.1.0
