from dataclasses import dataclass

from spanguard.recognizers.ner import SpacyRecognizer
from spanguard.result import Span


@dataclass
class _FakeEnt:
    label_: str
    start_char: int
    end_char: int


class _FakeDoc:
    def __init__(self, ents: list[_FakeEnt]) -> None:
        self.ents = ents


class _FakeNLP:
    """Stand-in for a loaded spaCy pipeline: callable text -> doc with .ents."""

    def __init__(self, ents_for: dict[str, list[_FakeEnt]]) -> None:
        self._ents_for = ents_for

    def __call__(self, text: str) -> _FakeDoc:
        return _FakeDoc(self._ents_for.get(text, []))


def test_maps_person_and_location_labels() -> None:
    text = "Jane lives in Paris"
    nlp = _FakeNLP({text: [
        _FakeEnt("PERSON", 0, 4),
        _FakeEnt("GPE", 14, 19),
    ]})
    rec = SpacyRecognizer(_nlp=nlp)
    spans = rec.recognize(text)
    assert Span("PERSON", 0, 4) in spans
    assert Span("LOCATION", 14, 19) in spans
    assert len(spans) == 2


def test_unmapped_labels_are_ignored() -> None:
    text = "Acme raised $5M"
    nlp = _FakeNLP({text: [
        _FakeEnt("ORG", 0, 4),      # not in label_map -> ignored
        _FakeEnt("MONEY", 12, 14),  # ignored
    ]})
    rec = SpacyRecognizer(_nlp=nlp)
    assert rec.recognize(text) == []


def test_custom_label_map() -> None:
    text = "Contact Bob"
    nlp = _FakeNLP({text: [_FakeEnt("PERSON", 8, 11)]})
    rec = SpacyRecognizer(_nlp=nlp, label_map={"PERSON": "NAME"})
    assert rec.recognize(text) == [Span("NAME", 8, 11)]


def test_missing_spacy_raises_clear_import_error(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Simulate spaCy not installed: _load() import fails.
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "spacy":
            raise ModuleNotFoundError("No module named 'spacy'")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", fake_import)
    rec = SpacyRecognizer()  # no _nlp injected -> will try to import spacy on use
    try:
        rec.recognize("Jane in Paris")
    except ImportError as e:
        assert "ner" in str(e).lower()          # names the extra
        assert "Jane" not in str(e)             # no input text leaked
        return
    raise AssertionError("expected ImportError when spaCy is missing")
