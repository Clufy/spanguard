"""Command-line interface: `spanguard scan` and `spanguard redact`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from spanguard.policy import DEFAULT_ENTITIES, Policy
from spanguard.redactor import Redactor


def _entities(value: str | None) -> list[str]:
    if not value:
        return list(DEFAULT_ENTITIES)
    return [e.strip().upper() for e in value.split(",") if e.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spanguard",
        description="Detect and redact PII/PHI in text files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Report detected entity counts (no raw values).")
    scan.add_argument("file", help="Path to a UTF-8 text file to scan.")
    scan.add_argument("--entities", help="Comma-separated entity types (default: all).")
    scan.add_argument("--json", action="store_true", help="Emit the audit record as JSON.")

    red = sub.add_parser("redact", help="Write redacted text.")
    red.add_argument("file", help="Path to a UTF-8 text file to redact.")
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


def _read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _cmd_scan(args: argparse.Namespace) -> int:
    text = _read_file(args.file)
    policy = Policy(mode="placeholder", entities=_entities(args.entities))
    result = Redactor(policy).redact(text)
    assert result.audit is not None
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
    text = _read_file(args.file)
    policy = Policy(mode=args.mode, entities=_entities(args.entities))
    result = Redactor(policy).redact(text)
    assert result.audit is not None
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
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
