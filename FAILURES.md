# FAILURES.md

Written as I went; every real failure that cost time, in order.

1. **HHS page 403 for the fetcher.** `WebFetch` got HTTP 403 from
   hhs.gov (bot protection). Fixed by using a different reader tool for the
   same URL. Lesson: keep a second fetch path for stubborn government sites.

2. **Syntax error generating data (mismatched bracket).** A `{...}` dict in
   `data_gen.py` closed with `]`. Python pointed at the wrong line
   ("closing parenthesis ']' does not match '{'") - cost a couple of minutes
   of staring. Lesson: the bracket Python reports is where it *noticed*,
   not necessarily where the mistake is.

3. **Label alignment round-trip failed 20/20 notes.** The check I wrote
   (labels -> decode -> compare spans) reported every note wrong with spans
   ~1-10 chars short. Two separate causes:
   - the decoder treated every non-word-start token as "not part of the
     entity", so multi-token words ("www.portal.com" tokenises as
     www . portal . com with only "www" labelled) collapsed to their first
     token. Fix: run-expansion decoding (`decode.py`) - a labelled token
     expands across contiguous tokens to the full word run.
   - trailing sentence punctuation ("Reidstad.", "430318833)") got glued
     onto spans. Fix: trim ` \t\n\r,;:.)]` from span tails (periods stay on
     genuine "St." suffixes - a documented 1-char imperfection).
   After fixes: 20/25 test notes reconstruct exactly; the rest differ only
   by boundary punctuation.

4. **Entities glued to punctuation got no label at all.** "(04/2026"
   tokenises as "(" + "04/2026"; "04" is contiguous with "(" so it looked
   like a continuation subword and got -100 - the whole DATE silently
   unlabelled. This is exactly the class of silent bug the brief warns
   about. Fix: a token is a word start if whitespace precedes it OR it
   starts a gold entity (`train.align_labels`).

5. **AGE spans absorbed "-year-old".** "94-year-old" is one word run, so
   run expansion produced an 11-char AGE span where gold is the 2-digit
   number. Fix: AGE never run-expands (`NO_EXPAND_TYPES` in decode.py).

6. **AGE rule missed real entities while the pattern was fine.** Two test
   misses ("97-year-old matriarch", "turn 95 next month"): my regex put the
   age evidence in a LOOKAHEAD, then the Python check searched for it in
   `group(0)`, which excludes lookaheads. Fix: check the text *after* the
   number for the suffix, and the prefix+before-window for an age cue.

7. **My own gold labels had errors - found by the rules layer.** The rule
   scan flagged "Visit date: 04/09/2025" in test_01 as a spurious DATE; it
   was a *gold* miss (I had written it unmarked). Also fixed: "tomorrow"
   and "Monday" wrongly marked as DATE (relative time must stay),
   "Atlanta" unmarked, "01/09-01/11" unmarked, name-word mentions
   ("first name Austin") unmarked. Lesson: always cross-check gold labels
   against an independent detector; hand labels rot too.

8. **Bare 10-digit phones missed.** "contacted at 5550172398" failed
   because (a) `\bcontact\b` doesn't match "contacted", (b) my
   context window excluded `.` and "D. SMYTHE" broke it, (c) the number
   started its own line so the same-line window was empty. Fix: substring
   search for phone words in a 60-char window (previous line included when
   the current one is empty), plus an "ID label directly before" guard to
   avoid stealing MRNs.

9. **MM/YYYY dates and dotted dates unmatched.** "04/2025" needed its own
   pattern (with a sub-span dedupe so "09/2025" inside "04/09/2025"
   doesn't double-fire); "29.Oct.2025" needed `.` as a separator in the
   day-month-year regex.

10. **Silent buffer: couldn't watch training progress.** I piped the
    training command through `grep | tail`, which buffers everything until
    the process exits - the log file stayed 0 bytes for an hour. The run
    itself was fine (verified via the process table). Lesson: write logs
    straight to a file; grep the file, don't pipe the process.

11. **`age_chunks` unpacking crash** (`ValueError: too many values to
    unpack`) - mixed str/tuple parts unpacked as (text, label). Fix: a
    `NoteBuilder.mixed()` helper that accepts both. Also one stray
    multi-argument `b.t()` call and a dead stub function with a bad
    annotation - all caught by the first generator run.

12. **Windows quirks.** HF hub symlink warning (cosmetic); spaCy
    en_core_web_lg download needed a separate step after presidio install;
    `dataloader_num_workers=0` set deliberately to avoid Windows
    multiprocessing hangs in the Trainer.

13. **Padded-batch decoding crash (found only with the trained model).**
    `inference.py` zipped the *padded* batch ids back against per-window
    offsets, so decoding a short window in a mixed-length batch ran past
    its offsets (IndexError). The random-head smoke test missed it because
    single-window batches pad to their own length. Fix: keep each window's
    true length and decode with that. Lesson: smoke-test the unhappy path
    (mixed batch sizes), not just the happy one.

14. **Span-type theft in the merge.** The model's ACCOUNT guess overlapping
    a rule-detected LICENSE span kept the model's type, because my priority
    check compared type *sets* instead of which span came from which layer.
    Result: LICENSE recall 20% despite the rules being perfect on it. Fix:
    spans carry a `rule` flag; any overlap resolves to the rule layer's
    type. LICENSE (and ACCOUNT) went back to 100% recall.

15. **Edit ate the `rehydrate` method.** While inserting the surname-recall
    method, my edit replaced the `def rehydrate(...)` line without
    re-adding it; its body became unreachable code inside the new method
    (syntactically valid, silently). Caught by the test suite
    (`AttributeError: no attribute 'rehydrate'`). Lesson: run the tests
    after every refactor, before any eval.

16. **Evaluation was blind to the safety nets.** The late-catch and
    surname passes mask spans in *masked-text* coordinates, but
    `entity_list` only carried pass-1 original-text spans - so eval under-
    reported exactly the recall features that had been added (leak rate
    stuck at 16% while the masked output was actually clean). Fix: a
    coordinate map (masked char -> original char) so every pass reports
    spans in original coordinates. Leak rate 16% -> 4% with no behaviour
    change - the metrics finally described reality.

17. **Model split one name into two spans** ("Dr" + ". Felicity
    Huntington") and even masked a timestamp ("07:52") as NAME. Fixes:
    stitch same-label model spans separated only by punctuation, and drop
    pure-time NAME/LOCATION spans.

18. **transformers 5: `apply_chat_template` returns a BatchEncoding.**
    The local-LLM path crashed with `ones_like(): argument 'input' must be
    Tensor, not BatchEncoding` - v5 returns a dict even with
    `return_tensors="pt"`. Fix: `return_dict=True` and generate with
    `**enc`, slicing output by `enc["input_ids"].shape[1]`.

19. **bfloat16 was SLOWER than fp32 on this CPU.** Assumed BF16 weights
    would speed the local LLM up; measured 3.1 vs 4.6 tok/s - the CPU has
    no native BF16 path, so it emulates. Benchmark before believing.
    fp32 + capped tokens + live streaming is the demo configuration.
