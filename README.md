# Swipe-to-Ship Video Workflow

Turn proven "swipe" videos (winning ad formats from any category) into new
videos for our brand using the same underlying creative mechanics. Target
turnaround: same-day, hours not days.

This repo is the working environment. The real output of the early phase is
not the workflow — it's a Claude skill (`skill/SKILL.md`) that codifies what
becomes stable after 5–10 real runs. We build by doing, log friction, and
promote what survives.

See `NOTES.md` for the canonical context (architecture, decisions made,
known gaps, what's out of scope).

## How it's intended to work

```
seed video
   │
   ▼
Stage 1: Deconstruct (Gemini → JSON; Claude → prose)
   │
   ▼
Stage 2: Abstract (Claude → portable formula + non-negotiables + swap vars)
   │
   ▼  HITL: concept approve
Stage 3: Translate (Claude → re-instantiated for our brand) — TBD
   │
   ▼
Concept → images (Higgsfield) → motion clips (Higgsfield)
   │
   ▼  HITL: clips approve
DaVinci Resolve assembly → QA → publish → feedback into seed library
```

Two HITL gates, deliberately placed where rework is cheapest.
Decompose and Abstract are brand-agnostic — Translate is where brand inputs land.

## Repo layout

```
prompts/    Prompts used in the workflow. Currently: decompose.md (Stages 1–2).
scripts/    Tooling. Currently: analyze_video.py (Gemini Stage 1).
runs/       One folder per real execution. Run logs live here.
skill/      Empty until ~Run 5–10. The skill is the *output* of learning.
NOTES.md    Canonical context. Append, don't refactor.
```

## Setup

1. **API key.** `GEMINI_API_KEY` needs to be in the environment.
   - **Desktop Claude Code:** add to `~/.claude/settings.json` under `"env"`.
   - **Cloud-mobile Claude Code:** add via your environment's variables panel
     in claude.ai/code (mobile browser is fine). Caveat: the UI explicitly
     warns that variables aren't encrypted secrets — restrict the key on
     Google's side (quotas, IP scopes) so blast radius is bounded.
   - **Local terminal:** `export GEMINI_API_KEY=...` in your shell.

2. **Python deps.**

   ```sh
   python -m venv .venv && source .venv/bin/activate
   pip install -r scripts/requirements.txt
   ```

   `yt-dlp` is installed alongside `google-genai` so the script can take URLs
   directly (TikTok, YouTube, Reels, X, etc.).

## Running Stage 1 against a video

Local file:

```sh
python scripts/analyze_video.py path/to/seed.mp4 --out runs/01-<label>/analysis.json
```

URL:

```sh
python scripts/analyze_video.py "https://www.tiktok.com/@user/video/123" \
  --out runs/02-<label>/analysis.json
```

When given a URL, the script runs `yt-dlp` first, drops the file as
`source.<ext>` next to your `--out` path (gitignored), then proceeds. For
sites that require auth, pass `--cookies-from-browser chrome` (or `firefox`).

Either way: uploads to the Gemini Files API, runs `gemini-2.5-pro` with a JSON
schema mirroring the 12 sections of `prompts/decompose.md`, writes the
structured analysis to disk. Then run Stage 2 (Abstract) in Claude using that
JSON as input.

### Sandbox limitation (Claude Code on mobile / web)

The Claude Code cloud sandbox's egress IPs are on TikTok's, YouTube's, and
similar platforms' datacenter blocklists — `yt-dlp` will get HTTP 403 / player
extraction errors from inside the sandbox. Two workable paths:

- **Run the script locally** on your laptop where the IP is residential.
- **Rip on your phone** (e.g. snaptik.app or ssstik.io in a mobile browser),
  upload the MP4 to the Gemini app with the prompt from
  `prompts/decompose.md`, and paste the JSON into the run folder yourself.
  This is the documented workaround until cloud-managed sessions get a clean
  secrets-injection path *and* better egress.

## How to start a run

1. Copy `runs/_template.md` to `runs/NN-<label>/run.md`.
2. Drop the seed video into the same folder (gitignored — videos don't get
   committed).
3. Run `analyze_video.py` and write the JSON into the run folder.
4. Use `prompts/decompose.md` in Claude with the JSON as context to produce
   Stage 2 (Abstract) output. Save as `decompose.md` in the run folder.
5. Log every HITL intervention and every handoff break in the run file. These
   are the contracts that will harden over the next several runs.

## What to do if it doesn't work as advertised

It probably won't, on the first few runs. That's the point.

- Gemini's JSON misses sections or hallucinates timestamps → log it as a
  handoff break, hand-fix, keep going. Don't refactor the schema until the
  same break shows up in 2–3 runs.
- A stage feels redundant or missing → log it. Don't restructure the workflow
  mid-run.
- The prompt outputs prose where you wanted structure → log it. Stage 1 has a
  structured pass via the script; the others will get one when there's
  evidence they need it.

The friction log in each run is more valuable than the artefact.
