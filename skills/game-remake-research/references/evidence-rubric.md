# Evidence Rubric

Use this reference when facts are disputed, dated, region-specific, or derived from opaque systems.

## Confidence Ladder

- `Confirmed`
  Use only when at least one primary source or repeated direct observation supports the claim.
- `Inferred`
  Use when behavior is strongly implied by observation, datamine, or multiple secondary sources, but the internal rule is not directly documented.
- `Open`
  Use when the fact is plausible but under-evidenced, contradictory, or version-sensitive.

Do not upgrade a claim from `Inferred` to `Confirmed` just because many people repeat it.

## Minimum Evidence By Claim Type

### Product Positioning And Feature Availability

- Prefer official site, store page, manual, launch material, or patch notes.
- For live-service games, include exact dates and region scope.

### Gameplay Rules And Timing

- Prefer direct footage from multiple clips or build versions.
- For frame-sensitive claims, sample more than one clip where possible.
- If compression or frame interpolation makes exact counts unreliable, say so.

### Balance Values And Economy Rates

- Prefer official patch notes, in-game UI captures, or reputable spreadsheets/datamines.
- If only player footage exists, capture the observation context:
  - player level or gear
  - content tier
  - platform or region
  - time window

### Narrative, Copy, And Terminology

- Prefer official localization, UI captures, quest logs, manuals, and trailers.
- Track region-specific naming drift explicitly.

### Architecture And Technical Inference

- Treat client structure, tick model, data ownership, and hidden formulas as inferential unless directly documented.
- Explain the external behavior that drove the inference.

## Region, Platform, And Time Pitfalls

- `Region drift`
  JP, KR, Global, CN, console, mobile, and PC versions can diverge materially.
- `Historical drift`
  Pre-expansion, rebooted, remastered, and post-live-service eras may contradict one another.
- `Platform drift`
  Ported games often alter UI density, encounter pacing, and control grammar.

Always stamp:

- region
- platform
- date or patch window
- whether the observation is historical or current

## Recommended Evidence Mix

For a full remake pack, aim for:

- at least 2 official sources
- at least 3 gameplay observations across different progression stages
- at least 1 source for menus/UI
- at least 1 source for economy or upgrade loops
- at least 1 source for bosses or failure-heavy gameplay

Increase the sample when the game is live-service or highly patched.

## Anti-Patterns

- Building the whole pack from one creator video.
- Treating wiki statements as primary evidence.
- Mixing regions or eras without labeling them.
- Writing remake decisions as if they were original-game facts.
- Inventing exact formulas when only behavior bands are observable.

## When Evidence Is Thin

If evidence is thin but the user still wants a usable spec:

1. label the point `Open` or `Inferred`
2. provide the likely model
3. explain the assumption
4. describe the cheapest validation task

That is better than fake certainty.
