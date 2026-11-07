"""Convert the hand-written test notes into data/test.jsonl with exact spans.

The 25 notes in testset_notes.py are annotated inline as [[TYPE::value]] (a
single colon [[TYPE:value]] is accepted too; values may span line breaks).
This script computes exact character spans, strips the markup, validates
types and non-overlap, and writes the gold test set.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .labels import ENTITY_TYPES
from .testset_notes import TEST_NOTES

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MARKUP_RE = re.compile(r"\[\[(\w+):{1,2}(.*?)\]\]", re.DOTALL)


def convert(notes: list[tuple[str, str, str]]) -> list[dict]:
    out = []
    for note_id, focus, marked in notes:
        entities = []
        pos = 0          # cursor over the marked source
        out_pos = 0      # cursor over the cleaned text
        clean_parts = []
        for m in MARKUP_RE.finditer(marked):
            # text before the markup
            before = marked[pos:m.start()]
            clean_parts.append(before)
            out_pos += len(before)
            label, value = m.group(1).upper(), m.group(2)
            if label not in ENTITY_TYPES:
                raise ValueError(f"{note_id}: unknown type {label}")
            entities.append({"start": out_pos, "end": out_pos + len(value),
                             "label": label, "value": value})
            clean_parts.append(value)
            out_pos += len(value)
            pos = m.end()
        clean_parts.append(marked[pos:])
        text = "".join(clean_parts)
        if "[[" in text or "]]" in text:
            raise ValueError(f"{note_id}: unbalanced markup remains")
        prev_end = 0
        for e in entities:  # sorted by construction; check non-overlap
            assert e["start"] >= prev_end, f"{note_id}: overlap at {e}"
            assert text[e["start"]:e["end"]] == e["value"], f"{note_id}: span mismatch"
            prev_end = e["end"]
        out.append({"id": note_id, "focus": focus, "text": text,
                    "entities": entities})
    return out


def main() -> None:
    notes = convert(TEST_NOTES)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "test.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for n in notes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    counts: dict[str, int] = {}
    for n in notes:
        for e in n["entities"]:
            counts[e["label"]] = counts.get(e["label"], 0) + 1
    print(f"wrote {len(notes)} notes -> {path}")
    for k in sorted(counts):
        print(f"  {k:11s} {counts[k]}")
    print(f"  total       {sum(counts.values())}")


if __name__ == "__main__":
    main()
