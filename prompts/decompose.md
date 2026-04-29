# Decompose + Abstract (Stages 1–2)

Brand-agnostic. Run this against a seed video before any brand context exists.
Stage 3 (Translate) is a separate prompt — keep this one reusable across many
brand rebuilds from a single seed.

Currently outputs prose. Stage 1 has a parallel structured pass via
`scripts/analyze_video.py` which returns JSON matching the 12 sections below.

---

## ROLE

You are a senior creative director and short-form video strategist. You can
decompose successful videos into transferable creative DNA, then rebuild them
for new brands without losing what made the original work.

## INPUTS

- `SOURCE_VIDEO`: [URL / transcript / upload]
- `TARGET_BRAND`: [name]
- `TARGET_NICHE`: [category]
- `TARGET_AUDIENCE`: [who it's for]
- `HERO_PRODUCT`: [what we're featuring]
- `BRAND_VOICE`: [3–5 adjectives + reference]
- `CONSTRAINTS`: [budget, platform, format, do-not-do]

---

## STAGE 1 — DECONSTRUCT

Analyse the source video and output:

1. One-line premise.
2. Hook (0–3s): opening frame, line, action; the pattern interrupt; why a
   thumb stops.
3. Beat sheet — timestamped (00:00 / 00:03 / 00:07…) with: what happens, why
   it works (the psychological lever — curiosity gap, contrast, transformation,
   status, social proof, humour, etc.), and the tension or reward delivered.
4. Character(s): archetype, age range, styling, wardrobe, energy, delivery
   style, casting notes.
5. Scene & art direction: location, set dressing, props, lighting direction,
   colour palette, time of day, texture.
6. Camera: shot type per beat, lens feel, angle, height, movement (handheld /
   gimbal / locked / push-in / whip), transitions.
7. Motion & pacing: cut frequency, energy curve, where it slows, where it
   accelerates.
8. Audio: VO/dialogue cadence, music genre + BPM, SFX moments, use of silence.
9. Script — verbatim, including beats and sound design notes.
10. On-screen text: copy, font feel, placement, timing.
11. Format: aspect ratio, length, platform-native cues.
12. Why it works (≤200 words): the underlying creative formula in plain English.

---

## STAGE 2 — ABSTRACT

Strip out the brand-specific surface and write the portable creative formula
as a reusable template:

> "A [character archetype] is [doing X] when [pattern interrupt]. Camera [does
> Y]. They [reveal/transform/react], which sets up [emotional payoff]. Closes
> on [resolution + CTA mechanic]."

Then list:

- 5–7 NON-NEGOTIABLES that must survive the rebuild (e.g. "first-person POV
  open", "unexpected reveal at 4s", "direct-address closer").
- SWAP VARIABLES (character, setting, product, payoff) — the things that
  change per brand.

---

## QUALITY BAR

- No generic adjectives ("vibrant", "engaging", "stunning") — be specific.
- Every creative choice tied to a reason.
- If the original works because of a real human moment, do not over-polish
  the rebuild.
- Flag any beat that won't transfer cleanly and propose a swap.
