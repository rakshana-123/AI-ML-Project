"""Evaluation: entity-level P/R/F1 per type, leak rate, seqeval cross-check.

Span matching: a predicted span matches a gold span when the labels agree and
the overlap covers >= 50% of the SHORTER span (boundary characters often
differ by a punctuation attach - recall-first systems should not be punished
for a trailing comma).

Leak rate: share of test notes with at least one gold identifier that has NO
overlapping predicted span of any type - i.e. the raw value reached the LLM.

Run:  python -m phi_gateway.evaluate --system model|rules|model-only|presidio
      python -m phi_gateway.evaluate --all      (writes results/RESULTS.md)
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from seqeval.metrics import classification_report
from seqeval.scheme import IOB2

from .labels import ENTITY_TYPES

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


def load_notes(split: str = "test") -> list[dict]:
    with open(DATA_DIR / f"{split}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_presidio_preds() -> dict[str, list[dict]]:
    path = RESULTS_DIR / "presidio_preds.jsonl"
    if not path.exists():
        raise SystemExit("run `python -m phi_gateway.presidio_baseline` first")
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            out[rec["id"]] = rec["entities"]
    return out


def predict(system: str, notes: list[dict]) -> list[list[dict]]:
    """Run the requested system over all notes; returns per-note span lists."""
    if system == "presidio":
        preds_by_id = load_presidio_preds()
        return [preds_by_id.get(n.get("id", ""), []) for n in notes]

    from .masker import PHIGateway
    gw = PHIGateway(use_model=system != "rules")
    out = []
    for n in notes:
        if system == "model-only":
            spans = gw.ner.predict_spans(n["text"]) if gw.ner else []
        else:
            _, _, ents = gw.deidentify(n["text"], return_entities=True)
            spans = [{"start": e["start"], "end": e["end"],
                      "label": e["label"]} for e in ents]
        out.append(spans)
    return out


def _overlap(a, b) -> int:
    return max(0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def match_note(gold: list[dict], pred: list[dict], thresh: float = 0.5):
    """greedy same-label matching; returns (matched pairs, fn list, fp list)"""
    matches = []
    used = [False] * len(pred)
    fns = []
    for g in gold:
        best, best_score = None, 0.0
        for i, p in enumerate(pred):
            if used[i] or p["label"] != g["label"]:
                continue
            ov = _overlap(g, p)
            if ov <= 0:
                continue
            score = ov / min(g["end"] - g["start"], p["end"] - p["start"])
            if score > best_score:
                best, best_score = i, score
        if best is not None and best_score >= thresh:
            used[best] = True
            matches.append((g, pred[best]))
        else:
            fns.append(g)
    fps = [p for i, p in enumerate(pred) if not used[i]]
    return matches, fns, fps


def word_level_tags(text: str, spans: list[dict]) -> list[str]:
    """Derive word-level BIO tags from character spans (for seqeval).

    A word takes the label of the first span it overlaps; the first word of
    each consecutive same-label run becomes B-, the rest I-.
    """
    words = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
    flat = ["O"] * len(words)
    for sp in sorted(spans, key=lambda s: s["start"]):
        for wi, (ws, we) in enumerate(words):
            if _overlap({"start": ws, "end": we}, sp) > 0 and flat[wi] == "O":
                flat[wi] = sp["label"]
    tags = []
    for wi, lab in enumerate(flat):
        if lab == "O":
            tags.append("O")
        elif wi > 0 and flat[wi - 1] == lab:
            tags.append(f"I-{lab}")
        else:
            tags.append(f"B-{lab}")
    return tags


def evaluate(system: str, notes: list[dict], preds: list[list[dict]]) -> dict:
    tp = defaultdict(int)
    fn = defaultdict(int)
    fp = defaultdict(int)
    leaks = []
    for note, pred in zip(notes, preds):
        gold = note["entities"]
        matches, fns, fps = match_note(gold, pred)
        for g, _ in matches:
            tp[g["label"]] += 1
        for g in fns:
            fn[g["label"]] += 1
        for p in fps:
            fp[p["label"]] += 1
        # leak: a gold entity with no overlapping pred span of ANY type
        leaked = [g for g in gold
                  if not any(_overlap(g, p) > 0 for p in pred)]
        if leaked:
            leaks.append({"id": note.get("id"), "entities": [
                {"label": e["label"], "value": e["value"]} for e in leaked]})
    per_type = {}
    for t in ENTITY_TYPES:
        p = tp[t] / (tp[t] + fp[t]) if tp[t] + fp[t] else 0.0
        r = tp[t] / (tp[t] + fn[t]) if tp[t] + fn[t] else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        per_type[t] = {"precision": p, "recall": r, "f1": f1,
                       "tp": tp[t], "fp": fp[t], "fn": fn[t]}
    T = sum(tp.values()); FNs = sum(fn.values()); FPs = sum(fp.values())
    micro_p = T / (T + FPs) if T + FPs else 0.0
    micro_r = T / (T + FNs) if T + FNs else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if micro_p + micro_r else 0.0
    return {
        "system": system,
        "n_notes": len(notes),
        "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f1},
        "per_type": per_type,
        "leak_rate": len(leaks) / len(notes) if notes else 0.0,
        "leaked_notes": leaks,
    }


def seqeval_report(notes: list[dict], preds: list[list[dict]]) -> str:
    y_true, y_pred = [], []
    for note, pred in zip(notes, preds):
        y_true.append(word_level_tags(note["text"], note["entities"]))
        y_pred.append(word_level_tags(note["text"], pred))
    return classification_report(y_true, y_pred, mode="strict", scheme=IOB2,
                                 digits=3, zero_division=0)


SYSTEM_LABELS = {
    "model": "PHI Gateway (DistilBERT + rules)",
    "rules": "Rules only",
    "model-only": "Model only (no rules)",
    "presidio": "Microsoft Presidio (baseline)",
}


def md_table(results: dict) -> str:
    lines = ["| Identifier type | Precision | Recall | F1 | Support (gold) |",
             "|---|---|---|---|---|"]
    for t in ENTITY_TYPES:
        m = results["per_type"][t]
        support = m["tp"] + m["fn"]
        lines.append(f"| {t} | {m['precision']:.3f} | **{m['recall']:.3f}** "
                     f"| {m['f1']:.3f} | {support} |")
    mi = results["micro"]
    lines.append(f"| **micro-average** | {mi['precision']:.3f} | "
                 f"**{mi['recall']:.3f}** | {mi['f1']:.3f} | "
                 f"{sum(m['tp'] + m['fn'] for m in results['per_type'].values())} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="model",
                    choices=["model", "rules", "model-only", "presidio"])
    ap.add_argument("--split", default="test")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    notes = load_notes(args.split)

    systems = (["model", "model-only", "rules", "presidio"] if args.all
               else [args.system])
    all_results = {}
    for sysname in systems:
        preds = predict(sysname, notes)
        res = evaluate(sysname, notes, preds)
        all_results[sysname] = res
        print(f"\n===== {SYSTEM_LABELS[sysname]} =====")
        print(f"micro  P={res['micro']['precision']:.3f}  "
              f"R={res['micro']['recall']:.3f}  F1={res['micro']['f1']:.3f}")
        print(f"leak rate: {res['leak_rate']:.1%} "
              f"({len(res['leaked_notes'])}/{res['n_notes']} notes)")
        if args.all or args.system == sysname:
            print(md_table(res))
        if sysname == "model":
            print("\nseqeval strict IOB2 cross-check (word-level):")
            print(seqeval_report(notes, preds))

    out_path = RESULTS_DIR / f"metrics_{args.split}.json"
    out_path.write_text(json.dumps(all_results, indent=2, default=str),
                        encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
