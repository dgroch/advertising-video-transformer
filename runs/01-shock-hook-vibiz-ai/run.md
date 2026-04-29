# Run 01 — shock-hook-vibiz-ai

Date: 2026-04-29
Seed video: user-supplied local file (not committed; gitignored)
Brand context: N/A — Stages 1–2 are brand-agnostic. Translate (Stage 3) deferred.

## Inputs

- `SOURCE_VIDEO`: ~19s, 9:16, vibiz.ai marketing demo with silent-shock hook
- `TARGET_BRAND`: not yet
- `TARGET_NICHE`: not yet
- `TARGET_AUDIENCE`: not yet
- `HERO_PRODUCT`: not yet
- `BRAND_VOICE`: not yet
- `CONSTRAINTS`: not yet

## Artefacts in this folder

- `analysis.json` — Stage 1 (Decompose) structured output. Generated in
  Gemini mobile app, not via the API script. See HITL section below.
- `abstract.md` — Stage 2 (Abstract) prose: portable formula,
  non-negotiables, swap variables, transferability flags.

## HITL interventions

- **Bypassed the API entirely.** `GEMINI_API_KEY` could not be cleanly
  injected into the cloud-managed mobile sandbox without leaking into chat
  or repo (documented Anthropic gap — no dedicated secrets store yet). User
  ran the Stage 1 prompt manually via Gemini mobile, pasted the JSON back,
  agent saved it as if it had come from `scripts/analyze_video.py`. Script
  was never executed.
- **Stage 2 (Abstract) authored by Claude in-chat**, not via a separate
  prompt run. Used `analysis.json` as structured input. Output saved to
  `abstract.md`.

## Handoff breaks

The contracts that need to harden. One bullet per break.

- **`camera` array under-populated.** Schema asks for per-beat camera notes
  aligned with `beat_sheet`. Gemini returned 2 entries for 7 beats. The
  rebuild can't be shot from this — camera will need to be re-derived shot
  by shot at concept stage. Watch for this on Run 02; if it recurs, either
  tighten the prompt or stop asking Gemini for it and assign that work to
  Claude downstream.
- **`on_screen_text` duplicates `script_verbatim` content** but loses the
  beat markers. Not blocking, but means downstream consumers have to choose
  one source of truth or reconcile.
- **`format.length_seconds: 19` vs final on-screen text at `00:18` with
  duration `00:01`.** Consistent enough but tight. Edge cases like this
  could break a strict EDL importer downstream.

## Friction notes

- **Cloud-managed Claude Code on mobile has no clean secret-injection
  path.** Confirmed via docs research, not assumed. Workaround: round-trip
  through the Gemini mobile app. Costs ~5 min per video and a context
  switch, but the artefact is identical. Acceptable for now; revisit if
  using API becomes blocking (e.g. for batch runs).
- **The decompose prompt was originally one prose-only Stage 1+2 block.**
  Splitting Stage 1 into structured JSON (via Gemini) and Stage 2 into
  prose (via Claude) felt natural — Stage 2 is genuinely synthesis work
  that benefits from prose, while Stage 1 is extraction that wants
  structure. Worth keeping as the default split.
- **Gemini's analysis is good but slightly polished.** It calls the hook
  "hyper-emotive" and uses the magic-trick metaphor — both useful for
  copy-paste into a deck, but the prompt's quality bar says no generic
  adjectives. Half-pass on that. Not blocking.

## Outcome

- Shipped: not yet — Stage 3 (Translate) deferred per project plan.
- Where: n/a
- Performance: n/a
- Would do again: yes — formula extraction is clean, non-negotiables list
  feels like real IP. Next time, run Stage 2 through the same agent on a
  totally unrelated seed and check whether the non-negotiables look
  meaningfully different. If they look samey across very different videos,
  the abstraction step is collapsing detail and needs sharpening.
