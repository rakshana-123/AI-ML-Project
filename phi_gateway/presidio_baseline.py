"""Microsoft Presidio baseline over the hand-labelled test set.

Presidio's analyzer (default recognizer registry + spaCy NLP engine) is run
on every test note; recognised entities are mapped onto our type space:

    PERSON            -> NAME
    LOCATION          -> LOCATION
    DATE_TIME         -> DATE
    PHONE_NUMBER      -> PHONE
    EMAIL_ADDRESS     -> EMAIL
    US_SSN            -> SSN
    IP_ADDRESS        -> IP
    URL               -> URL
    US_DRIVER_LICENSE -> LICENSE
    AGE / US_PASSPORT / ... kept as-is when they match our types

Presidio has no default recognisers for medical record numbers, health-plan
IDs or account numbers - a documented gap, not a bug in our adapter.
Results are written to results/presidio_preds.jsonl for evaluate.py.

Run: python -m phi_gateway.presidio_baseline
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
DATA_DIR = ROOT / "data"

TYPE_MAP = {
    "PERSON": "NAME",
    "LOCATION": "LOCATION",
    "DATE_TIME": "DATE",
    "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL",
    "US_SSN": "SSN",
    "IP_ADDRESS": "IP",
    "URL": "URL",
    "US_DRIVER_LICENSE": "LICENSE",
    "AGE": "AGE",
    "MEDICAL_RECORD": "MRN",
    "US_PASSPORT": "LICENSE",
    "US_ITIN": "SSN",
}


def make_analyzer():
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    # prefer the large spaCy model (Presidio's recommendation), fall back
    # to the small one if it is not installed
    import spacy
    model = "en_core_web_lg"
    try:
        spacy.load(model)
    except OSError:
        model = "en_core_web_sm"
        spacy.load(model)          # raise if neither is present

    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": model}],
    })
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(
        languages=["en"], nlp_engine=provider.create_engine())
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=["en"],
    )
    return analyzer, model


def run(split: str = "test") -> None:
    analyzer, model = make_analyzer()
    print(f"presidio nlp engine: {model}")
    RESULTS_DIR.mkdir(exist_ok=True)
    notes = [json.loads(l) for l in
             open(DATA_DIR / f"{split}.jsonl", encoding="utf-8")]
    out_path = RESULTS_DIR / f"presidio_preds_{split}.jsonl"
    n_ents = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for note in notes:
            results = analyzer.analyze(text=note["text"], language="en")
            ents = []
            for r in results:
                mapped = TYPE_MAP.get(r.entity_type)
                if mapped is None:
                    continue
                ents.append({"start": r.start, "end": r.end,
                             "label": mapped,
                             "presidio_type": r.entity_type,
                             "score": r.score})
            n_ents += len(ents)
            f.write(json.dumps({"id": note["id"], "entities": ents}) + "\n")
    # evaluate.py expects the canonical filename for the test split
    if split == "test":
        (RESULTS_DIR / "presidio_preds.jsonl").write_text(
            out_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote {n_ents} entities for {len(notes)} notes -> {out_path}")


if __name__ == "__main__":
    run()
