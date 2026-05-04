---
name: smtv
description: Summarize "The Morning Show" episodes from the @StockMarketMedia YouTube channel into an article-style HTML page with a locked editorial design. Auto-fetches video and transcript, applies article-genie writing rules, outputs to docs/output/smtv-YYYY-MM-DD.html and opens it in the browser (locally).
---

# SMTV Summarizer

Summarize daily episodes of "The Morning Show" on the @StockMarketMedia YouTube channel into a self-contained, article-style HTML page that a random reader who has never seen the show could understand.

## When to invoke

The user types `/smtv`, `/smtv [URL]`, `/smtv today`, or `/smtv YYYY-MM-DD`, OR says any natural-language equivalent ("summarize today's SMTV", "make today's morning show article", pastes a YouTube URL from the channel).

Also runs daily as a Claude Code routine (Tue-Sat 6 AM PHT). In routine mode, the cloud session clones this repo, runs the workflow, commits the HTML to `docs/output/`, pushes, then POSTs the public URL to Telegram.

## Working directory

All commands assume the current working directory is the project root (the directory containing this `SKILL.md`). Locally that's `~/smtvsummarizer/`. In the cloud routine, it's the freshly cloned repo. If you're not there, `cd` to it first before running anything.

## Cast and how to handle each speaker

- **Spencer** (host): drives conversation, reads the price tape, hands off topics. Don't attribute lines to him in prose.
- **JC** (regular analyst): big-picture frameworks, macro takes, oil/energy bull. His big takes are included.
- **Steve "Strazza"** (regular analyst): charts, "junky crypto" book, hedging trades. His takes are included.
- **Kenny Glick** (rotating, day trader): VWAP options, intraday levels. His content is mostly day-trade setups. **DO NOT include in default articles.**
- **Louis Sykes** (rotating, crypto): every Friday at minimum. His takes are PROMINENT in the Crypto chapter when he's on.
- **All other guests** (Jeff Mackey, Sean McLaclin, Larry Thompson, Andrew O'Donnell, Mary, Phil Pearlman, etc.): SKIP entirely. Do not give them sections. Do not name them. Useful content can be folded into prose without attribution.

## Reader assumption

The user is advanced in crypto and onchain markets but a self-described newbie at stocks, indices, FX, ETFs, and traditional macro. When mentioning anything stock-side, briefly explain inline:

- ETFs (especially niche/sector/thematic): name the underlying theme and dominant holdings
- Tickers beyond well-known megacaps (NVDA, TSLA, MSFT, AAPL, GOOGL, META, AMZN, AMD, COIN, MSTR, HOOD): brief one-line context
- Stock-market jargon (float, short interest, days to cover, polarity, VWAP, sympathy bid, capex tone, breadth, correlation coefficient, etc.): swap for plain English or define inline
- Specific FX moves: name the currency and what it affects

Crypto concepts do NOT need to be dumbed down.

## Workflow

1. **Resolve the video.**
   - URL provided → use directly.
   - "Today" or no input → `python fetch_video.py`
   - Date → `python fetch_video.py YYYY-MM-DD`

2. **Fetch transcript.** Run `python fetch_transcript.py <video_id>` and save the JSON output to `past-shows/transcript-<video_id>.json`. Then run a quick Python one-liner to flatten it to `past-shows/transcript-<video_id>.txt` with `[MM:SS] text` per line. If transcript is not yet available, tell the user and offer to retry in 30-60 minutes.

3. **Read the transcript.** Read the flat-text file in chunks (~700 lines per Read call). Identify show segments and the day's main story.

4. **Compose the article content** following the structure and rules below.

5. **Render.** Read `template.html`. Substitute `{{title}}`, `{{subtitle}}`, `{{source_line}}`, `{{video_url}}`, `{{date}}`, `{{duration}}`, `{{read_time}}`, `{{tldr_headline}}`, the `<!-- TLDR_BULLETS -->` block, the `<!-- CHAPTERS -->` block, and the `<!-- BOTTOM_LINE_POINTS -->` block. Write final HTML to `docs/output/smtv-YYYY-MM-DD.html`.

6. **Open in browser** (local only; skip in routine). Run `open docs/output/smtv-YYYY-MM-DD.html`.

7. **Routine mode only**: after writing the file, commit and push (`git add docs/output/smtv-YYYY-MM-DD.html && git commit -m "Add smtv-YYYY-MM-DD" && git push`), then POST the public Pages URL to Telegram using the env vars `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Public URL pattern: `https://halibutcrypto.github.io/smtvsummarizer/output/smtv-YYYY-MM-DD.html`.

## Article structure

Two templates depending on day of week.

### Friday (Louis Sykes is on)

1. **Crypto** chapter, substantial. Lead with Louis content: spot prices, his structural calls (e.g. "$SOL underperform the decade"), his pick-of-the-week if any, alt rotation read. Real meat in this chapter.
2. **Markets / lead story.** The day's main news beat (Intel ATH, Fed day, big-tech earnings, etc.).
3. **Special framework or theme** (when applicable). JC's chart of the day, big macro framework, sequential history (use the `.timeline` component), short-squeeze regime, etc.
4. **Quotes.** 3-4 verbatim quotables.
5. **Bottom Line.** 3 numbered takeaways. Never 4.

### Non-Friday (no Louis)

1. **Crypto** chapter, shorter. Find the macro→crypto angle even on slow crypto days. If the macro is BTC-friendly (dollar weakening, metals up, stocks up), say so. If a meme/alt is breaking out, flag it. Don't pretend nothing's happening.
2. **Markets / lead story.** The day's main beat.
3. **Big Tech, earnings, or framework.** Whatever the second story is.
4. **Quotes.** 3-4.
5. **Bottom Line.** 3 numbered.

## Writing rules (strict, zero tolerance)

These are article-genie's rules. They are absolute.

- **No em dashes.** Not `—`, not `–`, not double hyphens used as dashes. Use commas, periods, semicolons, parentheses.
- **No "X, not Y" reveal patterns.** Banned: "It's not X, it's Y," any sentence ending with ", not [contrast]." Examples banned: "This is structural, not cyclical." "It's a buy thesis, not a trade." "The signal is real, not noise." Just state the claim.
- **No colon-as-setup in prose.** Max 2 colons in prose total across the entire article. Colons inside visual components (stat cards, lists, takeaways) don't count. Banned colon patterns include "His take:", "The number:", "The framework:", "Here's the thing:", "The reason?". Restructure with periods or commas.
- **No fake enthusiasm openers.** "Great", "Love this", "Absolutely", "Solid". Get into substance.
- **No AI slop.** "It's worth noting", "To be fair", "That said", "It bears mentioning".
- **No cliche scene-setters.** "You wake up Tuesday and..." kind of openers. State the news directly.
- **No naming non-Louis guests.** Mackey/Sean/Larry/Andrew/Mary/Phil are not in the article. Their content, if used, is folded in without attribution.
- **Speaker attribution in prose is light.** Drop it where possible. Keep it on verbatim quotes for verifiability.

## Final-pass scan (mandatory before declaring done)

After composing the article, do a deliberate scan of the prose body against the banned patterns. Common slips that have shipped in past articles:

1. **The ", not [X]" tail.** Search every period for sentences that end with ", not [contrast]". Examples that slipped in: "That's the design, not a disappointment." / "Until it doesn't, sit out, not chase." Fix: drop the contrast tail or split into a separate sentence.
2. **The "isn't X, it's Y" pattern across a comma.** Examples: "Tesla isn't priced for today's cars, it's priced for tomorrow's." Fix: rewrite as two declarative sentences.
3. **Colons used as setup.** Search the prose for ":" and count. Common offenders: "For positioning today:", "Translation:", "Here's the framework:", "The number to internalize:". Allowed inside visual components, capped at 2 in prose. Fix: comma, period, or restructure.
4. **Em dashes.** Search for `—` `–` and `--`. None should appear.

Do this scan before saving. Treat it as part of the workflow, not optional polish.

## Filtering priorities

User cares about, in order:

1. Crypto / BTC (especially Friday with Louis)
2. Broader market and indices (SPX, NDX, Dow)
3. Precious metals (gold, silver). Usually short, skip if no movement.
4. Individual prominent stocks: NVDA, TSLA, COIN, MSTR, MSFT, AAPL, AMD, GOOGL, META, AMZN, HOOD
5. Verbatim quotes worth tweeting (3-4 max). If a quote is "ass" (vague, not actually quotable), cut it.
6. Strong frameworks worth saving (chart of the day, conceptual takes, cycle frameworks)

Skip or compress hard:

- Off-topic banter (food, sports, kids, gear, sex jokes, life logistics)
- Non-Louis guests entirely
- Day-trade setups, VWAP entries, scalp-style trades
- Small caps the user doesn't trade
- Sector content outside priority list (utilities, biotech, cannabis) UNLESS it's the day's main story or has a clear crypto crossover

Target 1000-1500 words of prose total. More than that is too long.

## Visual components

CSS is in `template.html`. Use these components when content fits.

### Tickers and prices (inline in prose)

```html
<span class="tk">$BTC</span> <span class="pr">$78,150</span> <span class="ch up">+1%</span>
```

`.tk` is bold orange mono - the locked ticker style. NEVER use chip/badge backgrounds (rejected as corny).
`.pr` is bold mono dark for prices.
`.ch` is mono with `.up` (green), `.down` (red), or `.flat` (muted) modifiers.

### Stat card grid (4+ price points)

```html
<div class="stats">
  <div class="stat">
    <div class="stat-label">S&amp;P 500</div>
    <div class="stat-value">7,200</div>
    <div class="stat-change up">+0.5% · ATH</div>
  </div>
  <!-- more stat divs -->
</div>
```

### Pull quote (Quotes chapter)

```html
<div class="pullquote">
  <blockquote>"Verbatim quote text."</blockquote>
  <div class="attrib">JC, brief context if useful <a class="ts" href="https://www.youtube.com/watch?v=VIDEO_ID&amp;t=300s" target="_blank">[5:00]</a></div>
</div>
```

### Compare grid (winners vs losers)

```html
<div class="compare">
  <div class="winners">
    <div class="head">Winners</div>
    <ul><li><span class="tk">$GOOGL</span> · breakaway gap, ATH</li></ul>
  </div>
  <div class="losers">
    <div class="head">Losers</div>
    <ul><li><span class="tk">$META</span> · screw-you capex stance</li></ul>
  </div>
</div>
```

Green-tinted = positive. Red-tinted = negative. Never swap.

### Timeline (sequential historical events with a pattern)

```html
<div class="timeline">
  <div class="timeline-item">
    <div class="year">1901</div>
    <h4>US Steel formed</h4>
    <p>Description.</p>
  </div>
  <!-- more items -->
</div>
```

### Margin notes (cross-topic crossovers)

```html
<div class="note crypto">
  <div class="label">The crypto angle</div>
  <p>Connect the chapter's topic back to the user's crypto world.</p>
</div>
```

Three flavors:
- `.note.crypto` (orange top border): use ONLY in non-crypto chapters when there's a real crossover. NEVER in the Crypto chapter (redundant).
- `.note.local` (navy top border): "Local angle (Philippines)" or similar. Use when something specific to PHP/Philippines comes up.
- `.note` (default amber top border): generic call-out.

### Bottom line (always at the end, dark card)

```html
<section class="bottom-line">
  <h2>The Bottom Line</h2>
  <ol>
    <li><strong>Headline.</strong> Body of the takeaway.</li>
    <!-- exactly 3 -->
  </ol>
</section>
```

The `.bottom-line .pr`, `.bottom-line .ch`, and `.bottom-line .tk` color overrides in `template.html` are CRITICAL. Do not remove. Without them, prices render invisible against the dark background.

## Visual style locked in

- Theme: warm light, NOT dark
- Background: `#faf8f2` (cream/paper)
- Surface: `#ffffff`
- Accent: `#d4530b` (orange) - main color, used for tickers, chapter labels, TL;DR pill, pull quote borders, timestamp links
- Fonts (Google Fonts loaded in template.html):
  - Space Grotesk 700 for headings
  - IBM Plex Sans 300/400/500 for body
  - IBM Plex Mono 600/700 for tickers, prices, timestamps
- Max width 860px

## Headline style

Title is a real editorial headline written about the day's content, not the YouTube video title. Like a Bloomberg or FT headline. It should hook the day's biggest story.

Subtitle is a single sentence under the title that adds the secondary thread. Frames the argument or hook, never describes the format.

Examples we've shipped:
- "Stocks Hit Fresh All-Time Highs Through a 3% Yen Eruption"
- "Intel Caps 26 Years of Pain at New All-Time Highs"
- "Big Tech's Super Bowl, Powell's Last Dance, and the Stock-Pickers' Market Comes Back"

## Output

- File path: `docs/output/smtv-YYYY-MM-DD.html`
- Date in filename = the show's broadcast date in PHT
- Locally: auto-open in default browser after writing
- Routine: commit + push to GitHub, then notify via Telegram. Public URL: `https://halibutcrypto.github.io/smtvsummarizer/output/smtv-YYYY-MM-DD.html`

## Reference articles for style

- `docs/output/smtv-2026-04-30.html` (Thu, slow day, no Louis)
- `docs/output/smtv-2026-04-24.html` (Fri, Louis on, timeline component used for IPO history)
- `docs/output/smtv-2026-04-29.html` (Wed, pre-earnings setup, framework chapter)

If you're unsure how to render something, look at these for a known-good example.
