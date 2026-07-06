# Security Policy

spanguard is a library for detecting and redacting PII/PHI in text and
streaming transcripts. Because it is explicitly a security/privacy tool, we
treat vulnerability reports here as high priority — please read this policy
before reporting.

## Supported versions

spanguard is pre-1.0 and has not yet been published to PyPI (current version:
`0.1.0`). Until a stable `1.x` line exists, only the latest `0.x` release
receives security fixes.

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

This table will be revised once spanguard reaches a stable 1.0 release and
adopts a longer-lived support window.

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security vulnerability.**
Public issues are indexed and visible to everyone immediately, which is the
opposite of what you want for an unpatched redaction bypass.

Instead, please report privately using **GitHub's private vulnerability
reporting**:

1. Go to the [spanguard repository](https://github.com/Clufy/spanguard).
2. Click the **Security** tab.
3. Click **Report a vulnerability** to open a draft Security Advisory.

This creates a private conversation with the maintainer (@Clufy) that is not
visible to the public until you and the maintainer agree it's safe to
disclose. If you're unsure whether something rises to the level of a
security issue, it's fine to err on the side of reporting it this way rather
than as a public issue.

### What to include

- A minimal reproduction using **synthetic data only** — never paste real
  PII/PHI into a report, even a private one. Use placeholder values like
  `jane@example.com`, `555-123-4567`, or `123-45-6789`.
- The spanguard version, Python version, and relevant `Policy`/`Redactor`
  configuration.
- What you expected (e.g. "should be redacted" / "should not appear in the
  audit record") versus what actually happened.

## Scope

Examples of issues we consider **in scope** for a security report:

- **Audit record leakage** — any way `RedactionResult.audit` (or anything
  derived from it) ends up containing a raw matched value, a span's source
  text, or otherwise reconstructible sensitive data, rather than only
  entity-type counts, a policy hash, and a timestamp. This is the library's
  core guarantee, so a break here is treated as critical.
- **Redacted-output leakage** — raw PII/PHI surviving into `redact()` or
  `StreamRedactor.feed()`/`flush()` output when the configured policy says it
  should have been redacted, including at chunk boundaries in streaming mode.
- **Detector bypass** — a built-in `Recognizer` silently failing to detect an
  entity of a type it claims to support, for a realistic input format (as
  opposed to a documented, deliberate precision/recall trade-off — see
  `docs/known-limitations.md` for the ones we already know about and have
  decided not to change).
- **Key/token leakage** — `hmac_key`/`tokenize_key` material, or reversible
  tokens, ending up somewhere they shouldn't (e.g. logged, included in an
  audit record, or recoverable without the key via `reveal()` or otherwise).
- **CLI leakage** — `spanguard scan` printing raw matched values instead of
  counts, or `spanguard redact` writing raw values to a stream (e.g. stderr
  audit JSON) that should only ever carry redacted text or counts.

Examples of things that are generally **out of scope** (open a normal issue
or discussion instead):

- A detector missing an entity format that is already documented as a known
  limitation.
- General feature requests, performance issues without a security impact, or
  questions about how to configure a `Policy`.
- Vulnerabilities in dependencies (Pydantic, spaCy) themselves — please
  report those upstream, though we're happy to hear about them too if they
  affect spanguard's usage of them.

## Response expectations

This is a small, best-effort open-source project without a dedicated
security team or paid triage staff. We aim to:

- Acknowledge a new report within a few days.
- Give an initial assessment (in scope / out of scope, severity) once
  triaged.
- Work with you on a fix and coordinate a disclosure timeline before any
  public advisory or release notes go out, for anything confirmed as a real
  vulnerability.

There is no guaranteed SLA — please be patient, and feel free to follow up
on the advisory thread if you haven't heard back in a reasonable time.

## spanguard is a best-effort tool, not a compliance guarantee

spanguard aims to make PII/PHI redaction easier and safer to get right, and
its test suite specifically enforces the audit-record leak-free guarantee.
**It is not, by itself, a certification, compliance guarantee, or legal
assurance of HIPAA, GDPR, PCI-DSS, or any other regulatory compliance.**
Detectors are pattern- and model-based and have real, documented blind
spots — see [`docs/known-limitations.md`](docs/known-limitations.md) for the
current list (credit-card boundary handling, `API_KEY` generic-pattern
over-matching, `EMAIL` over-matching non-email tokens, NER model limitations,
and the ephemeral-key behavior for `hash`/`tokenize` modes).

If you are using spanguard as part of a compliance program, you are
responsible for validating it against your own data, threat model, and
regulatory requirements — including deciding whether additional detectors,
manual review, or a defense-in-depth approach is needed for your use case.
