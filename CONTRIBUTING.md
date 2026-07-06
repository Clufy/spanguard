# Contributing to spanguard

Thanks for considering a contribution to spanguard. spanguard detects and
redacts PII/PHI, so correctness and test rigor matter more here than in a
typical library — a missed detector or a leaky audit record is a real privacy
bug, not just a wrong answer. This guide covers environment setup, the checks
your PR needs to pass, and the conventions the codebase follows.

## Development environment

spanguard uses [`uv`](https://docs.astral.sh/uv/) for environment and
dependency management. Install `uv` first, then:

```bash
git clone https://github.com/Clufy/spanguard.git
cd spanguard
uv venv --python 3.12
```

Install the package in editable mode with the `ner` extra (needed to run the
full test suite, including the spaCy-backed recognizer tests) plus the dev
tools:

```bash
uv pip install -e ".[ner]" pytest pytest-cov ruff mypy
```

If you're working on NER (`PERSON`/`LOCATION`) specifically, you'll also want
a downloaded spaCy model:

```bash
uv run python -m spacy download en_core_web_sm
```

From here on, run everything through `uv run` so it executes inside the
project's virtualenv without needing to activate it manually.

## Running the checks

Every PR needs to pass lint, type-check, and tests before review. Run all
three locally before pushing — this is exactly what CI runs:

```bash
uv run ruff check .
uv run mypy
uv run pytest --cov=spanguard --cov-report=term-missing --cov-fail-under=90
```

For a quick local loop while iterating, plain `uv run pytest` is fine; add
the `--cov*` flags before you open a PR to confirm you haven't dropped
coverage below the gate.

## Coding standards

- **`mypy --strict` clean.** The project's `[tool.mypy]` config sets
  `strict = true` over `src`, `tests`, and `benchmarks`. Untyped defs,
  implicit `Any`, and missing return types will fail CI. New public APIs need
  complete type annotations, including `Protocol`-based structural types
  where appropriate (see `Recognizer` in `src/spanguard/recognizers/base.py`).
- **`ruff check .` clean.** Ruff is configured with `select = ["E", "F", "I",
  "UP", "B", "SIM", "RUF"]` (pyflakes, pycodestyle, isort, pyupgrade,
  bugbear, simplify, ruff-specific) at a 100-character line length,
  targeting Python 3.12. Run `uv run ruff check . --fix` for anything
  auto-fixable, then review the diff.
- **Tests are required, not optional, for behavior changes.** The suite
  currently sits at 97 tests and 96.92% statement+branch coverage; the CI
  gate fails any run under 90%. A PR that drops coverage below the gate, or
  that adds a detector/feature with no tests, will not be merged.
- **Never let raw matched values leak into non-text output.** This is the
  core invariant of the library: `AuditRecord` (see
  `src/spanguard/result.py`) must only ever contain entity-type counts, a
  policy hash, and a timestamp — never the matched substrings, never span
  text. If you touch anything in the redaction, audit, or streaming path,
  add or update a test in `tests/test_audit_safety.py` asserting the raw
  input text does not appear anywhere in the audit record.

## Adding a new detector (`Recognizer`)

Custom and built-in detectors both implement the `Recognizer` protocol
(`src/spanguard/recognizers/base.py`):

```python
from typing import Protocol, runtime_checkable
from spanguard.result import Span

@runtime_checkable
class Recognizer(Protocol):
    entity_type: str

    def recognize(self, text: str) -> list[Span]: ...
```

A few rules that fall directly out of the audit-safety guarantee above:

- `entity_type` must be a fixed, non-sensitive **label** (e.g. `"EMAIL"`),
  never anything derived from the matched text. That label appears verbatim
  in placeholder output (`[EMAIL]`) and as a key in `audit.counts`.
- `recognize()` must return **non-overlapping** spans for its own entity
  type; overlap resolution across recognizers is handled centrally (see
  `src/spanguard/_overlap.py`), not by individual recognizers.

When you add or change a detector, include **both**:

1. **Positive tests** — text that should match, asserting the exact span
   boundaries and/or count for representative real-world formats.
2. **Negative tests** — text that looks similar but should *not* match
   (false-positive guards), and/or entity text that is deliberately outside
   the detector's supported format (false-negative documentation). Look at
   `tests/test_recognizers.py` for the existing pattern per entity type —
   e.g. the credit-card recognizer tests both Luhn-valid card numbers in
   several groupings *and* Luhn-invalid or boundary-adjacent digit runs that
   must be left alone.

If a detector has a known, deliberate blind spot (a precision/recall
trade-off, not a bug), document it in `docs/known-limitations.md` rather than
silently shipping it — see the existing entries for `CREDIT_CARD`,
`API_KEY`, and `EMAIL` for the expected level of detail.

## Commit messages

This repo follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short summary>
```

Types used in this repo's history: `feat`, `fix`, `docs`, `refactor`,
`chore`, `ci`, `test`. Examples from the actual log:

```
feat: add StreamRedactor with boundary-safe chunked redaction
fix: enforce StreamRedactor tail floor (64) to prevent sub-threshold entity leak
docs: note EMAIL over-match of @-bearing non-email tokens in known limitations
ci: add lint/type/test+coverage gate, OIDC publish, Pages docs, and README
```

Keep the summary line imperative and under ~72 characters; put rationale in
the body if the "why" isn't obvious from the diff.

## Pull request process

1. Fork the repo and create a branch off `master`.
2. Make your change, with tests, following the standards above.
3. Run `ruff check .`, `mypy`, and `pytest --cov=spanguard --cov-fail-under=90`
   locally — all three must pass clean before you open the PR (CI runs the
   same three commands on every push and PR).
4. Update `docs/` if you changed or added user-facing behavior (a new
   detector, a new CLI flag, a new redaction mode) — undocumented behavior
   is treated as incomplete.
5. Open a PR with a title following the Conventional Commits format above.
   Describe *what* changed and *why*; link any related issue.
6. **Never include real PII/PHI in test fixtures, examples, or PR
   descriptions** — synthetic data only (e.g. `jane@example.com`,
   `555-123-4567`, `123-45-6789`). This applies even when demonstrating a bug
   with detector false negatives on realistic-looking input.
7. A maintainer will review, and CI must be green before merge.

## Reporting security issues

Please do not open a public issue for a security vulnerability (e.g. a way
raw PII/PHI can leak through the audit record, logs, or streaming output, or
a detector silently failing to redact something it claims to cover). See
[SECURITY.md](SECURITY.md) for how to report privately.
