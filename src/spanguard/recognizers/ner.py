"""Optional spaCy NER recognizer (PERSON/LOCATION). Requires the [ner] extra."""

from __future__ import annotations

from typing import Any

from spanguard.result import Span

_DEFAULT_LABEL_MAP = {"PERSON": "PERSON", "GPE": "LOCATION", "LOC": "LOCATION"}


class SpacyRecognizer:
    """Detect PERSON/LOCATION entities via spaCy NER.

    spaCy is imported lazily so the base install stays light and `import
    spanguard` works without the [ner] extra. Pass `_nlp` to inject a loaded
    pipeline (used by tests) and skip the model load entirely.
    """

    def __init__(
        self,
        model: str = "en_core_web_sm",
        label_map: dict[str, str] | None = None,
        _nlp: Any | None = None,
    ) -> None:
        self.model = model
        self.label_map = dict(label_map) if label_map is not None else dict(_DEFAULT_LABEL_MAP)
        self._nlp = _nlp

    def _load(self) -> Any:
        if self._nlp is None:
            try:
                import spacy
            except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
                raise ImportError(
                    "SpacyRecognizer requires the optional 'ner' extra: "
                    "pip install spanguard[ner], then download a model "
                    "(python -m spacy download en_core_web_sm)."
                ) from exc
            self._nlp = spacy.load(self.model)
        return self._nlp

    def recognize(self, text: str) -> list[Span]:
        nlp = self._load()
        doc = nlp(text)
        spans: list[Span] = []
        for ent in doc.ents:
            mapped = self.label_map.get(ent.label_)
            if mapped is not None:
                spans.append(Span(type=mapped, start=ent.start_char, end=ent.end_char))
        return spans
