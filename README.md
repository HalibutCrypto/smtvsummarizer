# SMTV Summarizer

Claude skill that summarizes "The Morning Show" from the [@StockMarketMedia](https://www.youtube.com/@StockMarketMedia) YouTube channel.

## What it does

Fetches today's episode (or a specified one), pulls the transcript with timestamps, and generates a themed HTML summary focused on:

- Crypto / BTC (pinned to top)
- Broader market and indices (S&P, Nasdaq, etc.)
- Precious metals (gold, silver)
- Individual prominent stocks (lite coverage)
- Verbatim quotables (raw material for tweets)
- Strong takes (high-conviction calls, frameworks, levels)

Every section has clickable timestamps that jump back into the YouTube video at the exact moment.

## Project layout

```
.
├── README.md             this file
├── SKILL.md              Claude skill instructions
├── TODO.md               Phase 2/3 features
├── requirements.txt      Python dependencies
├── fetch_video.py        find today's episode on the channel
├── fetch_transcript.py   get transcript with timestamps
├── generate_summary.py   main orchestrator (skeleton, fills in next)
├── template.html         HTML output template
├── speakers.md           speaker profiles (built from past 10 episodes)
├── stocks.json           prominent tickers list
├── past-shows/           cached past episode transcripts
└── output/               generated summary HTML files land here
```

## How to run (manual v1)

```bash
# one-time setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# summarize today's episode
python generate_summary.py

# summarize a specific URL
python generate_summary.py https://www.youtube.com/live/xOSeC6lanRU

# summarize by date
python generate_summary.py --date 2026-05-01
```

Output lands in `output/smtv-YYYY-MM-DD.html` and opens in your browser.

## Phase plan

| Phase | What | Status |
|-------|------|--------|
| 1 | Manual invoke. Skeleton + first working run on past episode. | in progress |
| 2 | Telegram delivery, daily index page. | TODO |
| 3 | Daily 6 AM PHT weekday auto-run, US market holiday awareness, headless Claude Code. | TODO |
