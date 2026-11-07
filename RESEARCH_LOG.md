# Research log

Working log kept while building the gateway: what I read, what I tried,
what came of it. Failures also get their own file, `FAILURES.md`.

## Phase 1 - The rules (HIPAA Safe Harbor)

- Read the primary source: HHS "Guidance Regarding Methods for De-identification
  of Protected Health Information in Accordance with the HIPAA Privacy Rule"
  (hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification).
  Took away the 18 identifiers, and the three special rules that matter here:
  - Dates: anything finer than year must go (birth date, admission,
    discharge, death, service dates...).
  - Ages: everything over 89 must be aggregated into "90+" - so mask the
    number itself.
  - ZIP: full 5-digit ZIP is identifiable unless the 3-digit prefix covers
    >20,000 people (17 prefixes are restricted anyway). Decision: mask the
    whole ZIP - recall first, and partial ZIPs destroy utility anyway.
- Interesting nuance found in the HHS FAQ: Safe Harbor technically does NOT
  require removing provider names (facilities/clinicians), because the rule
  lists identifiers of the *individual*. The brief explicitly requires
  masking clinicians, and masking them is the safe choice, so we do - noted
  in the README as a deliberate stricter-than-Safe-Harbor decision.
- i2b2/n2c2 2014 de-identification challenge (overview: Stubbs & Uzuner,
  "De-identification of longitudinal clinical notes", JAMIA 2015): the
  seven i2b2 categories map cleanly onto the brief's list; the challenge
  results showed the same weakness my Presidio baseline shows - dates and
  IDs are easy (regex-like), NAMES and LOCATIONS are where recall dies.
  That is why the model exists and why it focuses on NAME/LOCATION.

## Phase 2 - Problem framing

- NER as token classification with BIO tags (HF NLP course, chapter on token
  classification): B-X starts an entity, I-X continues it, O is outside.
  13 entity types -> 27 labels.
- Subword label alignment (the "silent bug" the brief warns about):
  DistilBERT's WordPiece splits words into pieces; only the first subword of
  a word carries the label, continuations get -100 (ignored by the loss).
  I verified alignment by round-tripping: labels -> decode -> spans must
  reconstruct the gold spans exactly. First version failed (see FAILURES.md
  #2/#3); final version reconstructs 20/25 test notes exactly and the rest
  differ only by attached punctuation.

## Phase 3 - Model choice

Compared model cards:

| Model | Params | Vocab | Training data | Notes for this task |
|---|---|---|---|---|
| distilbert-base-cased | 66M | 119K WordPiece | distillation of BERT-base on Toronto BookCorpus+Wiki | cased = keeps capitalisation cues for names; 40% smaller than BERT, ~97% of NER quality |
| bert-base-cased | 110M | 119K | BookCorpus+Wiki | baseline; 1.7x slower on our CPU-only box |
| Bio_ClinicalBERT | 110M | 119K | MIMIC-III clinical notes | domain match, but this task's hard part is invented names/facilities, not clinical language; also 1.7x slower |
| deberta-v3-small | 142M | 128K SentencePiece | CC100 + curated | strongest encoder here but ~2-3x CPU cost |

Decision: **distilbert-base-cased** (66,985,830 params with our head - exact
count written to `models/distilbert-phi/training_summary.json` when training
finishes). Reasons: CPU-only training budget, cased tokenizer, and the
identifier surface forms in synthetic notes are mostly invented names and
formatted IDs where clinical pretraining adds little. "Does clinical
pretraining help?" is answered honestly in the README as *not tested for
compute-budget reasons* - flagged as the first follow-up experiment with a
GPU (fine-tune Bio_ClinicalBERT on the same data and compare dev recall).

## Phase 4 - Data

- Faker for inventing values; 13 hand-written note templates (H&P, SOAP,
  discharge, referral letter, radiology, ED, psych, telehealth, op note,
  pathology, billing, voicemail, "trap-dense" neurology note).
- Deliberate variation: 12 date formats, 6 phone formats, name styles
  (Dr. X, LAST-FIRST headers, misspellings, hyphens, suffixes), ages mostly
  <=89 with ~15% over 89, ZIP+4 vs ZIP, labelled IDs in unlikely spots.
- Adversarial traps: clinicians named Parkinson/Huntington/Bell/... next to
  the matching eponymous disease; place-named people (Austin Houston);
  states kept vs cities masked; relative time ("3 days post-op") next to
  calendar dates; year-only mentions kept.
- Test set: 25 notes written BY HAND in a different style from the
  generator (new vocabulary, invented values), annotated inline
  `[[TYPE::value]]`, converted to character spans by script. 414 entities.

## Phase 5 - Baseline (Presidio)

- presidio-analyzer 2.2.x with spaCy en_core_web_lg, default recognizer
  registry; mapped PERSON->NAME etc. (see presidio_baseline.py).
- Result on our test set (see README for the table): micro R=74.6%,
  P=58.2%, leak rate 88% of notes. Misses: all MRN/HEALTHPLAN/ACCOUNT/AGE
  (no default recognizers), most sub-state LOCATIONs, half the LICENSEs.
  Its NAME recall is strong (92.6%) - that validated putting the neural
  model's effort into NAME/LOCATION rather than formats.

## Phase 6 - Training

- HF Trainer, BIO labels, -100 on continuations/specials, sliding windows
  (384 tokens, stride 64) so long notes train end-to-end, 3 epochs,
  batch 8, lr 5e-5, seqeval strict/IOB2 dev F1 for model selection.
- Smoke test first (0.03 epochs) to validate the plumbing end to end on
  CPU (~7.7 s/step measured; full run ~2.5-3 h).

## Phase 7 - The gateway

- Hybrid masking: model spans UNION rule spans; overlaps merge with the
  rule label winning (regexes are near-perfect on their formats).
- Placeholders per (type, normalised value): `[NAME_1]`, `[DATE_1]`, ...
- Post-mask safety net: re-scan the masked text with the rule layer;
  anything found there was missed by the merge and gets masked too
  (defence in depth - reported as "late catches").
- Rehydration replaces placeholders back; unknown placeholders returned by
  the LLM are left untouched (no data risk) and reported.

## Phase 8 - Utility + demo

- Same 5 notes, 3 questions, asked twice (original vs masked); ROUGE-L F1
  between answer pairs. Offline MockLLM fallback so the pipeline always
  runs; set GROQ_API_KEY for real numbers.
