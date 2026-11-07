"""One-command end-to-end demo of the PHI De-identification Gateway.

    python demo.py                 # default demo note
    python demo.py --note x.txt    # your own note (plain text)
    python demo.py --interactive   # type/paste a note at the prompt

Flow shown: original note -> deidentify() -> [masked note + private mapping]
-> LLM (Groq / OpenAI-compatible / local Ollama / offline mock) -> answer
-> rehydrate() -> final text with identifiers restored.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from phi_gateway.build_testset import MARKUP_RE   # noqa: E402
from phi_gateway.llm import get_llm               # noqa: E402
from phi_gateway.masker import PHIGateway         # noqa: E402

HERE = Path(__file__).parent
QUESTION = ("You are a clinical assistant. Read the note below and answer in "
            "3-4 sentences: what is the working diagnosis, what immediate "
            "management is planned, and what follow-up is arranged? "
            "Quote key details from the note.\n\nNOTE:\n")


def strip_markup(text: str) -> str:
    return MARKUP_RE.sub(lambda m: m.group(2), text)


def run_once(gateway: PHIGateway, llm, note_text: str) -> None:
    print("=" * 78)
    print("ORIGINAL NOTE (never leaves this machine until masked)")
    print("=" * 78)
    print(note_text)

    masked, mapping = gateway.deidentify(note_text)
    report = gateway.last_report

    print("=" * 78)
    print(f"MASKED NOTE  -  {report['entities']} identifiers masked "
          f"({report['late_catches']} by the post-mask safety net)")
    print("=" * 78)
    print(masked)

    print("=" * 78)
    print("PRIVATE MAPPING (kept locally - this is what the LLM never sees)")
    print("=" * 78)
    for k, v in mapping.items():
        print(f"  {k:14s} <-> {v}")

    print("=" * 78)
    print(f"LLM ({llm.name}) receives ONLY the masked note")
    print("=" * 78)
    try:
        response = llm.complete(QUESTION + masked, stream=True)
    except TypeError:                       # provider without streaming
        response = llm.complete(QUESTION + masked)
        print(response)

    restored = gateway.rehydrate(response, mapping)
    unknowns = gateway.last_report.get("unknown_placeholders", [])

    print("=" * 78)
    print("REHYDRATED ANSWER (identifiers restored on our side)")
    print("=" * 78)
    print(restored)
    if unknowns:
        print(f"\n[!] {len(unknowns)} unknown placeholder(s) returned by the "
              f"LLM (left untouched, no data risk): {unknowns}")
    print("=" * 78)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--note", help="path to a plain-text note")
    ap.add_argument("--interactive", action="store_true",
                    help="paste a note interactively (blank line + Ctrl-Z/Ctrl-D to finish)")
    args = ap.parse_args()

    gateway = PHIGateway()
    llm = get_llm()
    print(f"[demo] gateway: {'DistilBERT + rules' if gateway.ner else 'RULES ONLY (train the model first)'}"
          f"   |   llm: {llm.name}\n")

    if args.note:
        run_once(gateway, llm, Path(args.note).read_text(encoding="utf-8"))
    elif args.interactive:
        print("Paste your note. Finish with a blank line, then Ctrl-Z + Enter"
              " (Windows) or Ctrl-D (Unix).")
        lines = sys.stdin.read().splitlines()
        run_once(gateway, llm, "\n".join(lines).strip())
    else:
        note_text = strip_markup(
            (HERE / "data" / "demo_note.txt").read_text(encoding="utf-8"))
        run_once(gateway, llm, note_text)


if __name__ == "__main__":
    main()
