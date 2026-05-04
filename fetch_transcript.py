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
import re
import sys
import warnings

# Silence the harmless LibreSSL warning from urllib3 on macOS system Python.
warnings.filterwarnings("ignore", message=".*OpenSSL.*")

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


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
    """Fetch transcript chunks for a video. Returns list of {start, duration, text}."""
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id)
    return fetched.to_raw_data()


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
