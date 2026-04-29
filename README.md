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

1. **API key.** Add `GEMINI_API_KEY` to `~/.claude/settings.json`:

   ```json
   { "env": { "GEMINI_API_KEY": "..." } }
   ```

   This keeps it out of the repo and out of any chat transcript. If you run
   the script outside Claude Code, export it in your shell instead.

2. **Python deps.**

   ```sh
   python -m venv .venv && source .venv/bin/activate
   pip install -r scripts/requirements.txt
   ```

## Running Stage 1 against a video

```sh
python scripts/analyze_video.py path/to/seed.mp4 --out runs/01-<label>/analysis.json
```

Uploads the local file via the Gemini Files API, runs `gemini-2.5-pro` with
a JSON schema mirroring the 12 sections of `prompts/decompose.md`, and writes
the structured analysis to disk. Then run Stage 2 (Abstract) in Claude using
that JSON as input.

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
