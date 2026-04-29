"""Run Stage 1 (Deconstruct) of the decompose prompt against a video using Gemini.

Accepts either a local video file path or a URL (TikTok, YouTube, Instagram,
Reels, X, etc. — anything yt-dlp supports). Uploads the video via the Gemini
Files API and asks Gemini to return JSON matching the 12 sections of
`prompts/decompose.md` Stage 1.

Usage:
    python scripts/analyze_video.py <path-or-url> [--out runs/NN/analysis.json]
    python scripts/analyze_video.py <url> --cookies-from-browser chrome

Requires GEMINI_API_KEY in the environment. Requires yt-dlp on PATH for URLs.

Note: from inside the Claude Code cloud sandbox, yt-dlp will fail against
TikTok / YouTube / similar — their datacenter-IP block hits us. Run this on a
local machine for URL ripping; the sandbox is fine for path-based runs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-2.5-pro"

PROMPT = """You are a senior creative director and short-form video strategist analysing a video.

Decompose it into the schema provided. Be specific — no generic adjectives like
"vibrant", "engaging", or "stunning". Every creative choice must be tied to a
reason. If the video works because of a real human moment, name it precisely.

Use timestamps in mm:ss format. Quote dialogue verbatim where possible.
"""

# Mirrors the 12 Stage 1 sections in prompts/decompose.md.
SCHEMA = {
    "type": "object",
    "properties": {
        "premise": {
            "type": "string",
            "description": "One-line premise of the video.",
        },
        "hook": {
            "type": "object",
            "properties": {
                "opening_frame": {"type": "string"},
                "opening_line": {"type": "string"},
                "opening_action": {"type": "string"},
                "pattern_interrupt": {"type": "string"},
                "why_thumb_stops": {"type": "string"},
            },
            "required": [
                "opening_frame",
                "opening_action",
                "pattern_interrupt",
                "why_thumb_stops",
            ],
        },
        "beat_sheet": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "description": "mm:ss"},
                    "what_happens": {"type": "string"},
                    "why_it_works": {"type": "string"},
                    "psychological_lever": {
                        "type": "string",
                        "description": "e.g. curiosity gap, contrast, transformation, status, social proof, humour",
                    },
                    "tension_or_reward": {"type": "string"},
                },
                "required": [
                    "timestamp",
                    "what_happens",
                    "why_it_works",
                    "psychological_lever",
                ],
            },
        },
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "archetype": {"type": "string"},
                    "age_range": {"type": "string"},
                    "styling": {"type": "string"},
                    "wardrobe": {"type": "string"},
                    "energy": {"type": "string"},
                    "delivery_style": {"type": "string"},
                    "casting_notes": {"type": "string"},
                },
                "required": ["archetype", "energy"],
            },
        },
        "scene_art_direction": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "set_dressing": {"type": "string"},
                "props": {"type": "string"},
                "lighting_direction": {"type": "string"},
                "colour_palette": {"type": "string"},
                "time_of_day": {"type": "string"},
                "texture": {"type": "string"},
            },
            "required": ["location", "lighting_direction", "colour_palette"],
        },
        "camera": {
            "type": "array",
            "description": "Per-beat camera notes. Align timestamps with beat_sheet where possible.",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string"},
                    "shot_type": {"type": "string"},
                    "lens_feel": {"type": "string"},
                    "angle": {"type": "string"},
                    "height": {"type": "string"},
                    "movement": {
                        "type": "string",
                        "description": "handheld / gimbal / locked / push-in / whip / etc.",
                    },
                    "transition_in": {"type": "string"},
                },
                "required": ["timestamp", "shot_type", "movement"],
            },
        },
        "motion_pacing": {
            "type": "object",
            "properties": {
                "cut_frequency": {"type": "string"},
                "energy_curve": {"type": "string"},
                "where_it_slows": {"type": "string"},
                "where_it_accelerates": {"type": "string"},
            },
            "required": ["cut_frequency", "energy_curve"],
        },
        "audio": {
            "type": "object",
            "properties": {
                "vo_or_dialogue_cadence": {"type": "string"},
                "music_genre": {"type": "string"},
                "music_bpm": {"type": "string"},
                "sfx_moments": {"type": "string"},
                "use_of_silence": {"type": "string"},
            },
            "required": ["vo_or_dialogue_cadence"],
        },
        "script_verbatim": {
            "type": "string",
            "description": "Verbatim script including beat markers and sound design notes.",
        },
        "on_screen_text": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string"},
                    "copy": {"type": "string"},
                    "font_feel": {"type": "string"},
                    "placement": {"type": "string"},
                    "duration": {"type": "string"},
                },
                "required": ["timestamp", "copy"],
            },
        },
        "format": {
            "type": "object",
            "properties": {
                "aspect_ratio": {"type": "string"},
                "length_seconds": {"type": "number"},
                "platform_native_cues": {"type": "string"},
            },
            "required": ["aspect_ratio", "length_seconds"],
        },
        "why_it_works": {
            "type": "string",
            "description": "<=200 words: the underlying creative formula in plain English.",
        },
    },
    "required": [
        "premise",
        "hook",
        "beat_sheet",
        "characters",
        "scene_art_direction",
        "camera",
        "motion_pacing",
        "audio",
        "script_verbatim",
        "format",
        "why_it_works",
    ],
}


def is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))


def rip_url(url: str, dest_dir: Path, cookies_from_browser: str | None) -> Path:
    """Download a video URL with yt-dlp into dest_dir. Returns the local path."""
    if shutil.which("yt-dlp") is None:
        raise SystemExit("yt-dlp not on PATH. `pip install yt-dlp`.")

    dest_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(dest_dir / "source.%(ext)s")
    cmd = ["yt-dlp", "--no-warnings", "-o", out_template, url]
    if cookies_from_browser:
        cmd[1:1] = ["--cookies-from-browser", cookies_from_browser]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"yt-dlp failed (exit {result.returncode}):\n{result.stderr.strip()}\n\n"
            "If you're inside the Claude Code sandbox, this is expected — "
            "egress IPs are blocked by major platforms. Run on a local machine."
        )

    files = sorted(dest_dir.glob("source.*"))
    if not files:
        raise SystemExit("yt-dlp returned 0 but produced no file.")
    return files[0]


def upload_and_wait(client: genai.Client, video_path: Path) -> types.File:
    file = client.files.upload(file=str(video_path))
    while file.state.name == "PROCESSING":
        time.sleep(3)
        file = client.files.get(name=file.name)
    if file.state.name != "ACTIVE":
        raise RuntimeError(f"File processing failed: state={file.state.name}")
    return file


def analyze(video_path: Path) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "GEMINI_API_KEY not set. On cloud-mobile Claude Code, set it in "
            "your environment's variables panel; on desktop, use "
            "~/.claude/settings.json under 'env'."
        )

    client = genai.Client(api_key=api_key)
    video_file = upload_and_wait(client, video_path)

    response = client.models.generate_content(
        model=MODEL,
        contents=[video_file, PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )

    return json.loads(response.text)


def resolve_source(source: str, out: Path | None, cookies_from_browser: str | None) -> Path:
    """Return a local path for the video. Rips if `source` is a URL."""
    if not is_url(source):
        path = Path(source)
        if not path.exists():
            raise SystemExit(f"Video not found: {path}")
        return path

    # URL: rip into the run folder if --out is given, else a tempdir.
    dest_dir = out.parent if out else Path(tempfile.mkdtemp(prefix="ytdlp_"))
    path = rip_url(source, dest_dir, cookies_from_browser)
    print(f"Ripped to {path}", file=sys.stderr)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        help="Local video file path OR a URL (TikTok, YouTube, etc.).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Where to write the JSON. URL rips land alongside it. Defaults to stdout.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        default=None,
        help="Pass through to yt-dlp (e.g. 'chrome', 'firefox') for sites that need auth.",
    )
    args = parser.parse_args()

    video_path = resolve_source(args.source, args.out, args.cookies_from_browser)
    result = analyze(video_path)
    payload = json.dumps(result, indent=2, ensure_ascii=False)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
