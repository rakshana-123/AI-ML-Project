"""Decode model token labels back to character spans.

Training labels follow the standard convention: only the FIRST subword of
each word carries a BIO tag; continuation subwords are -100.  A word,
however, can be a whole dotted run ("www.portal.com", "555-017-9088",
"19-Apr-2016") that the tokenizer splits into many non-whitespace-separated
tokens.  Only the first of those is labelled, so decoding must EXPAND each
labelled token to the end of its contiguous run (tokens that touch with no
whitespace between them belong to the same word).
"""

from __future__ import annotations

TRAILING_TRIM = " \t\n\r,;:.)]"  # sentence punctuation stripped from span tails

# AGE entities are bare numbers in gold ("94" in "94-year-old"); never
# run-expand them into the surrounding "-year-old" text.
NO_EXPAND_TYPES = {"AGE"}


def expand_run_end(offsets, i: int) -> int:
    """End char offset of the contiguous token run starting at token i."""
    end = offsets[i][1]
    j = i + 1
    n = len(offsets)
    while j < n and offsets[j][0] == end and offsets[j][1] > offsets[j][0]:
        end = offsets[j][1]
        j += 1
    return end


def expand_run_start(offsets, i: int) -> int:
    """Start char offset of the contiguous token run ending at token i."""
    start = offsets[i][0]
    j = i - 1
    while j >= 0 and offsets[j][1] == start and offsets[j][1] > offsets[j][0]:
        start = offsets[j][0]
        j -= 1
    return start


def bio_ids_to_spans(text: str, offsets, label_ids, id2label) -> list[dict]:
    """Convert per-token BIO label ids (-100 for ignored tokens) to char spans.

    Every labelled token expands to its full word run; consecutive B/I tags
    of the same type merge into one span.  Trailing separators (commas,
    colons, whitespace) are trimmed off the end of a span so masking does
    not swallow sentence punctuation.
    """
    spans: list[dict] = []
    cur: dict | None = None
    for i, lid in enumerate(label_ids):
        if lid == -100:
            continue
        tag = id2label[int(lid)]
        if tag == "O":
            if cur:
                _close(text, cur, spans)
                cur = None
            continue
        s, e = offsets[i]
        if s == e:
            continue
        if tag.startswith("B-"):
            if cur:
                _close(text, cur, spans)
            cur = {"start": expand_run_start(offsets, i) if cur is None else s,
                   "end": _end(offsets, i, tag[2:]), "label": tag[2:]}
        elif tag.startswith("I-") and cur and cur["label"] == tag[2:]:
            cur["end"] = _end(offsets, i, tag[2:])
        else:  # stray I- (or type switch): treat as a new entity
            if cur:
                _close(text, cur, spans)
            cur = {"start": s, "end": _end(offsets, i, tag[2:]),
                   "label": tag[2:]}
    if cur:
        _close(text, cur, spans)
    return spans


def _end(offsets, i: int, etype: str) -> int:
    if etype in NO_EXPAND_TYPES:
        return offsets[i][1]
    return expand_run_end(offsets, i)


def _close(text: str, cur: dict, out: list[dict]) -> None:
    end = cur["end"]
    while end > cur["start"] and text[end - 1] in TRAILING_TRIM:
        end -= 1
    if end > cur["start"]:
        out.append({"start": cur["start"], "end": end,
                    "label": cur["label"], "value": text[cur["start"]:end]})
