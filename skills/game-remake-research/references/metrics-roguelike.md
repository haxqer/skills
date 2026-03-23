# Roguelike Metrics

Use this reference when the primary lens is roguelike and you need run structure, RNG governance, and re-entry pacing in measurable terms.

## Core Metrics

| Metric | Unit | How to capture | Why it matters |
| --- | --- | --- | --- |
| Full run duration | `minutes/run` | Time a representative successful run from start to ending or victory screen. | Defines session expectation and pacing envelope. |
| Meaningful choice interval | `minutes/decision` | Measure time between draft, shop, pathing, or loadout decisions that materially change the run. | Shows agency density between fights. |
| Recovery node frequency | `count/run` | Count heal, shop, rest, reroll, or bailout opportunities in a representative run. | Reveals how forgiving the structure is after bad luck or mistakes. |
| Pre-boss anti-brick opportunities | `count-before-first-boss` | Count guaranteed or likely systems that rescue weak starts before the first major gate. | Prevents runs from feeling dead on arrival. |
| Loss-to-retry time | `seconds/retry` | Measure time from failure screen to regained player control in a fresh run. | Defines how fast mastery loops restart. |

## Interpretation Guardrails

- Measure winning runs and failed runs separately.
- Separate weighted-random offers from guaranteed safety valves.
- Track early-run rescue structure before talking about fairness.
- Do not mistake high variance for high replay value.
