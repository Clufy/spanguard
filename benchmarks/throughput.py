"""Throughput benchmark for Redactor.redact() over a synthetic ~1MB corpus.

Generates a deterministic, purely synthetic corpus (fabricated emails,
phones, SSNs, credit cards -- no real PII) and times Redactor.redact() with
time.perf_counter, reporting MB/s and entities/s.

Run directly:

    uv run python benchmarks/throughput.py

Or import `run_benchmark` / `generate_corpus` (e.g. from
tests/test_benchmark_smoke.py) to exercise it on a tiny input in CI without
depending on wall-clock magnitude.
"""

from __future__ import annotations

import random
import time
from typing import TypedDict

from spanguard import Policy, Redactor

_DEFAULT_SEED = 20260706
_TARGET_BYTES = 1_000_000

_FIRST_NAMES = ("alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi")
_DOMAINS = ("example.com", "example.org", "example.net", "test.invalid")
_FILLER_WORDS = (
    "the quarterly report was filed after the meeting concluded and the team "
    "moved on to the next agenda item without further discussion",
    "please review the attached notes before the call tomorrow morning since "
    "several open questions still need an answer from the working group",
    "our team completed the migration ahead of schedule this sprint and "
    "logged the results in the shared tracking document for reference",
    "the incident was resolved without any customer impact today after "
    "engineering rolled back the change and verified the affected systems",
    "thanks for the update, I will follow up with the vendor next week once "
    "the paperwork has been signed and returned to our procurement team",
)


class BenchmarkStats(TypedDict):
    bytes: int
    elapsed_sec: float
    mb_per_sec: float
    entity_count: int
    entities_per_sec: float


_PII_EVERY_N_LINES = 8
"""Only every Nth line carries fabricated PII; the rest is plain prose filler.

This mirrors a realistic document mix (most text is prose, PII is sparse)
rather than an adversarial worst case, and keeps the benchmark's runtime
reasonable for a ~1MB corpus.
"""


def _synthetic_line(rng: random.Random, index: int) -> str:
    """One deterministic synthetic line, occasionally with fabricated PII-shaped patterns."""
    filler = rng.choice(_FILLER_WORDS)
    if index % _PII_EVERY_N_LINES != 0:
        return f"line {index}: {filler}."
    first = rng.choice(_FIRST_NAMES)
    domain = rng.choice(_DOMAINS)
    email = f"user{index}.{first}@{domain}"
    phone = f"555-{rng.randint(0, 99):02d}xx-{rng.randint(0, 9999):04d}"
    ssn = f"{rng.randint(100, 899):03d}-{rng.randint(10, 99):02d}-{rng.randint(1000, 9999):04d}"
    return f"line {index}: {filler}. contact {email} or {phone}. ref ssn {ssn}."


def generate_corpus(num_lines: int, seed: int = _DEFAULT_SEED) -> str:
    """Deterministic synthetic corpus of `num_lines` lines (fixed seed => fixed output)."""
    rng = random.Random(seed)
    lines = [_synthetic_line(rng, i) for i in range(num_lines)]
    return "\n".join(lines) + "\n"


def generate_corpus_of_size(target_bytes: int = _TARGET_BYTES, seed: int = _DEFAULT_SEED) -> str:
    """Deterministic synthetic corpus of approximately `target_bytes` UTF-8 bytes."""
    rng = random.Random(seed)
    lines: list[str] = []
    total = 0
    i = 0
    while total < target_bytes:
        line = _synthetic_line(rng, i)
        lines.append(line)
        total += len(line.encode("utf-8")) + 1  # +1 for the newline
        i += 1
    return "\n".join(lines) + "\n"


def run_benchmark(corpus: str, policy: Policy | None = None) -> BenchmarkStats:
    """Time Redactor.redact() over `corpus`; return throughput stats."""
    policy = policy or Policy(mode="placeholder")
    redactor = Redactor(policy, hmac_key=b"benchmark-key", tokenize_key=b"benchmark-key")

    start = time.perf_counter()
    result = redactor.redact(corpus)
    elapsed = time.perf_counter() - start

    num_bytes = len(corpus.encode("utf-8"))
    entity_count = sum(result.audit.counts.values())
    # Guard against a (practically impossible on real hardware) zero-duration
    # measurement so mb_per_sec/entities_per_sec stay finite and positive.
    safe_elapsed = max(elapsed, 1e-9)

    return {
        "bytes": num_bytes,
        "elapsed_sec": elapsed,
        "mb_per_sec": (num_bytes / (1024 * 1024)) / safe_elapsed,
        "entity_count": entity_count,
        "entities_per_sec": entity_count / safe_elapsed,
    }


def main() -> None:
    corpus = generate_corpus_of_size(_TARGET_BYTES)
    stats = run_benchmark(corpus)
    print(f"corpus: {stats['bytes'] / (1024 * 1024):.2f} MB")
    print(f"elapsed: {stats['elapsed_sec']:.4f} s")
    print(f"throughput: {stats['mb_per_sec']:.2f} MB/s")
    print(f"entities detected: {stats['entity_count']}")
    print(f"entity throughput: {stats['entities_per_sec']:.0f} entities/s")


if __name__ == "__main__":
    main()
