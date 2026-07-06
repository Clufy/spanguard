# Recognizers

A `Recognizer` detects one entity type in text. spanguard ships a default
set covering common PII/PHI, and you can plug in your own alongside (or
instead of) the built-ins.

## Built-in entity table

| Entity type   | Detector                          | Notes                                                             |
|---------------|------------------------------------|--------------------------------------------------------------------|
| `EMAIL`       | regex                              | Unicode local part and domain; requires a dotted TLD of >= 2 letters. |
| `PHONE`       | regex                              | NANP-style 3-3-4, optional `+country`, `-`/`.`/space/parens separators. |
| `SSN`         | regex                              | `###-##-####`.                                                     |
| `MRN`         | regex (context-anchored)           | Requires an `MRN` prefix; only the digit run is redacted.          |
| `DOB`         | regex                              | `mm/dd/yyyy` (1- or 2-digit month/day) or ISO `yyyy-mm-dd`.         |
| `CREDIT_CARD` | regex + Luhn checksum              | Contiguous 13-19 digits, or standard printed groupings; Luhn-validated. |
| `API_KEY`     | regex                              | Known prefixes (`sk-`, `AKIA`, `ghp_`) or a long high-entropy alnum run. |
| `PERSON`, `LOCATION` | spaCy NER (optional `[ner]` extra) | Requires `pip install spanguard[ner]` and a downloaded spaCy model. |

`Policy.entities` selects which of these run by default. Passing your own
`recognizers=[...]` to `Redactor` replaces entity-based auto-selection
entirely — you get exactly the recognizers you list.

## The `entity_type`-is-a-label contract

`Recognizer.entity_type` (and the `type` field of every `Span` it returns)
**must be a fixed, non-sensitive entity label** — e.g. `"EMAIL"`, `"ZIP"` —
**never a value derived from the matched text**. This label is what appears
verbatim in `placeholder` mode output (`[EMAIL]`) and as a key in the audit
record's `counts`. If you derived the label from the matched value, raw data
would leak into redacted output and into the audit trail — exactly what
spanguard exists to prevent.

## Writing a custom recognizer

A recognizer is any object with an `entity_type: str` attribute and a
`recognize(text: str) -> list[Span]` method — see the `Recognizer` protocol
in `spanguard.recognizers.base`. Here is a complete example that detects
5-digit US ZIP codes and plugs it into a `Redactor`:

<!-- custom-recognizer-example:start -->
```python
import re
from spanguard import Redactor, Policy, Span


class Zip5Recognizer:
    """Detects 5-digit US ZIP codes."""

    entity_type = "ZIP"

    def recognize(self, text):
        return [Span("ZIP", m.start(), m.end()) for m in re.finditer(r"\b\d{5}\b", text)]


policy = Policy(mode="placeholder", entities=("ZIP",))
redactor = Redactor(policy, recognizers=[Zip5Recognizer()])
result = redactor.redact("zip 90210 please")
print(result.text)
# zip [ZIP] please
print(result.audit.counts)
# {'ZIP': 1}
```
<!-- custom-recognizer-example:end -->

This exact snippet is executed by `tests/test_docs_examples.py`, so it
cannot silently drift out of sync with the library's API.

!!! note
    Passing `recognizers=[...]` overrides the `entities`-based default
    lookup entirely: only the recognizers you pass in are run, regardless
    of what `Policy.entities` lists. Combine your custom recognizer with
    the built-ins by importing them from
    `spanguard.recognizers.regex_recognizers.DEFAULT_RECOGNIZERS` if you
    want both.
