"""Smoke test for benchmarks/throughput.py: runs on a tiny input, fast, in CI.

Asserts only that the benchmark runs end-to-end and reports positive
throughput -- it must not depend on wall-clock magnitude (timing varies
across machines/CI), only on the shape and positivity of the result.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BENCHMARKS_DIR = Path(__file__).parent.parent / "benchmarks"
if str(_BENCHMARKS_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCHMARKS_DIR))

from throughput import generate_corpus, run_benchmark  # noqa: E402


def test_run_benchmark_on_tiny_input_returns_positive_throughput() -> None:
    corpus = generate_corpus(num_lines=20, seed=1)
    stats = run_benchmark(corpus)

    assert stats["mb_per_sec"] > 0
    assert stats["entities_per_sec"] > 0
    assert stats["entity_count"] > 0
    assert stats["elapsed_sec"] > 0
    assert stats["bytes"] == len(corpus.encode("utf-8"))


def test_generate_corpus_is_deterministic() -> None:
    first = generate_corpus(num_lines=10, seed=42)
    second = generate_corpus(num_lines=10, seed=42)
    assert first == second


def test_generate_corpus_contains_no_real_pii_markers() -> None:
    # Synthetic corpus only: fabricated example.{com,org,net}/test.invalid emails,
    # never a real domain. Use enough lines to guarantee at least one PII line
    # (PII appears on only every Nth line by design).
    corpus = generate_corpus(num_lines=40, seed=1)
    assert any(domain in corpus for domain in ("example.com", "example.org", "example.net"))
