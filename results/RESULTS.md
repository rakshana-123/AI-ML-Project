# Results

Test set: 25 hand-written, hand-labelled notes, 414 identifiers.

Model: distilbert-base-cased fine-tuned for 1 epoch(s) on 3000 synthetic notes (3008 sliding windows); **65,211,675 parameters** total (65,211,675 trainable); training time 100 min on a 12-core CPU. Best-epoch dev seqeval F1 (strict IOB2): 1.000. Stopped after epoch 1: dev seqeval strict-IOB2 F1 saturated at 0.9996; epochs 2-3 were projected to add <0.001 for ~3 CPU-hours. Best checkpoint (epoch 1) salvaged from runs/checkpoint-376.

## Headline comparison

| System | Precision | Recall | F1 | Leak rate |
|---|---|---|---|---|
| PHI Gateway (DistilBERT + rules) | 0.847 | **0.966** | 0.903 | 4% |
| Model only (DistilBERT) | 0.476 | **0.915** | 0.626 | 28% |
| Rules only | 0.975 | **0.572** | 0.721 | 100% |
| Microsoft Presidio (baseline) | 0.582 | **0.746** | 0.654 | 88% |

Leak rate = share of test notes where at least one gold identifier reached the LLM unmasked (no overlapping prediction of any type).

## Per-identifier-type metrics - PHI Gateway

| Type | Precision | Recall | F1 | TP | FN | FP |
|---|---|---|---|---|---|---|
| NAME | 0.781 | **0.992** | 0.874 | 121 | 1 | 34 |
| LOCATION | 0.712 | **0.852** | 0.776 | 52 | 9 | 21 |
| DATE | 0.907 | **0.967** | 0.936 | 88 | 3 | 9 |
| AGE | 1.000 | **1.000** | 1.000 | 6 | 0 | 0 |
| PHONE | 0.979 | **0.979** | 0.979 | 47 | 1 | 1 |
| EMAIL | 0.875 | **1.000** | 0.933 | 14 | 0 | 2 |
| SSN | 1.000 | **1.000** | 1.000 | 3 | 0 | 0 |
| MRN | 0.875 | **1.000** | 0.933 | 14 | 0 | 2 |
| HEALTHPLAN | 0.857 | **1.000** | 0.923 | 6 | 0 | 1 |
| ACCOUNT | 1.000 | **1.000** | 1.000 | 18 | 0 | 0 |
| LICENSE | 1.000 | **1.000** | 1.000 | 5 | 0 | 0 |
| URL | 1.000 | **1.000** | 1.000 | 17 | 0 | 0 |
| IP | 0.818 | **1.000** | 0.900 | 9 | 0 | 2 |

## Per-identifier-type recall - gateway vs Presidio

| Type | Gateway recall | Presidio recall |
|---|---|---|
| NAME | **0.992** | 0.926 |
| LOCATION | **0.852** | 0.246 |
| DATE | **0.967** | 0.967 |
| AGE | **1.000** | 0.000 |
| PHONE | **0.979** | 0.979 |
| EMAIL | **1.000** | 1.000 |
| SSN | **1.000** | 1.000 |
| MRN | **1.000** | 0.000 |
| HEALTHPLAN | **1.000** | 0.000 |
| ACCOUNT | **1.000** | 0.000 |
| LICENSE | **1.000** | 0.600 |
| URL | **1.000** | 1.000 |
| IP | **1.000** | 1.000 |

## Remaining leaks (honesty section)

- **test_21**: LOCATION='Charlotte'; LOCATION='Atlanta'; LOCATION='Madison'

## Utility check

LLM: mock (offline deterministic) - same 5 notes x 3 questions on original vs masked notes; average ROUGE-L F1 between answer pairs: **0.95**. Full side-by-side: `utility_check.md`.
