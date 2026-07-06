## Summary

<!-- What does this change do, and why? Link any related issue. -->

## Checklist

- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/) (`feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `chore: ...`, `ci: ...`, `test: ...`).
- [ ] Tests added/updated for the change, including **both positive and negative cases** if this touches a `Recognizer` (see `CONTRIBUTING.md`).
- [ ] `uv run ruff check .` passes clean.
- [ ] `uv run mypy` passes clean (`strict = true` — no new untyped defs or `Any` leaks).
- [ ] `uv run pytest --cov=spanguard --cov-report=term-missing --cov-fail-under=90` passes and coverage is maintained (currently 96.92%; gate is 90%).
- [ ] Docs updated under `docs/` if this changes or adds user-facing behavior (new detector, new CLI flag, new redaction mode, etc.), including `docs/known-limitations.md` if this introduces a deliberate precision/recall trade-off.
- [ ] `CHANGELOG.md` updated under `[Unreleased]` if this is a user-visible change.
- [ ] **No real PII/PHI in tests, examples, fixtures, or this PR description** — synthetic data only (e.g. `jane@example.com`, `555-123-4567`, `123-45-6789`).
- [ ] If this touches redaction, audit records, or streaming: confirmed no raw matched value can reach `RedactionResult.audit`, redacted output (when it shouldn't), or CLI `scan` output.

## Additional context

<!-- Anything a reviewer needs to know: design trade-offs, alternatives considered, follow-up work, etc. -->
