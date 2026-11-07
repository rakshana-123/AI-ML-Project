"""Fine-tune a token-classification model for PHI detection.

Model: distilbert-base-cased (66M params) — chosen after comparing model
cards (see README): DistilBERT is 40% smaller than BERT-base with ~97% of
its NER quality, runs comfortably on CPU for training and inference, and
the *cased* variant preserves capitalisation cues that matter for names.

Label alignment (the classic silent bug): BERT-style tokenizers split
words into subwords.  We label only the FIRST subword of each word and set
continuation subwords to -100 (ignored by the loss).  Word boundaries are
detected from the fast tokenizer's offset mapping: a subword whose start
offset immediately follows the previous subword's end (no whitespace
between them) is a continuation.

Long notes are split into overlapping windows (stride) so no entity near
the end of a long note is silently dropped from training.

Usage:  python -m phi_gateway.train [--model distilbert-base-cask]
                                      (typo guard: distilbert-base-cased)
Output: models/distilbert-phi + models/distilbert-phi/param_count.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                          Trainer, TrainingArguments)
from seqeval.metrics import f1_score as seq_f1
from seqeval.scheme import IOB2

from .labels import ENTITY_TYPES, ID_TO_LABEL, LABEL_LIST, LABEL_TO_ID

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"

MAX_LEN = 384
STRIDE = 64


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class PHIDataset(Dataset):
    """Pre-tokenised sliding windows with word-level BIO labels (-100 on
    continuation subwords and special tokens)."""

    def __init__(self, notes: list[dict], tokenizer, max_len: int = MAX_LEN,
                 stride: int = STRIDE):
        self.examples = []
        for note in notes:
            text = note["text"]
            enc = tokenizer(text, return_offsets_mapping=True,
                            truncation=False, add_special_tokens=False)
            tokens = enc["input_ids"]
            offsets = enc["offset_mapping"]
            if not tokens:
                continue
            for start in range(0, max(len(tokens), 1), max_len - stride):
                window = range(start, min(start + max_len, len(tokens)))
                ids = [tokens[i] for i in window]
                offs = [offsets[i] for i in window]
                labels = align_labels(text, offs, note["entities"])
                self.examples.append({
                    "input_ids": [tokenizer.cls_token_id] + ids + [tokenizer.sep_token_id],
                    "attention_mask": [1] * (len(ids) + 2),
                    "labels": [-100] + labels + [-100],
                })
                if start + max_len >= len(tokens):
                    break

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


def is_word_start(text: str, token_idx: int, offsets) -> bool:
    s = offsets[token_idx][0]
    if token_idx == 0:
        return True
    return s > 0 and text[s - 1].isspace()


def align_labels(text: str, offsets, entities) -> list[int]:
    """BIO label id per token; -100 for continuation subwords.

    A token is a "word start" if whitespace precedes it OR it begins a gold
    entity — the second clause matters for identifiers glued to punctuation,
    e.g. "(04/2026" or "ID[[MRN::...]]": their first token is contiguous with
    the previous token but still must carry the B- tag.
    """
    ent_starts = {ent["start"] for ent in entities}
    labels = []
    for i, (s, e) in enumerate(offsets):
        if s == e:
            labels.append(-100)
            continue
        if not is_word_start(text, i, offsets) and s not in ent_starts:
            labels.append(-100)  # continuation subword: the silent-bug guard
            continue
        lab = "O"
        for ent in entities:
            if ent["start"] <= s and e <= ent["end"]:
                lab = f"B-{ent['label']}" if s == ent["start"] else f"I-{ent['label']}"
                break
        labels.append(LABEL_TO_ID[lab])
    return labels


class Collator:
    def __init__(self, tokenizer):
        self.pad_id = tokenizer.pad_token_id

    def __call__(self, batch):
        maxlen = max(len(b["input_ids"]) for b in batch)
        input_ids, attn, labels = [], [], []
        for b in batch:
            pad = maxlen - len(b["input_ids"])
            input_ids.append(b["input_ids"] + [self.pad_id] * pad)
            attn.append(b["attention_mask"] + [0] * pad)
            labels.append(b["labels"] + [-100] * pad)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attn, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    true_seqs, pred_seqs = [], []
    for pred_row, label_row in zip(preds, labels):
        true, prd = [], []
        for p, l in zip(pred_row, label_row):
            if l == -100:
                continue
            true.append(ID_TO_LABEL[int(l)])
            prd.append(ID_TO_LABEL[int(p)])
        true_seqs.append(true)
        pred_seqs.append(prd)
    f1 = seq_f1(true_seqs, pred_seqs, mode="strict", scheme=IOB2, average="micro",
                zero_division=0)
    return {"seqeval_f1": float(f1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="distilbert-base-cased")
    ap.add_argument("--epochs", type=float, default=4.0)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--output", default=None, help="output dir under models/")
    args = ap.parse_args()

    out_dir = MODELS_DIR / (args.output or "distilbert-phi")
    out_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model, num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL, label2id=LABEL_TO_ID)

    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"model={args.model}  total params={total_params:,}  trainable={trainable:,}")

    train_notes = load_jsonl(DATA_DIR / "train.jsonl")
    dev_notes = load_jsonl(DATA_DIR / "dev.jsonl")
    train_ds = PHIDataset(train_notes, tokenizer)
    dev_ds = PHIDataset(dev_notes, tokenizer)
    print(f"train windows: {len(train_ds)}  dev windows: {len(dev_ds)}")

    targs = TrainingArguments(
        output_dir=str(out_dir / "runs"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=16,
        learning_rate=args.lr,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="seqeval_f1",
        logging_steps=50,
        seed=42,
        report_to=[],
        dataloader_num_workers=0,   # Windows: avoid multiprocessing hangs
        save_total_limit=1,
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        data_collator=Collator(tokenizer),
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    t0 = time.time()
    trainer.train()
    train_secs = time.time() - t0

    metrics = trainer.evaluate()
    print("final dev metrics:", metrics)

    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))

    per_type_counts = {t: 0 for t in ENTITY_TYPES}
    for n in dev_notes:
        for e in n["entities"]:
            per_type_counts[e["label"]] += 1

    summary = {
        "base_model": args.model,
        "total_params": total_params,
        "trainable_params": trainable,
        "label_count": len(LABEL_LIST),
        "train_notes": len(train_notes),
        "dev_notes": len(dev_notes),
        "train_windows": len(train_ds),
        "dev_windows": len(dev_ds),
        "train_seconds": round(train_secs, 1),
        "dev_seqeval_f1": metrics.get("seqeval_f1"),
        "dev_entity_counts": per_type_counts,
        "hyperparams": {"epochs": args.epochs, "batch": args.batch_size,
                        "lr": args.lr, "max_len": MAX_LEN, "stride": STRIDE},
    }
    (out_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"saved -> {out_dir}  ({train_secs/60:.1f} min)")


if __name__ == "__main__":
    main()
