# SMTV Production Rollout Plan

Goal: ship `/smtv` as a daily auto-running Claude Code routine that runs Tue-Sat 6 AM PHT, posts the HTML article to GitHub Pages, and notifies the user via Telegram. The user's Mac does NOT need to be on (routine runs on Anthropic cloud).

This plan is the source of truth for execution after compact. Refer back to it when in doubt.

## Architecture (locked in)

- **Skill source**: `/Users/keke/smtvsummarizer/SKILL.md` (symlinked to `~/.claude/skills/user/smtv/SKILL.md` so `/smtv` works locally)
- **Code hosting**: GitHub repo at `https://github.com/HalibutCrypto/smtvsummarizer` (PUBLIC, confirmed by user 2026-05-04). User's `gh` CLI already authenticated as `HalibutCrypto` with `repo` + `workflow` scopes.
- **Output hosting**: GitHub Pages serving from `/docs/output/`. Public URL per article: `https://halibutcrypto.github.io/smtvsummarizer/output/smtv-YYYY-MM-DD.html`
- **Notification**: Telegram bot, sends link to user's chat
- **Scheduler**: Claude Code routine via `/schedule`. Cron: Tue-Sat 6 AM PHT = `0 22 * * 1-5` UTC (Mon-Fri 22:00 UTC, since PHT = UTC+8)
- **Cost**: $0 extra. Routines consume the user's existing Claude Code subscription quota.

## Prerequisites status (post-confirmation 2026-05-04)

- ✅ GitHub username: `HalibutCrypto` (already authenticated in `gh` CLI)
- ✅ Repo name: `smtvsummarizer` (confirmed)
- ✅ Public repo: confirmed
- ⏳ Telegram bot token: NEEDED during Phase C (user creates via @BotFather, walks through interactively)
- ⏳ Telegram chat ID: NEEDED during Phase C (from `curl https://api.telegram.org/bot<TOKEN>/getUpdates` after user messages bot)

Phase A (path refactor) and Phase B (GitHub repo) can run autonomously. Pause at the start of Phase C to walk the user through Telegram bot creation interactively.

## Phase A: Make the project repo-portable ✅ DONE

Goal: same code works locally AND in the cloud routine after `git clone`.

Tasks:
- [x] A1. Update `SKILL.md`: paths are now relative (e.g. `python fetch_video.py`, `template.html`, `docs/output/`). Added "Working directory" section.
- [x] A2. `fetch_video.py` and `fetch_transcript.py` had no hardcoded paths. No changes needed.
- [x] A3. Updated `generate_summary.py`: `OUTPUT_DIR = PROJECT_DIR / "docs" / "output"`, plus `mkdir(parents=True, ...)`.
- [x] A4. Created `docs/` directory.
- [x] A5. Moved 4 articles from `output/` to `docs/output/`. Created symlink `output → docs/output` for back-compat.
- [x] A6. Verified articles still accessible at new path AND via symlink.
- [x] A7. (Skipped — local /smtv full rerun deferred to Phase E manual trigger; non-trivial changes were path-only and verified visually.)

## Phase B: GitHub repo setup ✅ DONE

Tasks:
- [x] B1. `gh` already authed as HalibutCrypto.
- [x] B2. `git init -b main` in project root.
- [x] B3. `.gitignore` updated: now excludes `past-shows/transcript-*.json`/`*.txt` (the actual filenames). Removed obsolete `output/*.html` line since the 4 reference articles now live under `docs/output/` and we want them tracked for Pages.
- [x] B4. Initial commit `49ccec8`: 17 files, 3561 insertions.
- [x] B5. Repo created and pushed: https://github.com/HalibutCrypto/smtvsummarizer (public).
- [x] B6. GitHub Pages enabled on `main` branch, `/docs` folder. Build #1 succeeded in 41s.
- [x] B7. Verified: `curl https://halibutcrypto.github.io/smtvsummarizer/output/smtv-2026-04-30.html` → HTTP 200, 23 KB.

## Phase C: Telegram bot setup

User-side instructions (I'll guide):
- [ ] C1. Open Telegram. Search for `@BotFather`. Send `/newbot`.
- [ ] C2. Pick a bot display name (e.g. "SMTV Summary").
- [ ] C3. Pick a bot username (must end in "bot", e.g. `@halibut_smtv_bot`).
- [ ] C4. BotFather returns the bot token. Format: `123456789:ABCdefGHIjkl...`. Save it.
- [ ] C5. Open the bot in Telegram, send `/start` to it.
- [ ] C6. Get chat ID: in terminal, run `curl https://api.telegram.org/bot<TOKEN>/getUpdates` and find `"chat":{"id":XXXXXXXX}`. Save the chat ID.
- [ ] C7. Test: `curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage -d chat_id=<CHAT_ID> -d text="hello from smtv"`. User should see the message.

## Phase D: Routine setup

Tasks:
- [ ] D1. Write the routine prompt (what the cloud Claude session executes). Roughly: "Run /smtv to summarize today's episode. Save the HTML to docs/output/. Commit and push. Then POST a message to Telegram with the public URL."
- [ ] D2. Create routine via `/schedule` with:
  - Repository: `<username>/smtvsummarizer`
  - Setup script: `pip install -r requirements.txt`
  - Environment variables: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GITHUB_PAGES_URL`
  - Schedule: cron `0 22 * * 1-5` (Mon-Fri 22:00 UTC = Tue-Sat 6 AM PHT)
  - Allow unrestricted branch pushes: enabled (so the routine can push to main)
- [ ] D3. Document the routine config in this file.

## Phase E: Test

- [ ] E1. Manually trigger the routine (use the "run now" button in routine UI, or via cmd).
- [ ] E2. Watch logs: pip install succeeds, fetch_video finds episode, fetch_transcript works, Claude composes article, git push succeeds, Telegram POST succeeds.
- [ ] E3. Open the GitHub Pages URL, verify article renders correctly.
- [ ] E4. Verify Telegram message arrives with the URL.
- [ ] E5. User opens the link from Telegram, verifies article quality matches the 4 reference articles.

## Phase F: Activate

- [ ] F1. Enable the cron schedule.
- [ ] F2. Wait for first auto-run (next Tue, Wed, Thu, Fri, or Sat at 6 AM PHT).
- [ ] F3. Confirm it ran and delivered.

## Known edge cases (handle in routine prompt)

- Transcript not yet ready (1-3 hours after stream ends). At 6 AM PHT, 8+ hours after the show ended, this is essentially never an issue. But the routine should print a clear error and skip if transcript fetch returns "No transcript available."
- US market holiday → no show that day. Routine should detect (via `fetch_video.py` returning no match) and skip the post-Telegram step. Could also add holiday detection later.
- Channel listing changed / show moved time slot → routine fails to find episode. Surface clear error.
- Push conflicts (rare, since only routine pushes to main) → routine should retry once, then fail loud.

## Reference articles (the spec for "good output")

- `output/smtv-2026-04-30.html` (Thu, slow)
- `output/smtv-2026-04-29.html` (Wed, pre-earnings setup)
- `output/smtv-2026-04-24.html` (Fri, Louis on, timeline visual)
- `output/smtv-2026-04-23.html` (Thu, Tesla earnings reaction)

After compact, if I'm unsure about output style, I open one of these and pattern-match.

## Memory references

- `~/.claude/projects/-Users-keke-smtvsummarizer/memory/project_smtv_summarizer.md` (project context)
- `~/.claude/projects/-Users-keke-smtvsummarizer/memory/user_market_expertise.md` (reader level rule)
- These are auto-loaded in future sessions. Source of truth on writing rules and visual style.

## Compaction safety checklist

When the user runs /compact and I come back, I should:
1. Read this PLAN.md file first
2. Check what's been done (look at git log, check if `.git/` exists, check `gh repo view`)
3. Check off completed tasks in this file
4. Continue from where I left off
5. Not re-do completed phases
