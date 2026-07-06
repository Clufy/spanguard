# Changelog

All notable changes to spanguard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.1.0] - 2026-07-06

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
  every push and pull request; 97 tests at 96.92% coverage as of this
  release. Publishing to PyPI is wired up via GitHub Actions OIDC Trusted
  Publishing on `v*` tags (not yet used — spanguard is not yet published to
  PyPI as of 0.1.0).

[unreleased]: https://github.com/Clufy/spanguard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Clufy/spanguard/releases/tag/v0.1.0
