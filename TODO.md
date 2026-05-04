# SMTV Summarizer TODO

## Phase 1 status: COMPLETE

Format locked. Three reference articles produced and iterated. Writing rules + visual style + filter rules all encoded in `SKILL.md`. CSS shell extracted to `template.html`.

- [x] Install Python deps
- [x] Smoke test `fetch_transcript.py`
- [x] Smoke test `fetch_video.py` (works for today + recent dates, depth-limited for older episodes by design)
- [x] First end-to-end run (smtv-2026-04-30.html)
- [x] Second run with Louis on (smtv-2026-04-24.html)
- [x] Third run, pre-earnings setup (smtv-2026-04-29.html)
- [x] Iterate writing/visual until format feels right
- [x] Add HOOD to stocks list
- [x] Capture locked-in format into `SKILL.md` and `template.html`
- [x] Save user reader-level + project context to memory

Skipped intentionally:
- Speaker profile pre-training. User opted out, said attribution accuracy isn't worth context bloat.

## Phase 2 (next valuable wins)

- [ ] Daily index page (`output/index.html`) listing all summaries by date with title and key tickers. Auto-update on each new article.
- [ ] Telegram delivery: private bot pushes notification + link the moment a new summary lands. Needs user to make a bot via @BotFather and provide the token.
- [ ] Search/filter on the index (by ticker, by speaker, by date range)

## Phase 3 (automation)

- [ ] Cron schedule: 6 AM PHT weekday only (so user wakes up to a fresh summary)
- [ ] US market holiday calendar awareness (skip days with no show)
- [ ] Headless Claude Code mode for the daily auto-run (uses CC subscription)
- [ ] Smart retry on transcript availability (30-min interval, up to 4 hours)

## Refinements / nice-to-haves

- [ ] Fold cannabis-style "concentrated thesis" guest content (when it crosses prominent stocks or is a major sector call) — currently skipped entirely with all non-Louis guests
- [ ] Sharpen `stocks.json` based on which tickers actually come up over time
- [ ] Python helper that takes structured JSON + `template.html` and renders the final HTML (currently Claude does substitution manually). Useful for Phase 3.

## Discarded for v1 (revisit only if needed)

- One-tap copy buttons on quotables (user rewrites quotes anyway)
- Whisper fallback transcription (YouTube auto-captions reliable enough)
- Topic chips on each section
- Character count on quotables
- Ticker chip backgrounds (rejected as corny)
- "Trade setups" / day-trade chapter (user doesn't act on these)
- Crypto-angle margin note inside crypto chapters (redundant)
- 4-point Bottom Line (felt forced; locked at 3)
