"""Utility check: is the LLM still useful on masked notes?

Five hand-labelled test notes, the same three clinical questions each, asked
TWICE - once with the original note (contains synthetic identifiers) and once
with the gateway-masked note.  Answers are compared with ROUGE-L (F1) and
written side-by-side to results/utility_check.md.

With no API key configured this runs on the offline MockLLM; the pipeline is
identical, but for meaningful utility numbers set GROQ_API_KEY (free tier)
or point OPENAI_API_KEY/OPENAI_BASE_URL at any endpoint and re-run:

    python -m phi_gateway.utility_check
"""

from __future__ import annotations

import json
from pathlib import Path

from .llm import get_llm
from .masker import PHIGateway

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"

QUESTIONS = [
    "Summarise this clinical note in 3 sentences for a handover.",
    "What is the working diagnosis and the key supporting findings?",
    "What follow-up is arranged and with whom?",
]
PICK_IDS = ["test_01", "test_02", "test_05", "test_12", "test_23"]


def rouge_l_f1(a: str, b: str) -> float:
    """Character-insensitive word-level ROUGE-L F1."""
    def toks(s):
        return [w.strip(".,;:()[]").lower() for w in s.split()]
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return 0.0
    # longest common subsequence
    dp = [[0] * (len(tb) + 1) for _ in range(len(ta) + 1)]
    for i in range(1, len(ta) + 1):
        for j in range(1, len(tb) + 1):
            dp[i][j] = (dp[i - 1][j - 1] + 1 if ta[i - 1] == tb[j - 1]
                        else max(dp[i - 1][j], dp[i][j - 1]))
    lcs = dp[len(ta)][len(tb)]
    p, r = lcs / len(ta), lcs / len(tb)
    return 2 * p * r / (p + r) if p + r else 0.0


def main() -> None:
    notes = {json.loads(l)["id"]: json.loads(l)
             for l in open(DATA_DIR / "test.jsonl", encoding="utf-8")}
    gateway = PHIGateway()
    llm = get_llm()

    rows = []
    for nid in PICK_IDS:
        note = notes[nid]
        masked, mapping = gateway.deidentify(note["text"])
        for qi, q in enumerate(QUESTIONS):
            prompt_orig = f"{q}\n\nNOTE:\n{note['text']}"
            prompt_mask = f"{q}\n\nNOTE:\n{masked}"
            ans_orig = llm.complete(prompt_orig)
            ans_mask = llm.complete(prompt_mask)
            # the production experience: restore identifiers before the
            # clinician reads the answer
            ans_rehyd = gateway.rehydrate(ans_mask, mapping)
            rows.append({
                "id": nid, "question": q,
                "original_answer": ans_orig, "masked_answer": ans_mask,
                "rehydrated_answer": ans_rehyd,
                "rouge_l_f1": rouge_l_f1(ans_orig, ans_mask),
                "rouge_l_f1_rehydrated": rouge_l_f1(ans_orig, ans_rehyd),
                "n_placeholders": len(mapping),
            })
            print(f"{nid} Q{qi + 1}: ROUGE-L {rows[-1]['rouge_l_f1']:.2f} "
                  f"(rehydrated {rows[-1]['rouge_l_f1_rehydrated']:.2f})")

    avg = sum(r["rouge_l_f1"] for r in rows) / len(rows)
    avg_rehyd = sum(r["rouge_l_f1_rehydrated"] for r in rows) / len(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "utility_check.json").write_text(
        json.dumps({"llm": llm.name, "avg_rouge_l_f1": avg,
                    "avg_rouge_l_f1_rehydrated": avg_rehyd, "rows": rows},
                   indent=2), encoding="utf-8")

    md = [f"# Utility check - LLM answers on original vs masked notes",
          "",
          f"LLM: **{llm.name}**  |  notes: {', '.join(PICK_IDS)}  |  "
          f"3 questions each",
          "",
          f"Average ROUGE-L F1 between answers: **{avg:.2f}** (raw masked), "
          f"**{avg_rehyd:.2f}** after rehydration restores identifiers "
          "(1.0 = identical content).",
          "",
          "| Note | Question | ROUGE-L masked | ROUGE-L rehydrated |",
          "|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['id']} | {r['question'][:32]}... | "
                  f"{r['rouge_l_f1']:.2f} | {r['rouge_l_f1_rehydrated']:.2f} |")
    md.append("")
    for r in rows:
        md += [f"## {r['id']} - {r['question']}", "",
               "**Original:**", "", r["original_answer"], "",
               "**Masked:**", "", r["masked_answer"], ""]
    (RESULTS_DIR / "utility_check.md").write_text("\n".join(md), encoding="utf-8")
    print(f"avg ROUGE-L F1: {avg:.2f} masked, {avg_rehyd:.2f} rehydrated"
          f"  ->  results/utility_check.md")


if __name__ == "__main__":
    main()
