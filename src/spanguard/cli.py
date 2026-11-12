"""Command-line interface: `spanguard scan` and `spanguard redact`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from spanguard.policy import DEFAULT_ENTITIES, Policy
from spanguard.redactor import Redactor

_STDIN = "-"


class _UsageError(Exception):
    """A user-facing error: printed as ``error: <msg>`` with exit code 2.

    Messages name paths and entity labels only, never input content.
    """


def _entities(value: str | None) -> tuple[str, ...]:
    if not value:
        return DEFAULT_ENTITIES
    entities = tuple(e.strip().upper() for e in value.split(",") if e.strip())
    unknown = [e for e in entities if e not in DEFAULT_ENTITIES]
    if unknown or not entities:
        # Silently skipping a typo would leave that type unredacted.
        raise _UsageError(
            f"unknown entity type(s): {', '.join(unknown) or '(none given)'}; "
            f"choose from {', '.join(DEFAULT_ENTITIES)}"
        )
    return entities


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spanguard",
        description="Detect and redact PII/PHI in text files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Report detected entity counts (no raw values).")
    scan.add_argument("file", help="Path to a UTF-8 text file to scan ('-' for stdin).")
    scan.add_argument("--entities", help="Comma-separated entity types (default: all).")
    scan.add_argument("--json", action="store_true", help="Emit the audit record as JSON.")

    red = sub.add_parser("redact", help="Write redacted text.")
    red.add_argument("file", help="Path to a UTF-8 text file to redact ('-' for stdin).")
    red.add_argument(
        "--mode",
        choices=["mask", "placeholder", "hash", "tokenize"],
        default="mask",
    )
    red.add_argument("--entities", help="Comma-separated entity types (default: all).")
    red.add_argument("--out", help="Write redacted text here (default: stdout).")
    red.add_argument(
        "--audit-json", action="store_true", help="Emit the audit record as JSON to stderr."
    )
    return parser


def _read_input(path: str) -> str:
    """Read `path` (or stdin for ``-``) as UTF-8, mapping failures to usage errors."""
    label = "<stdin>" if path == _STDIN else path
    try:
        if path == _STDIN:
            # Decode the raw bytes ourselves: the console/pipe default (e.g.
            # cp1252 on Windows) would silently mis-decode UTF-8 input.
            buffer = getattr(sys.stdin, "buffer", None)
            data = buffer.read() if buffer is not None else sys.stdin.read().encode("utf-8")
            return bytes(data).decode("utf-8")
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise _UsageError(f"file not found: {label}") from None
    except UnicodeDecodeError:
        raise _UsageError(f"cannot decode {label} as UTF-8") from None
    except OSError as exc:
        raise _UsageError(f"cannot read {label}: {exc.strerror or type(exc).__name__}") from None


def _cmd_scan(args: argparse.Namespace) -> int:
    policy = Policy(mode="placeholder", entities=_entities(args.entities))
    text = _read_input(args.file)
    result = Redactor(policy).redact(text)
    if args.json:
        print(json.dumps(
            {"counts": result.audit.counts,
             "policy_hash": result.audit.policy_hash,
             "ts": result.audit.ts}
        ))
    else:
        if result.audit.counts:
            for etype, count in sorted(result.audit.counts.items()):
                print(f"{etype}: {count}")
        else:
            print("No entities detected.")
    return 0


def _cmd_redact(args: argparse.Namespace) -> int:
    policy = Policy(mode=args.mode, entities=_entities(args.entities))
    text = _read_input(args.file)
    result = Redactor(policy).redact(text)
    if args.out:
        Path(args.out).write_text(result.text, encoding="utf-8")
    else:
        sys.stdout.write(result.text)
        if not result.text.endswith("\n"):
            sys.stdout.write("\n")
    if args.audit_json:
        sys.stderr.write(json.dumps(
            {"counts": result.audit.counts,
             "policy_hash": result.audit.policy_hash,
             "ts": result.audit.ts}
        ) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            return _cmd_scan(args)
        return _cmd_redact(args)
    except _UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
