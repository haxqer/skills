# Capture Methods

Use this reference when extracting timings, formulas, UI flows, and production-relevant detail from footage or documents.

## Contents

- `Timing Capture`
- `Economy Sampling`
- `Progression Band Capture`
- `UI Flow Capture`
- `Audio Capture`
- `Copy And Narrative Capture`

## Timing Capture

For attacks, skills, dodges, and boss telegraphs:

1. pick the cleanest clip with visible animation start and hit event
2. note playback frame rate if known
3. count:
   - anticipation start
   - active frame start
   - active frame end
   - recovery end
4. record whether movement, buffering, or canceling interrupts any phase
5. repeat on at least one second clip if exact timing matters

Capture in a table with:

- clip reference
- timestamp range
- action name
- anticipation frames
- active frames
- recovery frames
- cancel notes
- confidence

## Economy Sampling

For drops, rewards, upgrade costs, and failure penalties:

1. lock the content tier and player context
2. sample multiple observations instead of one anecdote
3. separate guaranteed rewards from probabilistic rewards
4. record sinks, not just faucets
5. note hidden context such as event bonuses, premium multipliers, or difficulty modifiers

When exact rates are unavailable, estimate:

- lower bound
- representative observed band
- upper bound

Then mark the value `Inferred`.

## Progression Band Capture

For level bands, gear tiers, or chapter arcs:

- identify gate conditions
- record the player-facing goal
- record the dominant reward loop
- note what new systems unlock
- note what old loops become obsolete

This is more useful than a flat feature list because it preserves pacing.

## UI Flow Capture

For menus, upgrade flows, inventory, and onboarding:

1. capture entry point
2. count steps to completion
3. note blocking prompts and confirmation states
4. record visible information density
5. record failure, cancel, and back-navigation behavior

Useful outputs:

- screen flow map
- click path count
- state diagram

## Audio Capture

For music and feedback audio:

- identify loop, stinger, transition, and ambient layers
- log what gameplay events trigger audio cues
- separate gameplay-critical SFX from flavor SFX
- note mix dominance during combat, menus, victory, and failure

When exact implementation is unknown, describe observable behavior:

- ducking
- layering
- transition triggers
- cue priority

## Copy And Narrative Capture

For terminology, quest text, and story beats:

- log exact recurring terms
- separate system words from fiction words
- capture tone at onboarding, combat, reward, and failure moments
- record whether lore is mandatory, optional, or ambient

Avoid paraphrasing away the tone if the exact wording matters to the remake.
