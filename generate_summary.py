"""
Main orchestrator: resolve video, fetch transcript, generate themed HTML summary.

Usage:
    python generate_summary.py                            # today's episode
    python generate_summary.py <youtube_url>              # specific URL
    python generate_summary.py --date 2026-05-01          # specific date

Output: output/smtv-YYYY-MM-DD.html (auto-opens in browser).

NOTE: This is the v1 skeleton. The Claude-driven summarization step is
currently a stub that writes a placeholder summary. Phase 1 next step
is to wire up the actual LLM call (or have the Claude skill invoke this
script with the transcript already in context).
"""

from __future__ import annotations

import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fetch_transcript import extract_video_id, fetch_transcript
from fetch_video import find_episode_for_date, find_today_episode


PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR / "docs" / "output"
TEMPLATE_PATH = PROJECT_DIR / "template.html"
PHT = timezone(timedelta(hours=8))


def resolve_video(args: list[str]) -> dict:
    """Figure out which video to process based on CLI args."""
    if not args:
        episode = find_today_episode()
        if not episode:
            print("No episode found for today.", file=sys.stderr)
            sys.exit(1)
        return episode

    if args[0] == "--date" and len(args) >= 2:
        episode = find_episode_for_date(args[1])
        if not episode:
            print(f"No episode found for {args[1]}.", file=sys.stderr)
            sys.exit(1)
        return episode

    video_id = extract_video_id(args[0])
    return {
        "id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": "(title unknown - resolved from URL)",
        "upload_date": None,
    }


def render_placeholder_html(episode: dict, transcript_chunks: list[dict]) -> str:
    """v1 placeholder render. Real version will let Claude structure the body."""
    template = TEMPLATE_PATH.read_text()
    chunk_count = len(transcript_chunks)
    duration_min = round(transcript_chunks[-1]["start"] / 60) if transcript_chunks else 0

    placeholder_body = f"""
    <section>
      <h2>Skeleton placeholder</h2>
      <p>Transcript fetched: {chunk_count} chunks, ~{duration_min} minutes.</p>
      <p>Next step: wire up the Claude summarization pass that turns these
      chunks into the structured Crypto / Broader Market / Metals / Stocks /
      Quotables / Strong Takes sections.</p>
    </section>
    """

    title = episode.get("title") or "SMTV Summary"
    upload_date = episode.get("upload_date")
    if upload_date and len(upload_date) == 8:
        date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    else:
        date = datetime.now(PHT).strftime("%Y-%m-%d")
    video_url = episode["url"]

    html = template.replace("{{title}}", title)
    html = html.replace("{{date}}", date)
    html = html.replace("{{video_url}}", video_url)
    html = html.replace("<!-- BODY -->", placeholder_body)
    return html


def main():
    args = sys.argv[1:]
    episode = resolve_video(args)
    print(f"Resolved episode: {episode['title']} ({episode['url']})", file=sys.stderr)

    transcript = fetch_transcript(episode["id"])
    print(f"Fetched transcript: {len(transcript)} chunks", file=sys.stderr)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    upload_date = episode.get("upload_date")
    if upload_date and len(upload_date) == 8:
        date_slug = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    else:
        date_slug = datetime.now(PHT).strftime("%Y-%m-%d")

    out_path = OUTPUT_DIR / f"smtv-{date_slug}.html"
    out_path.write_text(render_placeholder_html(episode, transcript))
    print(f"Wrote {out_path}", file=sys.stderr)

    webbrowser.open(out_path.as_uri())


if __name__ == "__main__":
    main()
