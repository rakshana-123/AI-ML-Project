"""Assemble results/RESULTS.md from the generated metric files.

Run AFTER: presidio_baseline, evaluate --all (model trained), utility_check.

    python -m phi_gateway.make_results
"""

from __future__ import annotations

import json
from pathlib import Path

from .labels import ENTITY_TYPES

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MODELS = ROOT / "models" / "distilbert-phi"

ORDER = ["model", "model-only", "rules", "presidio"]
NAMES = {
    "model": "PHI Gateway (DistilBERT + rules)",
    "model-only": "Model only (DistilBERT)",
    "rules": "Rules only",
    "presidio": "Microsoft Presidio (baseline)",
}


def main() -> None:
    metrics = json.loads((RESULTS / "metrics_test.json").read_text())
    summary = {}
    p = MODELS / "training_summary.json"
    if p.exists():
        summary = json.loads(p.read_text())
    util = {}
    u = RESULTS / "utility_check.json"
    if u.exists():
        util = json.loads(u.read_text())

    md = ["# Results", "",
          f"Test set: 25 hand-written, hand-labelled notes, "
          f"{sum(m['tp'] + m['fn'] for m in metrics['model']['per_type'].values())} "
          "identifiers.", ""]

    if summary:
        md += [f"Model: {summary['base_model']} fine-tuned for "
               f"{summary['hyperparams']['epochs']} epochs on "
               f"{summary['train_notes']} synthetic notes "
               f"({summary['train_windows']} sliding windows); "
               f"**{summary['total_params']:,} parameters** total "
               f"({summary['trainable_params']:,} trainable); training time "
               f"{summary['train_seconds']/60:.0f} min on a 12-core CPU. "
               f"Best-epoch dev seqeval F1 "
               f"(strict IOB2): {summary['dev_seqeval_f1']:.3f}.", ""]

    md += ["## Headline comparison", "",
           "| System | Precision | Recall | F1 | Leak rate |", "|---|---|---|---|---|"]
    for sysname in ORDER:
        if sysname not in metrics:
            continue
        m = metrics[sysname]
        md.append(f"| {NAMES[sysname]} | {m['micro']['precision']:.3f} | "
                  f"**{m['micro']['recall']:.3f}** | {m['micro']['f1']:.3f} | "
                  f"{m['leak_rate']:.0%} |")
    md += ["", "Leak rate = share of test notes where at least one gold "
                "identifier reached the LLM unmasked (no overlapping "
                "prediction of any type).", ""]

    md += ["## Per-identifier-type metrics - PHI Gateway", "",
           "| Type | Precision | Recall | F1 | TP | FN | FP |", "|---|---|---|---|---|---|---|"]
    for t in ENTITY_TYPES:
        m = metrics["model"]["per_type"][t]
        md.append(f"| {t} | {m['precision']:.3f} | **{m['recall']:.3f}** | "
                  f"{m['f1']:.3f} | {m['tp']} | {m['fn']} | {m['fp']} |")

    md += ["", "## Per-identifier-type recall - gateway vs Presidio", "",
           "| Type | Gateway recall | Presidio recall |", "|---|---|---|"]
    for t in ENTITY_TYPES:
        g = metrics["model"]["per_type"][t]["recall"]
        p_ = metrics["presidio"]["per_type"][t]["recall"] if "presidio" in metrics else 0
        md.append(f"| {t} | **{g:.3f}** | {p_:.3f} |")

    if metrics["model"]["leaked_notes"]:
        md += ["", "## Remaining leaks (honesty section)", ""]
        for ln in metrics["model"]["leaked_notes"]:
            md.append(f"- **{ln['id']}**: " + "; ".join(
                f"{e['label']}={e['value']!r}" for e in ln["entities"]))

    if util:
        md += ["", "## Utility check", "",
               f"LLM: {util['llm']} - same 5 notes x 3 questions on original "
               f"vs masked notes; average ROUGE-L F1 between answer pairs: "
               f"**{util['avg_rouge_l_f1']:.2f}**. Full side-by-side: "
               "`utility_check.md`.", ""]

    (RESULTS / "RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote results/RESULTS.md")


if __name__ == "__main__":
    main()
