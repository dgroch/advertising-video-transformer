# Swipe-to-Ship Video Workflow — Canonical Context

This file is the single source of truth for what we're building and why. Drop new
context here as decisions stabilise. Don't refactor — append, then promote
stable patterns into `skill/SKILL.md` once they've survived 5–10 runs.

---

## What this is

A workflow that takes proven "swipe" videos (winning ad formats from any
category, sourced via a research step upstream) and rapidly produces new videos
for our brand using the same underlying creative mechanics. Target turnaround
is same-day, hours not days. The pipeline is human + agent, not fully
autonomous.

Deliberate call: **don't over-engineer the workflow in the abstract. Build it
by running 5–10 real executions, logging friction, and encoding what's stable
into a reusable Claude skill.** The skill is the *output* of the learning
phase, not the input.

Moving the work into Claude Code now because we need real tool execution
(Gemini for video analysis, Higgsfield for image and video generation, git
commits per run, eventually DaVinci handoff) rather than described execution.

## Architecture

The skill is the playbook. Tool calls happen around it.

- **Gemini** → video analysis (most capable model for video input)
- **Claude** → decompose, abstract, translate, shot prompts, audio brief,
  on-screen titles, EDL/shot manifest
- **Higgsfield** → images per shot, then motion clips
- **DaVinci Resolve** → final assembly from a templated project + EDL import

The real IP being developed is the **handoff contracts** at each boundary —
what Gemini outputs, what Claude consumes, what Higgsfield needs as input,
what DaVinci imports cleanly. Those contracts will harden over the first 5–10
runs.

## Current workflow (working draft, expected to evolve)

```
Research → seed video + mechanic tag (taxonomy TBD, not pre-built)
   ↓
Decompose (Gemini + Claude) → surface elements + underlying mechanics
   ↓
Abstract → format-agnostic creative formula + non-negotiables + swap variables
   ↓
Translate → re-instantiate for our brand/category
   ↓
Concept (beats / shot list / sound plan / title plan)
   ↓ HITL gate 1 (concept approve)
   ↓
Parallel:
  • Images per shot ← brand asset library (locked chars/locations/product/tokens)
  • Audio selection / brief
  • Title copy
   ↓
Storyboard assembly
   ↓
Motion clips (Higgsfield)
   ↓ HITL gate 2 (clips approve)
   ↓
DaVinci Resolve (templated project, EDL/manifest import)
   ↓
QA → publish → performance feedback into seed library
```

Two HITL gates, deliberately — placed where rework is cheapest. Audio is
planned at concept stage, not treated as a finishing step. Assets parallelize
after gate 1.

## Key decisions already made

- **Don't pre-build the mechanic taxonomy.** Let it emerge from real runs.
- **Decompose and Abstract are brand-agnostic** — can be run before any brand
  context exists. **Translate** is where brand inputs land.
- **Stage 3 (Translate) will be a separate, chainable prompt**, not bolted
  onto the decompose prompt. Keeps the abstract template reusable across many
  brand rebuilds from a single seed.
- **Outputs need to be structured (JSON/YAML alongside prose)** so downstream
  agents can parse cleanly. Shot list should be image-gen-prompt-ready. Audio
  section should be a search brief. Titles should be drop-in copy. Currently
  the prompt outputs prose only — fix this as we go.
- **Repo private for now.** Honest friction logs > performative ones.

## Known gaps to address as we go

Don't fix preemptively. Address when a real run exposes the friction.

- Add structured output schema alongside prose — *partially done at Stage 1
  via `scripts/analyze_video.py` (Gemini returns JSON matching the 12 sections
  of the decompose prompt).*
- Make shot list, audio brief, title copy executable rather than descriptive
- Add platform/objective/KPI to inputs
- Add a transferability flag (low/med/high + reason)

## Out of scope for now

Resist the urge to scaffold these. They emerge from runs.

- Mechanic taxonomy
- `skill/SKILL.md`
- Stage 3 (Translate) prompt
