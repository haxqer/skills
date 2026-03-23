# ARPG Metrics

Use this reference when the primary lens is ARPG and you need combat, loot, and endgame pacing in measurable terms.

## Core Metrics

| Metric | Unit | How to capture | Why it matters |
| --- | --- | --- | --- |
| Representative farming loop duration | `minutes/run` | Time one map, dungeon, or representative farming route from start to reward resolution. | Defines repeatability and session pacing. |
| Average combat pack density | `enemies/engagement` | Sample average enemies per meaningful engagement across a representative route. | Tracks tempo and crowd pressure. |
| Time to first meaningful build spike | `minutes-or-levels` | Record when the build first gains a clearly felt jump in clear speed or survivability. | Measures onboarding excitement and early retention. |
| Meaningful upgrade frequency | `upgrades/hour` | Count drops, crafts, or rerolls that materially improve the current build over a representative hour. | Shows whether loot chase feels alive or dry. |
| Respec or build pivot cost | `currency-plus-minutes` | Record the full cost to pivot into another viable build path. | Controls experimentation and failure recovery. |

## Interpretation Guardrails

- Measure farm routes at comparable gear power.
- Separate clear-speed routing from boss-kill pacing.
- Log deterministic progress and random progress separately.
- Do not judge loot quality by drop count alone; judge upgrade relevance.
