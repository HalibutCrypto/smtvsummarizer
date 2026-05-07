"""
Fetch a YouTube video transcript with timestamps.

Usage:
    python fetch_transcript.py <video_url_or_id>

Examples:
    python fetch_transcript.py xOSeC6lanRU
    python fetch_transcript.py https://www.youtube.com/live/xOSeC6lanRU
    python fetch_transcript.py "https://www.youtube.com/watch?v=xOSeC6lanRU"

Outputs JSON to stdout. Each chunk has: start (seconds), duration, text.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import warnings
from http.cookiejar import MozillaCookieJar

# Silence the harmless LibreSSL warning from urllib3 on macOS system Python.
warnings.filterwarnings("ignore", message=".*OpenSSL.*")
warnings.filterwarnings("ignore", message=".*verify.*")

# The Claude Code cloud env runs traffic through a security proxy that does
# SSL inspection with a self-signed cert. Disable cert verification so requests
# (used by youtube-transcript-api) works in cloud. No-op locally.
_orig_create_default_context = ssl.create_default_context
def _no_verify_context(*a, **kw):
    ctx = _orig_create_default_context(*a, **kw)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _no_verify_context
ssl._create_default_https_context = ssl._create_unverified_context

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


# Optional path to a Netscape-format cookies.txt for YouTube. When set,
# requests / yt-dlp authenticate as the logged-in user, which evades bot
# detection on cloud IPs.
COOKIES_FILE = os.environ.get("YT_COOKIES_FILE")


def _build_session() -> requests.Session:
    """Build a requests.Session with cookies attached if available."""
    session = requests.Session()
    session.verify = False
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        jar = MozillaCookieJar(COOKIES_FILE)
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
            session.cookies = jar
        except Exception as e:
            print(f"[fetch_transcript] failed to load cookies: {e}", file=sys.stderr)
    return session


def extract_video_id(url_or_id: str) -> str:
    """Pull a YouTube video ID out of a URL, or return the input if it already is one."""
    if "/" not in url_or_id and "?" not in url_or_id and len(url_or_id) == 11:
        return url_or_id

    patterns = [
        r"youtube\.com/live/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from: {url_or_id!r}")


def fetch_transcript(video_id: str) -> list[dict]:
    """Fetch transcript chunks for a video. Returns list of {start, duration, text}.

    Tries youtube-transcript-api first (fastest). Falls back to yt-dlp's caption
    URL extraction when the API is IP-blocked (common for cloud IPs).
    """
    session = _build_session()
    try:
        api = YouTubeTranscriptApi(http_client=session)
        fetched = api.fetch(video_id)
        return fetched.to_raw_data()
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        # Real content errors. Don't fall back; let main() report.
        raise
    except Exception as e:
        short_err = str(e).split("\n")[0][:100]
        print(
            f"[fetch_transcript] youtube-transcript-api failed ({short_err}); "
            f"trying yt-dlp fallback",
            file=sys.stderr,
        )
        return _fetch_via_ytdlp(video_id)


def _fetch_via_ytdlp(video_id: str) -> list[dict]:
    """Fallback: extract caption URL via yt-dlp, fetch JSON3 directly."""
    import yt_dlp

    opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
    }
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        # Authenticated requests still need to avoid the "android" client,
        # which currently returns bot-detection auth errors on cloud IPs even
        # with cookies attached and aborts the multi-client request. The "tv"
        # client is the one that actually returns populated automatic_captions
        # in this env; mweb/web come back with empty automatic_captions.
        opts["cookiefile"] = COOKIES_FILE
        opts["extractor_args"] = {"youtube": {"player_client": ["tv", "mweb", "web"]}}
    else:
        # Unauthenticated cloud IPs get bot-detected on the default web client;
        # android/mweb evade detection but trade off caption-track availability.
        opts["extractor_args"] = {"youtube": {"player_client": ["android", "mweb", "web"]}}
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        # process=False avoids format resolution which fails on finished livestreams
        # under cookie-auth in our cloud env. We only need the captions metadata.
        info = ydl.extract_info(url, download=False, process=False)

    json3_session = _build_session()
    for source_name, source in [("subtitles", info.get("subtitles", {})),
                                 ("automatic_captions", info.get("automatic_captions", {}))]:
        for lang_code in ("en", "en-US", "en-GB", "a.en"):
            tracks = source.get(lang_code) or []
            json3 = next((t for t in tracks if t.get("ext") == "json3"), None)
            if json3 and json3.get("url"):
                print(f"[fetch_transcript] using {source_name}/{lang_code}", file=sys.stderr)
                resp = json3_session.get(json3["url"], timeout=30)
                resp.raise_for_status()
                return _parse_json3(resp.json())

    print(
        f"No JSON3 caption track found for {video_id} via yt-dlp fallback. "
        f"Auto-captions usually appear 1-3 hours after a livestream ends.",
        file=sys.stderr,
    )
    sys.exit(4)


def _parse_json3(data: dict) -> list[dict]:
    """Parse YouTube JSON3 caption format into {start, duration, text} chunks."""
    chunks: list[dict] = []
    for event in data.get("events", []):
        start_ms = event.get("tStartMs")
        if start_ms is None:
            continue
        duration_ms = event.get("dDurationMs", 0) or 0
        segs = event.get("segs", [])
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if not text:
            continue
        chunks.append({
            "text": text,
            "start": start_ms / 1000.0,
            "duration": duration_ms / 1000.0,
        })
    return chunks


def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_transcript.py <video_url_or_id>", file=sys.stderr)
        sys.exit(1)

    try:
        video_id = extract_video_id(sys.argv[1])
        transcript = fetch_transcript(video_id)
    except VideoUnavailable:
        print(f"Video unavailable: {sys.argv[1]}", file=sys.stderr)
        sys.exit(2)
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.", file=sys.stderr)
        sys.exit(3)
    except NoTranscriptFound:
        print(
            "No transcript available yet. YouTube usually generates auto-captions "
            "1-3 hours after a livestream ends. Try again later.",
            file=sys.stderr,
        )
        sys.exit(4)

    print(json.dumps({"video_id": video_id, "chunks": transcript}, indent=2))


if __name__ == "__main__":
    main()
