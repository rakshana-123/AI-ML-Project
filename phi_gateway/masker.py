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
from .labels import ENTITY_TYPES, EPONYM_SURNAMES
from .rules import rule_spans

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "distilbert-phi"
PLACEHOLDER_RX = re.compile(r"\[(" + "|".join(ENTITY_TYPES) + r")_(\d+)\]")

NAME_TITLES = r"(?:Dr|Mr|Mrs|Ms|Prof)\."

# word tokens that are never treated as a surname by the recall pass
NON_SURNAME_WORDS = {
    "jr", "sr", "ii", "iii", "iv", "md", "do", "rn", "np", "pa", "phd",
    "md,", "lacsw", "lcsb", "facp", "facs", "ddi", "the", "and", "of",
}


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


TIME_LIKE = re.compile(r"^\d{1,2}:\d{2}")


def merge_spans(spans: list[dict], text: str | None = None) -> list[dict]:
    """Union of spans; overlapping spans merge, rule labels win disputes.

    A rule-layer span is near-perfect on its own format, so when a model
    span overlaps one, the merged mask keeps the RULE's type (the model's
    ACCOUNT guess must not steal a LICENSE span, and vice versa).  When the
    text is provided, two same-label spans separated only by punctuation
    ("Dr" + ". Felicity Huntington") are stitched back together.
    """
    spans = [s for s in spans if s["end"] > s["start"]]
    # model quirk: pure times are never identifiers
    if text is not None:
        spans = [s for s in spans
                 if not (s["label"] in ("NAME", "LOCATION")
                         and TIME_LIKE.match(text[s["start"]:s["end"]]))]
    spans.sort(key=lambda s: (s["start"], -s["end"]))
    merged: list[dict] = []
    for s in spans:
        if merged and s["start"] < merged[-1]["end"]:
            prev = merged[-1]
            prev["end"] = max(prev["end"], s["end"])
            if s.get("rule") and not prev.get("rule"):
                prev["label"] = s["label"]
            prev["rule"] = prev.get("rule", False) or s.get("rule", False)
        elif (merged and text is not None
              and merged[-1]["label"] == s["label"]
              and not merged[-1].get("rule") and not s.get("rule")):
            # stitch model split artefacts: gap of only ". " / ", "
            gap = text[merged[-1]["end"]:s["start"]]
            if gap and len(gap) <= 4 and gap.strip(" .,") == "" \
                    and ("." in gap or "," in gap):
                merged[-1]["end"] = s["end"]
                continue
            merged.append(dict(s))
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
        spans = merge_spans(spans, text)

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

        # pass 1: mask merged spans (left to right over the original text).
        # coord_map tracks, for every char of the masked string, where it
        # came from in the ORIGINAL text (None for placeholder chars) so
        # later passes can report spans in original coordinates.
        out = []
        coord_map: list[int | None] = []
        cursor = 0

        def emit(chunk: str, orig_start: int | None) -> None:
            out.append(chunk)
            if orig_start is None:
                coord_map.extend([None] * len(chunk))
            else:
                coord_map.extend(range(orig_start, orig_start + len(chunk)))

        for s in spans:
            emit(text[cursor:s["start"]], cursor)
            ph = placeholder_for(text[s["start"]:s["end"]], s["label"])
            emit(ph, None)
            cursor = s["end"]
        emit(text[cursor:], cursor)
        masked = "".join(out)

        def masked_to_orig(ms: int, me: int) -> tuple[int, int] | None:
            """map a masked-string span back to original-text coordinates"""
            if ms >= len(coord_map) or coord_map[ms] is None:
                return None
            j = me - 1
            while j >= ms and coord_map[j] is None:
                j -= 1
            if j < ms:
                return None
            return coord_map[ms], coord_map[j] + 1

        late_spans: list[dict] = []

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
                orig = masked_to_orig(r["start"], r["end"])
                if orig:
                    late_spans.append({"start": orig[0], "end": orig[1],
                                       "label": r["label"], "late": True})
                masked = masked[:r["start"]] + ph + masked[r["end"]:]

        # pass 3 (surname recall): if a full name was masked, later short
        # references to the same person ("Dr. Huntington" after
        # "Dr. Felicity Huntington") are still identifiers - mask them too.
        masked, n_surname, surname_spans = self._surname_recall(
            masked, mapping, placeholder_for, coord_map)
        late_catches += n_surname

        self.last_report = {
            "entities": len(mapping),
            "late_catches": late_catches,
            "mapping": mapping,
        }
        if return_entities:
            ents = [{k: s.get(k) for k in ("start", "end", "label")}
                    for s in spans]
            ents += late_spans + surname_spans
            ents.sort(key=lambda e: e["start"])
            for e in ents:
                e["value"] = text[e["start"]:e["end"]]
            self.last_report["entity_list"] = ents
            return masked, mapping, ents
        return masked, mapping

    def _surname_recall(self, masked: str, mapping: dict, placeholder_for,
                        coord_map=None):
        """Mask standalone repeats of already-masked people's surnames.

        Guards the classic leak where the full name was masked but
        "Dr. <Surname>" later in the note slips through.  Eponymous surnames
        (Parkinson, Bell, ...) and short 3-letter surnames are only masked
        with a title attached, so "Parkinson's disease" is never touched.
        Returns (masked, n_added, original-coordinate spans).
        """
        added = 0
        spans_out: list[dict] = []
        surnames: dict[str, bool] = {}      # surname -> title_required
        for ph, value in mapping.items():
            if not ph.startswith("[NAME_"):
                continue
            words = [w.strip(",.") for w in value.split()]
            words = [w for w in words if w.lower() not in NON_SURNAME_WORDS
                     and w.upper() != "DR" and not w.endswith(".")]
            alpha = [w for w in words if w.isalpha()]
            if not alpha:
                continue
            sur = alpha[-1]
            if sur.lower() in NON_SURNAME_WORDS or not sur[0].isupper():
                continue
            if len(sur) >= 4:
                surnames[sur] = sur.lower() in EPONYM_SURNAMES
                if sur.isupper():
                    surnames[sur.capitalize()] = sur.lower() in EPONYM_SURNAMES
            elif len(sur) == 3:
                # short surnames ("Bae") only count with a title attached
                surnames[sur] = True
        for sur in sorted(surnames, key=len, reverse=True):
            title_required = surnames[sur]
            pattern = (rf"{NAME_TITLES}\s*{re.escape(sur)}\b" if title_required
                       else rf"\b{re.escape(sur)}\b")
            # skip possessive disease forms ("Parkinson's disease")
            hits = [m for m in re.finditer(pattern, masked)
                    if masked[m.end():m.end() + 2] != "'s"]
            for m in reversed(hits):                # replace right-to-left
                s, e = m.start(), m.end()
                value = masked[s:e]
                ph = placeholder_for(value, "NAME")
                masked = masked[:s] + ph + masked[e:]
                added += 1
                if coord_map is not None and s < len(coord_map) \
                        and coord_map[s] is not None:
                    j = e - 1
                    while j >= s and (j >= len(coord_map)
                                      or coord_map[j] is None):
                        j -= 1
                    if j >= s:
                        spans_out.append({"start": coord_map[s],
                                          "end": coord_map[j] + 1,
                                          "label": "NAME",
                                          "late": True})
        return masked, added, spans_out

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
