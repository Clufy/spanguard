"""Runs the custom-recognizer example embedded in docs/recognizers.md verbatim.

This guards against documentation rot: the code block between the
``<!-- custom-recognizer-example:start -->`` / ``:end`` markers in
docs/recognizers.md is extracted and exec'd exactly as written, then we
assert on the results it leaves behind. If anyone edits the doc snippet in a
way that breaks the API, this test fails.
"""

from __future__ import annotations

import re
from pathlib import Path

from spanguard import RedactionResult

_DOCS_PATH = Path(__file__).parent.parent / "docs" / "recognizers.md"
_START = "<!-- custom-recognizer-example:start -->"
_END = "<!-- custom-recognizer-example:end -->"


def _extract_example() -> str:
    text = _DOCS_PATH.read_text(encoding="utf-8")
    start = text.index(_START) + len(_START)
    end = text.index(_END, start)
    block = text[start:end]
    match = re.search(r"```python\n(.*?)```", block, re.DOTALL)
    assert match is not None, "expected a fenced python code block between the markers"
    return match.group(1)


def test_docs_recognizers_example_markers_present() -> None:
    text = _DOCS_PATH.read_text(encoding="utf-8")
    assert _START in text
    assert _END in text
    assert text.index(_START) < text.index(_END)


def test_custom_zip_recognizer_example_runs_and_matches_documented_output() -> None:
    source = _extract_example()
    namespace: dict[str, object] = {}
    exec(compile(source, str(_DOCS_PATH), "exec"), namespace)

    result = namespace["result"]
    assert isinstance(result, RedactionResult)
    assert result.text == "zip [ZIP] please"
    assert result.audit.counts == {"ZIP": 1}
