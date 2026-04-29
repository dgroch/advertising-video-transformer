"""Run Stage 1 (Deconstruct) of the decompose prompt against a video using Gemini.

Reads a local video file, uploads it via the Files API, asks Gemini to return
JSON matching the 12 sections of `prompts/decompose.md` Stage 1.

Usage:
    python scripts/analyze_video.py path/to/video.mp4 [--out runs/01/analysis.json]

Requires GEMINI_API_KEY in the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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
            "GEMINI_API_KEY not set. Add it to ~/.claude/settings.json under 'env'."
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Path to the local video file.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Where to write the JSON. Defaults to stdout.",
    )
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")

    result = analyze(args.video)
    payload = json.dumps(result, indent=2, ensure_ascii=False)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
