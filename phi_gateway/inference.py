"""Neural NER inference: sliding-window prediction over long notes.

Notes can exceed the model's 512-token limit, so we run the model over
overlapping windows (reusing the training window geometry), decode each
window's BIO tags to character spans with run expansion, and merge.
"""

from __future__ import annotations

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

from .decode import bio_ids_to_spans
from .labels import ID_TO_LABEL
from .train import MAX_LEN, STRIDE


class ModelNER:
    def __init__(self, model_dir: str, device: str | None = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True)
        self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
        self.device = device or ("cpu")
        self.model.to(self.device)
        self.model.eval()

    def predict_spans(self, text: str, batch_size: int = 4) -> list[dict]:
        enc = self.tokenizer(text, return_offsets_mapping=True,
                             truncation=False, add_special_tokens=False)
        tokens = enc["input_ids"]
        offsets = enc["offset_mapping"]
        if not tokens:
            return []

        windows = []
        for start in range(0, len(tokens), MAX_LEN - STRIDE):
            idx = list(range(start, min(start + MAX_LEN, len(tokens))))
            windows.append(idx)
            if start + MAX_LEN >= len(tokens):
                break

        all_spans: list[dict] = []
        with torch.no_grad():
            for i in range(0, len(windows), batch_size):
                chunk = windows[i:i + batch_size]
                batch_ids, batch_mask, lengths = [], [], []
                for idx in chunk:
                    ids = [self.tokenizer.cls_token_id] + \
                          [tokens[j] for j in idx] + \
                          [self.tokenizer.sep_token_id]
                    batch_ids.append(ids)
                    batch_mask.append([1] * len(ids))
                    lengths.append(len(ids))
                maxlen = max(lengths)
                pad = self.tokenizer.pad_token_id
                batch_ids = [x + [pad] * (maxlen - len(x)) for x in batch_ids]
                batch_mask = [x + [0] * (maxlen - len(x)) for x in batch_mask]
                out = self.model(
                    input_ids=torch.tensor(batch_ids, device=self.device),
                    attention_mask=torch.tensor(batch_mask, device=self.device))
                preds = out.logits.argmax(-1).cpu().tolist()
                # decode with each window's TRUE length, not the padded one
                for idx, n, prd in zip(chunk, lengths, preds):
                    win_offsets = [offsets[j] for j in idx]
                    label_ids = prd[1:n - 1]     # drop CLS/SEP predictions
                    spans = bio_ids_to_spans(text, win_offsets, label_ids,
                                             ID_TO_LABEL)
                    all_spans.extend(spans)
        return _merge_window_spans(all_spans)


def _overlap(a: dict, b: dict) -> bool:
    return not (a["end"] <= b["start"] or b["end"] <= a["start"])


def _iou(a: dict, b: dict) -> float:
    inter = max(0, min(a["end"], b["end"]) - max(a["start"], b["start"]))
    if inter <= 0:
        return 0.0
    union = (a["end"] - a["start"]) + (b["end"] - b["start"]) - inter
    return inter / union


def _merge_window_spans(spans: list[dict]) -> list[dict]:
    """De-duplicate near-identical spans produced by overlapping windows."""
    spans = sorted(spans, key=lambda s: (s["start"], -s["end"]))
    kept: list[dict] = []
    for s in spans:
        dup = False
        for k in kept:
            if k["label"] == s["label"] and _iou(k, s) > 0.7:
                # same entity seen in two windows: keep the wider one
                k["start"] = min(k["start"], s["start"])
                k["end"] = max(k["end"], s["end"])
                k["value"] = None
                dup = True
                break
        if not dup:
            kept.append(dict(s))
    for k in kept:
        k.pop("value", None)
    return kept
