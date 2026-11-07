# Demo video script (<= 5 minutes)

Setup before recording: `pip install -r requirements.txt`, model trained
(`models/distilbert-phi` exists). The round-trip LLM needs NO API key: the
demo automatically uses a local Qwen2.5-0.5B-Instruct on CPU (first run
downloads ~1 GB once; answers stream live in the terminal at ~4-5 tok/s).
Optional `set GROQ_API_KEY=...` for instant cloud answers instead - say on
camera which provider is running (the demo prints it).

| Time | What to show | Command / action |
|---|---|---|
| 0:00-0:25 | The problem: hospitals can't send identifiable notes to an LLM; the gateway masks before and restores after; mapping never leaves the machine. | slides/terminal intro |
| 0:25-1:00 | Repo tour: data generator, hand-labelled test set, rule layer, model, gateway, eval. | quick file tree walk |
| 1:00-2:30 | LIVE: the one-command demo on the bundled note. Point out: original note, masked note (names, dates, MRN, phone, email, URL all become [TYPE_n]), the private mapping table ("this is what the LLM never sees"), LLM answer on masked input, rehydrated answer. | `python demo.py` |
| 2:30-3:10 | Ambiguity highlight: run demo on `data/test_ambiguity.txt` (Dr. Parkinson vs Parkinson's disease; ages 89 vs 90; "3 days post-op" kept). | `python demo.py --note data/test_ambiguity.txt` |
| 3:10-4:00 | Numbers: headline recall, per-type table, leak rate, side-by-side with Presidio (Presidio misses MRN/health-plan/account/AGE and most locations; we don't). | show `results/RESULTS.md` |
| 4:00-4:40 | Utility check: same 5 notes, same questions, original vs masked answers + ROUGE-L; explain the recall-first trade-off (extra masks are an inconvenience, a miss is a leak). | show `results/utility_check.md` |
| 4:40-5:00 | Unknown-placeholder behaviour: LLM answers with [NAME_9] that never existed -> left untouched and reported; recap privacy guarantees. | point at demo output / code in `masker.py` |

Live-interview checklist (same repo, fresh note from the panel):
`python demo.py --note their_note.txt` - then walk them through
`phi_gateway/masker.py` (merge + safety net), `rules.py` (one regex),
`train.py` (label alignment), and be ready to make a small change on the
spot (e.g. add a new date format to `rules.py` and re-run the demo).
