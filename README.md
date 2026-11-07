# PHI De-identification Gateway

A gateway that strips patient identifiers out of a clinical note before the
note is sent to an LLM, and puts them back into the LLM's answer afterwards.
The private mapping between placeholders and original values stays on our
side and is never sent to the LLM.

```
raw note ──deidentify()──> masked note ──> LLM ──> answer ──rehydrate()──> readable answer
                │                          (mapping never crosses this line)
                └── private mapping ────────┘
```

- **Model:** fine-tuned `distilbert-base-cased` token classifier,
  **65,211,675 parameters** (exact count from
  `models/distilbert-phi/training_summary.json`) — far below the 1B cap —
  backed by a deterministic regex rule layer (recall-first hybrid).
- **Interface:** `deidentify(text) -> (masked_text, mapping)` and
  `rehydrate(response, mapping) -> text`; the same value always gets the
  same placeholder inside a note (`[NAME_1]`, `[DATE_2]`, ...).

## Quick start (one command)

```bash
pip install -r requirements.txt
python demo.py                    # end-to-end: mask -> LLM -> restore
```

The demo runs fully offline if no LLM key is configured (it falls back to a
deterministic mock so the pipeline always works — the demo says which
provider is in use). To use a real LLM in the round trip:

```bash
set GROQ_API_KEY=gsk_...                 # free tier, or:
set OPENAI_API_KEY=sk-...                # any OpenAI-compatible endpoint
set OLLAMA_MODEL=llama3.2                # or run Ollama locally
```

Other entry points:

```bash
python -m phi_gateway.data_gen           # regenerate synthetic train/dev data
python -m phi_gateway.build_testset      # rebuild the hand-labelled test set
python -m phi_gateway.train              # fine-tune the model (~2.5 h, CPU)
python -m phi_gateway.presidio_baseline  # run the Presidio comparison
python -m phi_gateway.evaluate --all     # full metric tables -> results/
python -m phi_gateway.utility_check      # 5 original vs 5 masked LLM answers
python demo.py --note path/to/note.txt   # any note, e.g. at the interview
python demo.py --interactive             # paste a note at the prompt
```

## How it works

**Masking (recall-first hybrid).**
1. A fine-tuned DistilBERT tags tokens (BIO, 13 entity types). It handles
   the context-dependent cases: people vs diseases ("Dr. Parkinson" masked,
   "Parkinson's disease" kept), person vs place, which number is an age.
2. A regex rule layer adds format-regular identifiers (SSN, phone/fax,
   email, URL, IP, dates, ZIP, labelled MRN/plan/account/licence numbers)
   and enforces the arithmetic rule the classifier can't do: *only ages
   over 89 are masked*.
3. Spans are unioned; the rule label wins overlap disputes (regexes are
   near-perfect on their formats). Same value -> same placeholder.
4. **Safety net:** the masked text is re-scanned; anything the rules still
   find there was missed by the merge and is masked late ("late catches"
   are reported, so a leak can't hide silently).

**Restoration.** `rehydrate` replaces placeholders back (a bracketed token
can't collide: `[NAME_10]` ≠ `[NAME_1]`). If the LLM returns a placeholder
that never existed in the input, it is **left untouched and reported** —
it carries no PHI, and silently deleting LLM output could corrupt clinical
meaning.

**Why the hybrid?** The brief's asymmetry: *a missed identifier is a data
leak, an extra mask is only an inconvenience.* The union of a high-recall
model and near-perfect regexes targets ~100% recall on formats while the
model handles ambiguity. Precision is tuned only where it doesn't cost
recall.

## Results

<!-- RESULTS_SECTION: filled by hand from results/ after evaluation -->

Training note: the run was stopped after epoch 1 because dev seqeval
(strict IOB2) F1 had already reached 0.9996 - epochs 2-3 were projected to
add under 0.001 for ~3 more CPU-hours. The epoch-1 checkpoint is the
shipped model (`models/distilbert-phi`).

See `results/RESULTS.md` (generated) for full tables. Headlines on the
25-note hand-labelled test set (414 identifiers):

| System | Precision | **Recall** | F1 | Leak rate |
|---|---|---|---|---|
| **PHI Gateway (DistilBERT + rules)** | 0.847 | **0.966** | 0.903 | **4%** |
| Model only (DistilBERT) | 0.476 | 0.915 | 0.626 | 28% |
| Rules only | 0.975 | 0.572 | 0.721 | 100% |
| Microsoft Presidio (baseline) | 0.582 | 0.746 | 0.654 | 88% |

Per-identifier-type precision/recall/F1: `results/RESULTS.md`
(seqeval strict-IOB2 cross-check printed by `evaluate --all`).

**Presidio comparison takeaways** (default recognizer registry + spaCy
`en_core_web_lg`): strong on PERSON/PHONE/EMAIL/IP, but zero recall on
medical-record, health-plan and account numbers (no default recognisers),
zero on the >89 age rule, and it misses most sub-state locations — 88% of
our test notes still leak at least one identifier.

**Utility check** (`results/utility_check.md`): the same 5 notes and 3
questions answered from original vs masked notes; average ROUGE-L F1
0.86 with the configured LLM. (0.86 with the offline mock LLM;
re-run `python -m phi_gateway.utility_check` with `GROQ_API_KEY` set for
real-LLM numbers.) Masking costs some specificity - dates/ages become
placeholders and name-dependent sentences lose their subject - but
diagnosis and management content survive.

## Data

- **Training:** 3,000 synthetic notes + 300 dev notes, generated by
  `phi_gateway/data_gen.py` — Faker values poured into 13 hand-written
  clinical templates (H&P, SOAP, discharge, referral, radiology, ED, psych,
  telehealth, operative, pathology, billing, voicemail, adversarial
  "trap-dense" notes) with deliberately varied formats, misspellings,
  header/table/signature layouts and ambiguity traps.
- **Test:** 25 notes (414 identifiers) written by hand in a style different
  from the generator, labelled inline `[[TYPE::value]]` and converted to
  exact character spans (`phi_gateway/testset_notes.py`,
  `phi_gateway/build_testset.py`).
- **No real patient data anywhere.** Every name, number and address is
  invented (Faker or hand-written fiction).

## HIPAA Safe Harbor coverage

Covered here (13 types): names (patients, relatives, clinicians);
sub-state geography (street, city, ZIP, facility); all calendar dates
except year-only mentions; ages over 89; phone and fax; email; SSN; medical
record numbers; health-plan/member/policy numbers; account/accession
numbers; licence/DEA/NPI numbers; URLs; IP addresses.

Deliberately **out of scope**, with reasons:

| Category | Why left out |
|---|---|
| Vehicle IDs / plates (L) | never appear as free text in the note types studied (i2b2 2014 likewise folds them into a rare ID category) |
| Device IDs / serials (M) | ditto; our rule layer's generic "labelled ID" regex would catch `serial:` if present |
| Biometrics (P) | not representable in text notes |
| Full-face photos (Q) | not representable in text notes |
| "Any other unique characteristic" (R) | open-ended; we cover the concrete clinical cases (rare-disease + small population would need expert risk assessment, not a regex) |
| States, countries | Safe Harbor permits geography at state level and above; we keep state names, mask cities/ZIPs |

Edge-case decisions (all enforced in both rules and training labels):

- "Dr. Parkinson diagnosed Parkinson's disease" → the clinician's name is
  masked, the disease stays. Same for Huntington/Bell/Crohn/Graves traps.
- Calendar dates (incl. month-year, month-day, MM/YYYY) are masked;
  **year-only mentions and relative time ("3 days post-op", "two weeks
  ago", "POD 3") stay** because clinical meaning depends on them.
- Ages >89 masked (the bare number); ≤89 kept. Policy thresholds
  ("anyone over 93 gets home visits") are not an individual's age and stay.
- Provider names: Safe Harbor technically doesn't require removing them
  (HHS FAQ) — the brief requires it, and it's the safe side, so we mask.
- Employer/school *organisation* names are kept (not a Safe Harbor
  identifier); care facilities are masked.
- ZIPs masked whole (3-digit-prefix partial release not worth the risk).
- Times of day (14:32) are kept — Safe Harbor restricts dates, not times.
- Known limitation: a birth **year** combined with the service date implies
  an age over 89; we follow the brief's letter (years stay) and note it.

## Repository map

```
demo.py                     one-command end-to-end demo
phi_gateway/
  labels.py                 13 entity types, BIO label space
  data_gen.py               synthetic training data (templates + Faker)
  testset_notes.py          25 hand-written test notes (inline labels)
  build_testset.py          markup -> character spans -> data/test.jsonl
  rules.py                  regex rule layer (recall safety net)
  train.py                  DistilBERT fine-tuning + label alignment
  decode.py                 BIO -> char spans (subword run expansion)
  inference.py              sliding-window NER over long notes
  masker.py                 deidentify()/rehydrate() gateway + safety net
  llm.py                    Groq / OpenAI-compatible / Ollama / mock
  presidio_baseline.py      Presidio comparison runs
  evaluate.py               P/R/F1 per type, leak rate, seqeval cross-check
  utility_check.py          5 original vs 5 masked LLM answers (ROUGE-L)
data/                       train/dev/test JSONL + demo notes
results/                    metrics, tables, utility check (generated)
docs/DEMO_SCRIPT.md         5-minute demo video plan
FAILURES.md                 failures log, written as they happened
RESEARCH_LOG.md             what was read/tried/decided, in order
```

## Sources

- HHS, *Guidance Regarding Methods for De-identification of PHI (HIPAA
  Privacy Rule)* — the 18 identifiers, ZIP/age/date special rules, provider
  name FAQ. https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html
- Stubbs & Uzuner, *Annotating longitudinal clinical narratives for
  de-identification: the 2014 i2b2/n2c2 shared task* (JAMIA 2015) —
  identifier taxonomy and where systems typically miss.
- Hugging Face NLP course, token-classification chapter — BIO tagging and
  subword label alignment. https://huggingface.co/learn/nlp-course
- Model cards: `distilbert-base-cased`, `bert-base-cased`,
  `emilyalsentzer/Bio_ClinicalBERT`, `microsoft/deberta-v3-small`.
- Microsoft Presidio docs. https://microsoft.github.io/presidio/
- Faker docs. https://faker.readthedocs.io/
- seqeval. https://github.com/chakki-works/seqeval
- MTSamples-style public transcription structure informed the *shape* of
  the synthetic templates (structure only; no real reports copied).

## Reproducing

Everything is deterministic given the seeds baked into the scripts
(Faker/`random` seeds 42/1337, Trainer seed 42). On a 12-core CPU:
data generation ~20 s, training ~100 min (1 epoch; stopped when dev F1 hit 0.9996 - see README results note), full evaluation ~4 min
(model inference over 25 notes), Presidio baseline ~2 min.
