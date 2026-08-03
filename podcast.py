#!/usr/bin/env python3
"""
Morning Brief Podcast Builder
------------------------------
Reads today's brief.json (written by news_agent.py, so the news content is only
generated once), turns it into a spoken-word script, synthesizes it into an mp3
via OpenAI TTS, and updates a public RSS feed so it can be subscribed to in any
podcast app.

Required environment variables:
  OPENAI_API_KEY   - same key used by news_agent.py
  PAGES_BASE_URL   - public base URL where PUBLIC_DIR is served (GitHub Pages)
  PUBLIC_DIR       - local directory mirroring the gh-pages branch (default: public)
"""

import glob
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PAGES_BASE_URL = os.environ.get("PAGES_BASE_URL")
PUBLIC_DIR = os.environ.get("PUBLIC_DIR", "public")

RETENTION_DAYS = 30
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "onyx"  # try also: "fable", "echo", "nova" - just swap and re-run to compare
TTS_INSTRUCTIONS = (
    "Deliver this like a professional international news anchor - BBC World Service or "
    "NPR Morning Edition style. Calm, measured pacing with brief natural pauses between "
    "stories. Warm but understated authority, not chipper or robotic. Slight emphasis on "
    "names and numbers."
)


def load_brief(path="brief.json"):
    import json
    with open(path) as f:
        return json.load(f)


def speak_section(intro, items):
    story_lines = " ".join(f"{item['headline']}. {item['detail']}" for item in items)
    return f"{intro} {story_lines}"


def brief_to_script(brief):
    parts = [
        "Good morning. Here's your morning brief.",
        speak_section("Let's start with the world headlines.", brief["global_headlines"]),
        speak_section("Now, over to South Africa.", brief["south_africa"]),
        speak_section("In tech news,", brief["tech"]),
        speak_section("And finally, markets and finance.", brief["finance"]),
        "Before you go, here's something to carry into your day.",
        brief["affirmation"],
        "That's your morning brief. Have a great day.",
    ]
    return "\n\n".join(parts)


def synthesize_speech(text, out_path):
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": TTS_MODEL,
            "voice": TTS_VOICE,
            "input": text,
            "instructions": TTS_INSTRUCTIONS,
            "response_format": "mp3",
        },
        timeout=120,
    )
    response.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(response.content)


def episode_date_from_filename(path):
    name = os.path.basename(path)
    date_str = name.replace(".mp3", "")
    try:
        return date_str, datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None, None


def prune_old_episodes(episodes_dir, retention_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    for path in glob.glob(os.path.join(episodes_dir, "*.mp3")):
        _, episode_date = episode_date_from_filename(path)
        if episode_date and episode_date < cutoff:
            os.remove(path)


def build_feed(episodes_dir, feed_path, base_url):
    items = []
    for path in sorted(glob.glob(os.path.join(episodes_dir, "*.mp3")), reverse=True):
        date_str, episode_date = episode_date_from_filename(path)
        if not episode_date:
            continue
        size = os.path.getsize(path)
        pub_date = episode_date.strftime("%a, %d %b %Y 06:00:00 GMT")
        items.append(f"""
        <item>
          <title>Morning Brief - {episode_date.strftime('%d %B %Y')}</title>
          <pubDate>{pub_date}</pubDate>
          <enclosure url="{base_url}/episodes/{date_str}.mp3" length="{size}" type="audio/mpeg"/>
          <guid isPermaLink="false">{date_str}</guid>
        </item>""")

    feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Your Morning Brief</title>
    <link>{base_url}</link>
    <language>en-us</language>
    <description>A daily spoken news brief: world headlines, South Africa, tech, and markets.</description>
    <itunes:author>Morning Brief</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    {''.join(items)}
  </channel>
</rss>
"""
    with open(feed_path, "w") as f:
        f.write(feed_xml)


def main():
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY is not set", file=sys.stderr)
        sys.exit(1)
    if not PAGES_BASE_URL:
        print("PAGES_BASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    brief = load_brief()
    script_text = brief_to_script(brief)

    episodes_dir = os.path.join(PUBLIC_DIR, "episodes")
    os.makedirs(episodes_dir, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    episode_path = os.path.join(episodes_dir, f"{today}.mp3")

    print("Synthesizing podcast audio...")
    synthesize_speech(script_text, episode_path)

    print("Pruning episodes older than retention window...")
    prune_old_episodes(episodes_dir, RETENTION_DAYS)

    print("Rebuilding feed.xml...")
    build_feed(episodes_dir, os.path.join(PUBLIC_DIR, "feed.xml"), PAGES_BASE_URL)

    print("Done - podcast episode published.")


if __name__ == "__main__":
    main()
