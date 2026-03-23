# ARPG Template

Use this template when the game's identity depends on combat feel, loot chase, buildcraft, density, and repeatable endgame structure.

Read `metrics-arpg.md` when you need measurable baselines for combat tempo, loot chase, and build friction.

## What Makes The Research Different

- Combat timing matters as much as feature lists.
- Loot is a pacing system, not just an item list.
- Endgame must be modeled as a repeatable reward structure, not a bag of content.
- Build failure recovery is part of user retention.

## Focus By Role

### Product Manager

- Define who stays for feel, who stays for loot, and who stays for long-term optimization.
- Capture how the game communicates mastery versus grind.

### Professional Game Designer

- Map core loop, loot loop, build loop, and endgame loop separately.
- Identify must-preserve feelings: clear speed, boss dance, build payoff, loot spikes.

### Balance Designer

- Document damage scaling, survivability scaling, drop ladders, affix pools, crafting funnels, and reset costs.
- Capture deterministic versus random progression surfaces.

### Gameplay Designer

- Count anticipation, active, recovery, cancel windows, and movement commitment.
- Capture density expectations, traversal downtime, elite logic, and boss cadence.

### Art / Animation / Audio

- Record readability rules for effect-heavy combat.
- Capture impact hierarchy: hit pause, camera shake, VFX, SFX, UI numbers.

### Client Architect / Lead Engineer

- Identify hot paths: combat simulation, loot generation, projectile density, pathing, save serialization.
- Distinguish data-driven systems from hand-authored boss logic.

## Must Capture

- Core combat feel benchmarks.
- Loot rarity and crafting funnel.
- Skill-tag and build-synergy structure.
- Density pacing by progression band.
- Endgame repeatability loop and chase goals.

## Additional Deliverables

- Skill-tag and affix matrix.
- Combat pacing benchmark table.
- Loot ladder and crafting funnel.
- Endgame loop map.
- Build failure and recovery scenarios.

## Common Remake Traps

- Reproducing loot colors without reproducing chase quality.
- Making combat visually loud but mechanically mushy.
- Flattening density and turning the game into corridor downtime.
- Leaving endgame under-specified because "we can add content later."
