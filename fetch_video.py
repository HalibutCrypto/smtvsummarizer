"""
Find a Morning Show episode on the @StockMarketMedia channel.

The channel airs multiple show types (Trade Live With Me, Options Strategy
Deep Dive, etc). The Morning Show airs daily on US weekdays at ~8:30 PM PHT
(= 8:30 AM EDT, US pre-market). Episode titles vary heavily day to day:
sometimes literally "The Morning Show", sometimes a hot-take headline like
"Today Is Big Tech's Super Bowl" with no show name in the title at all.

Strategy: match by stream start time (release_timestamp from yt-dlp's full
metadata), not by title. Window: ±3 hours of 8:30 PM PHT on target date.
If multiple streams fall in the window, prefer one with "Morning Show" in
the title.

Usage:
    python fetch_video.py                  # find today's episode (PHT)
    python fetch_video.py 2026-05-04       # find episode by date

Outputs JSON: id, url, title, upload_date, release_timestamp.
"""

from __future__ import annotations

import json
import logging
import os
import ssl
import sys
import warnings
from datetime import datetime, timedelta, timezone
from typing import Optional

warnings.filterwarnings("ignore", message=".*OpenSSL.*")
warnings.filterwarnings("ignore", message=".*Python version 3.9.*")
warnings.filterwarnings("ignore", message=".*verify.*")
logging.getLogger("yt_dlp").setLevel(logging.ERROR)

# The Claude Code cloud env runs traffic through a security proxy that does
# SSL inspection with a self-signed cert, breaking default cert validation.
# Disable cert verification so yt-dlp + urllib work in cloud. No-op locally.
_orig_create_default_context = ssl.create_default_context
def _no_verify_context(*a, **kw):
    ctx = _orig_create_default_context(*a, **kw)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _no_verify_context
ssl._create_default_https_context = ssl._create_unverified_context

import yt_dlp


CHANNEL_STREAMS_URL = "https://www.youtube.com/@StockMarketMedia/streams"
PHT = timezone(timedelta(hours=8))
SHOW_HOUR_PHT = 20         # 8 PM
SHOW_MINUTE_PHT = 30       # 8:30 PM
TIME_WINDOW_HOURS = 1.5    # tolerate ±90 min slip vs the 8:30 PM PHT slot
DEFAULT_SEARCH_DEPTH = 30  # @StockMarketMedia posts many show types; need enough depth to find Morning Show


def _list_recent_stream_ids(limit: int = DEFAULT_SEARCH_DEPTH) -> list[dict]:
    """Quickly list IDs and titles of recent streams (flat mode, no dates)."""
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "playlistend": limit,
        "nocheckcertificate": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(CHANNEL_STREAMS_URL, download=False)
    return [
        {
            "id": e["id"],
            "title": e.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={e['id']}",
        }
        for e in info.get("entries", []) or []
    ]


def _fetch_full_metadata(video_id: str) -> dict:
    """Fetch full metadata for one video. ~2-5 seconds per call."""
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "nocheckcertificate": True}
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "id": info["id"],
        "title": info.get("title", ""),
        "url": url,
        "upload_date": info.get("upload_date"),
        "release_timestamp": info.get("release_timestamp"),
    }


def find_episode_for_date(
    target_date_str: str,
    search_depth: int = DEFAULT_SEARCH_DEPTH,
) -> Optional[dict]:
    """
    Find the Morning Show episode that aired on target_date (YYYY-MM-DD PHT).
    Pulls metadata for the most recent `search_depth` streams, matches by
    stream start time within ±TIME_WINDOW_HOURS of 8:30 PM PHT on the target date.
    Returns immediately on the first "Morning Show" title match in the window.
    Falls back to the closest time match if no title-tagged Morning Show is found.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=PHT)
    target_dt = target_date.replace(hour=SHOW_HOUR_PHT, minute=SHOW_MINUTE_PHT)
    target_ts = target_dt.timestamp()
    target_upload_date = target_date_str.replace("-", "")  # "2026-05-04" -> "20260504"
    window_secs = TIME_WINDOW_HOURS * 3600

    candidates = _list_recent_stream_ids(limit=search_depth)
    print(f"[fetch_video] Scanning {len(candidates)} recent streams.", file=sys.stderr)

    fallback: Optional[dict] = None
    fallback_delta: Optional[float] = None
    for c in candidates:
        try:
            full = _fetch_full_metadata(c["id"])
        except Exception as e:
            short_err = str(e).split("\n")[0][:80]
            print(f"[fetch_video]   skip {c['id']} ({c['title'][:30]}): {short_err}", file=sys.stderr)
            continue

        rt = full.get("release_timestamp")
        upload_date = full.get("upload_date")
        title_match = "morning show" in full["title"].lower()

        match_via_timestamp = False
        match_via_upload_date = False
        delta_s: Optional[float] = None

        if rt is not None:
            delta_s = rt - target_ts
            if abs(delta_s) <= window_secs:
                match_via_timestamp = True
        elif upload_date == target_upload_date:
            # YouTube sometimes returns release_timestamp=None on cloud IPs.
            # Fall back to upload_date matching (date precision only).
            match_via_upload_date = True

        if not (match_via_timestamp or match_via_upload_date):
            continue

        if match_via_timestamp:
            delta_h = (delta_s or 0) / 3600
            marker = "Morning Show" if title_match else "time-only"
            print(
                f"[fetch_video]   in window: {full['title'][:55]} "
                f"(delta {delta_h:+.2f}h, {marker})",
                file=sys.stderr,
            )
        else:
            marker = "Morning Show (date-only)" if title_match else "date-only"
            print(
                f"[fetch_video]   date match: {full['title'][:55]} "
                f"(upload {upload_date}, {marker})",
                file=sys.stderr,
            )

        if title_match:
            return full

        if fallback is None:
            fallback = full
            fallback_delta = abs(delta_s) if delta_s is not None else float("inf")
        elif delta_s is not None and abs(delta_s) < (fallback_delta or float("inf")):
            fallback = full
            fallback_delta = abs(delta_s)

    return fallback


def find_today_episode() -> Optional[dict]:
    """Find today's Morning Show in PHT."""
    today_pht = datetime.now(PHT).strftime("%Y-%m-%d")
    return find_episode_for_date(today_pht)


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
        episode = find_episode_for_date(target)
    else:
        target = "today"
        episode = find_today_episode()

    if episode is None:
        print(f"No Morning Show episode found for {target}.", file=sys.stderr)
        print(
            f"(Looked for streams that started within ±{TIME_WINDOW_HOURS}h "
            f"of 8:30 PM PHT on {target}.)",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(episode, indent=2))


if __name__ == "__main__":
    main()
