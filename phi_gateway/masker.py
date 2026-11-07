"""The PHI gateway: deidentify(text) -> (masked_text, mapping) and back.

Design (recall-first):
  1. Candidate spans = neural NER spans  UNION  rule-layer spans.
  2. Overlapping spans merge into one mask; the rule label wins type
     disputes (regexes are near-perfect on their formats).
  3. Same value (whitespace/case-insensitive) inside a note always maps to
     the same placeholder, e.g. [NAME_1].
  4. SAFETY NET: after masking, the masked text is re-scanned with the rule
     layer; any identifier the merge step somehow missed gets masked too
     ("late catches" - reported so leaks cannot hide).

Rehydration replaces placeholders longest-first ([NAME_10] before [NAME_1])
and leaves unknown placeholders (hallucinated by the LLM) untouched while
recording them, since they carry no PHI.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

from .inference import ModelNER
from .labels import ENTITY_TYPES
from .rules import rule_spans

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "distilbert-phi"
PLACEHOLDER_RX = re.compile(r"\[(" + "|".join(ENTITY_TYPES) + r")_(\d+)\]")

# rule labels win disputes inside a merged cluster
RULE_PRIORITY = {"SSN", "PHONE", "EMAIL", "URL", "IP", "DATE", "AGE",
                 "MRN", "HEALTHPLAN", "ACCOUNT", "LICENSE"}


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


def merge_spans(spans: list[dict]) -> list[dict]:
    """Union of spans; overlapping/adjacent-overlapping spans merge."""
    spans = [s for s in spans if s["end"] > s["start"]]
    spans.sort(key=lambda s: (s["start"], -s["end"]))
    merged: list[dict] = []
    for s in spans:
        if merged and s["start"] < merged[-1]["end"]:
            prev = merged[-1]
            prev["end"] = max(prev["end"], s["end"])
            if s["label"] in RULE_PRIORITY and prev["label"] not in RULE_PRIORITY:
                prev["label"] = s["label"]
            prev["rule"] = prev.get("rule", False) or s.get("rule", False)
        else:
            merged.append(dict(s))
    # after merging, drop any span fully contained in the previous one
    out: list[dict] = []
    for s in merged:
        if out and s["end"] <= out[-1]["end"]:
            continue
        out.append(s)
    return out


class PHIGateway:
    """deidentify / rehydrate gateway over a fine-tuned model + rules."""

    def __init__(self, model_dir: str | Path | None = None, use_model: bool = True):
        self.ner = None
        if use_model:
            model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
            if (model_dir / "config.json").exists():
                self.ner = ModelNER(str(model_dir))
            else:
                print(f"[gateway] no model at {model_dir}; running RULES-ONLY")
        self.last_report: dict = {}

    # ------------------------------------------------------------------ API
    def deidentify(self, text: str, return_entities: bool = False):
        """mask identifiers -> (masked_text, mapping {placeholder: value})"""
        spans: list[dict] = []
        if self.ner:
            spans += self.ner.predict_spans(text)
        for s in rule_spans(text):
            s["rule"] = True
            spans.append(s)
        spans = merge_spans(spans)

        mapping: "OrderedDict[str, str]" = OrderedDict()
        keys: dict[tuple[str, str], str] = {}
        counters: dict[str, int] = {}
        late_catches = 0

        def placeholder_for(value: str, etype: str) -> str:
            nonlocal late_catches
            key = (_norm(value), etype)
            if key in keys:
                return keys[key]
            counters[etype] = counters.get(etype, 0) + 1
            ph = f"[{etype}_{counters[etype]}]"
            keys[key] = ph
            mapping[ph] = value
            return ph

        # pass 1: mask merged spans (left to right over the original text)
        out = []
        cursor = 0
        for s in spans:
            out.append(text[cursor:s["start"]])
            out.append(placeholder_for(text[s["start"]:s["end"]], s["label"]))
            cursor = s["end"]
        out.append(text[cursor:])
        masked = "".join(out)

        # pass 2 (safety net): re-scan the masked text; anything the rules
        # still find there was missed by the merge - mask it too
        for _ in range(3):
            residual = rule_spans(masked)
            if not residual:
                break
            for r in sorted(residual, key=lambda r: r["start"], reverse=True):
                value = masked[r["start"]:r["end"]]
                ph = placeholder_for(value, r["label"])
                late_catches += 1
                masked = masked[:r["start"]] + ph + masked[r["end"]:]

        self.last_report = {
            "entities": len(mapping),
            "late_catches": late_catches,
            "mapping": mapping,
        }
        if return_entities:
            ents = [{k: s.get(k) for k in ("start", "end", "label")}
                    for s in spans]
            for e in ents:
                e["value"] = text[e["start"]:e["end"]]
            self.last_report["entity_list"] = ents
            return masked, mapping, ents
        return masked, mapping

    def rehydrate(self, response: str, mapping: dict) -> str:
        """restore original values; unknown placeholders left untouched."""
        unknown = []

        def _sub(m: re.Match) -> str:
            ph = m.group(0)
            if ph in mapping:
                return mapping[ph]
            unknown.append(ph)
            return ph           # no data risk in leaving an unknown tag

        restored = PLACEHOLDER_RX.sub(_sub, response)
        self.last_report = {"unknown_placeholders": unknown}
        return restored

    # convenience round trip -------------------------------------------
    def round_trip(self, text: str, llm, prompt_builder=None) -> dict:
        masked, mapping = self.deidentify(text)
        prompt = (prompt_builder(masked) if prompt_builder
                  else f"Answer this clinical question about the note:\n{masked}")
        response = llm.complete(prompt)
        restored = self.rehydrate(response, mapping)
        return {"masked": masked, "mapping": mapping, "response": response,
                "restored": restored}
