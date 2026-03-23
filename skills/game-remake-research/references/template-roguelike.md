# Roguelike Template

Use this template when the game's identity depends on self-contained runs, randomness governance, fail-forward structure, and controlled meta progression.

Read `metrics-roguelike.md` when you need measurable baselines for run rhythm, anti-brick structure, and re-entry speed.

## What Makes The Research Different

- A good run has rhythm, not just random events.
- Failure is part of the product, so re-entry matters.
- RNG surfaces must be governed explicitly.
- Meta progression should support mastery, not replace it.

## Focus By Role

### Product Manager

- Define whether the promise is mastery, discovery, chaos, speed, or build creativity.
- Capture how the game balances short-session replays against long-term unlocks.

### Professional Game Designer

- Map the run structure: start, ramp, recovery, spike, climax, post-run.
- Identify anti-brick systems and how the run recovers from weak starts.

### Balance Designer

- Track reward weighting, encounter escalation, permanent unlock caps, and economy carryover.
- Capture what is deterministic, what is weighted random, and what is player-directed.

### Gameplay Designer

- Document per-room or per-floor cadence, branch structure, and decision density.
- Capture how player verbs change within a run versus across runs.

### Art / Animation / Audio

- Identify how the game differentiates danger, reward rarity, and build state under repeated sessions.

### Client Architect / Lead Engineer

- Document seed surfaces, content pool composition, save boundaries, and run-state serialization.
- Identify tools required for balancing weighted randomness and large content pools.

## Must Capture

- Run rhythm and biome or floor cadence.
- RNG governance and anti-brick systems.
- Fail-forward structure and re-entry friction.
- Meta progression caps and carryover boundaries.
- Build pivot and recovery opportunities.

## Additional Deliverables

- Run structure timeline.
- RNG surface inventory.
- Reward-draft matrix.
- Meta progression cap table.
- Failure and recovery state map.

## Common Remake Traps

- Equating more randomness with more replayability.
- Letting meta unlocks overpower run-level decisions.
- Removing recovery nodes and making bad rolls unrecoverable.
- Treating rooms as content units without modeling run rhythm.
