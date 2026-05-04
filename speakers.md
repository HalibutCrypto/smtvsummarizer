# SMTV Speakers

Speaker profiles for "The Morning Show" on @StockMarketMedia. Profiles get populated after analyzing the past 10 episodes (Phase 1 next step). Used by the skill for accurate attribution since YouTube auto-transcripts have no speaker labels.

## Spencer (Host)
Role: Host, drives the conversation, hands off topics to analysts.
Patterns: TBD after past-episode analysis.

## JC (Regular Analyst)
Role: Markets, charts, technicals.
Patterns: TBD after past-episode analysis.

## Steve (Regular Analyst)
Role: Markets, charts, technicals.
Patterns: TBD after past-episode analysis.

## Kenny Glick (Special, Day Trader)
Role: VWAP options, intraday levels, tape reading.
Patterns: TBD after past-episode analysis.

## Louis Sykes (Special, Crypto)
Role: Crypto markets. Appears at minimum every Friday.
Patterns: TBD after past-episode analysis.

## Random Guests
Patterns: Spencer typically introduces them with name and firm at the top of their segment.

---

## How attribution works (current approach)

YouTube auto-captions don't include speaker labels. The skill infers speakers from:
1. Spencer's hand-offs ("JC, what are you seeing in oil?", "Kenny, take it away.")
2. Topic + style (Kenny on intraday levels, Louis on BTC, etc.)
3. Catchphrases (populated from past-episode analysis below)

Confidence isn't 100%. When a take could plausibly be either of two speakers, the skill labels it with the more likely speaker and adds "(or {other})" rather than guessing falsely confidently.
