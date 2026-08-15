# Search And Tuning

How to go from "these numbers are wrong" to a specific, minimal, verified parameter change. The
tools rank levers, then search under constraints, then confirm on unseen seeds.

## 1. Rank Levers Before Changing Any

Sensitivity answers which parameter to touch. Without it, tuning is a sequence of guesses whose
side effects nobody predicted.

```bash
python3 sim_search.py sensitivity scenario.json plan.json \
  --metric win_rate.point --metric rounds.mean --metric max_damage_share --workers 8
```

Each tunable is nudged up and down by two grid steps under common random numbers, and the delta on
each tracked metric is recorded. Two columns matter:

- `abs_effect`: the largest absolute movement of the primary metric. This ranks the levers.
- `elasticity`: movement per unit of parameter. This compares levers on different scales.

Read the ranking before writing a proposal. A parameter with near-zero `abs_effect` cannot fix the
problem no matter how far you move it, and moving it anyway is how a tuning pass ships churn.

Sensitivity is local. It describes the response surface near the current values only, and a lever
that is flat at the baseline can be steep two steps away. Re-run it after any large change.

## 2. Write The Objectives Down First

A tuning plan (`assets/templates/tuning-plan-template.json`) has objectives and tunables.

An objective takes `target` with `tolerance`, or `min`, or `max`. Violation is the distance outside
the acceptable band divided by `scale`, so `scale` is what makes different metrics comparable:
set it to the amount of movement in that metric you consider as bad as one unit of movement in the
others. `weight` then expresses genuine priority on top of that.

```json
{ "metric": "win_rate.point", "target": 0.55, "tolerance": 0.03, "scale": 0.03, "weight": 2.0 }
```

Objectives you almost always want alongside the primary band, because they catch the ways a search
will otherwise satisfy the letter of the target:

| Objective | Prevents |
| --- | --- |
| `timeout_rate` max | Hitting the win rate by making fights unresolvable |
| `rounds.p90` max | Hitting the mean length while the tail becomes a slog |
| `max_damage_share` max | Hitting every band with one carry doing everything |
| `concentration.effective_contributors` min | A roster that has become decoration |
| `outcome_entropy` min | A predetermined result that happens to average correctly |

A tunable declares `path`, `min`, `max`, and `step`. The legal range is a design constraint, not a
formality: it encodes what the rest of the game can absorb. The step is the tuning resolution, and
the search can only return grid points, so a step of 250 on a health pool cannot express a 3% edit.

## 3. Run The Search

```bash
python3 sim_search.py search scenario.json plan.json --workers 8 --restarts 4 --out proposal.json
```

The searcher is a multi-start coordinate descent:

- Each axis is probed at several step multiples (8x, 4x, 2x, 1x) in both directions, which steps
  over the flat spots that sampling noise creates in the response surface.
- After an improving pass it tries a Hooke-Jeeves pattern move, extrapolating along the whole pass,
  which follows a diagonal valley that single-axis steps only crawl down.
- It descends from several deterministic Halton starts as well as the baseline, and keeps the best.
  `restarts` in the output shows what every start converged to. Wide disagreement between starts
  means the surface is rugged and the answer is basin-dependent; report that.
- `change_penalty` adds a cost proportional to the mean fractional distance from the baseline, so
  among configurations that satisfy the objectives it prefers the smallest edit.

Every evaluation uses the same seed block, so candidates are compared under common random numbers.
Evaluations are cached, so revisiting a grid point is free.

## 4. Read The Result Honestly

The output contains `satisfied`, `violation`, the per-objective `metrics`, the `proposal` with
absolute and percentage deltas, and a `verification` block re-scored on a fresh seed block at a
higher sample count.

Three outcomes, three responses:

| Outcome | Meaning | Response |
| --- | --- | --- |
| `satisfied: true`, `held_on_fresh_seeds: true` | A real configuration meets the bands | Ship it through the regression gate |
| `satisfied: true`, `held_on_fresh_seeds: false` | Overfitted to the tuning seeds | Raise `eval_battles`, re-search, do not ship |
| `satisfied: false` | No grid point in range meets every objective | Read below |

An unsatisfiable plan is information, not a tool failure. Diagnose it in this order:

1. **Resolution**: is the grid too coarse to land inside the tolerance? Reduce `step`.
2. **Range**: is the best point pinned at a `min` or `max`? Widen it if design allows.
3. **Conflict**: do two objectives pull opposite ways? Check whether sensitivity shows any lever
   that moves them in compatible directions. If none does, the objectives are jointly impossible
   with these levers.
4. **Structure**: if no combination of legal values can satisfy the set, the fix is a design change
   (a new mechanic, a phase transition, a changed role), not a number. Say that explicitly and stop
   searching.

Case 4 is the most valuable result the tool produces, and the easiest to bury. A report that says
"reduced boss health 15% and win rate is now 58.4%, still outside the 52-58% band" is more useful
than one that quietly relaxes the band to make the run look successful.

## 5. Constraints On Any Proposal

- **Smallest coherent change**: fewer parameters moved, smaller moves. Two parameters at 5% is
  usually safer than one at 40%, but four parameters at 20% is churn nobody can review.
- **Name the mechanism**: state why the parameter causes the metric to move. If you cannot, you
  found a correlation on a seed block, not a lever.
- **Predict the side effects** before running the confirmation, then check them. A prediction made
  after seeing the numbers is not a prediction.
- **Respect identity**: a change that fixes the band by erasing what made a unit distinct has moved
  the problem into the design, where it is harder to see.
- **Check the neighbors**: report metrics at the proposal and one grid step either side. A value
  that only works at exactly one point is a cliff, and live data will not land on it.

## 6. Cost Control

The search cost is roughly `restarts * passes * axes * probes * 2 * eval_battles` battles. The
bundled plan (four tunables, five restarts, 2,000 battles per evaluation) runs 295 evaluations and
about 590,000 battles in 103 seconds on eight workers.

`eval_battles` is deliberately below the 10,000-battle reporting floor. Search evaluations are
intermediate comparisons under common random numbers, not quotable results, so 2,000 battles buys
enough resolution to rank candidates at a fifth of the cost. Nothing from the search is reported
until `verify_battles` re-scores the winner at the full floor on a fresh seed block.

Levers when it is too slow: fewer tunables (use sensitivity to drop the flat ones), lower
`eval_battles`, fewer restarts, or a coarser grid for a first pass followed by a fine grid around
the winner.

Lowering `eval_battles` trades precision for speed and raises the overfitting risk, which is
exactly what the verification block exists to catch. Never lower `verify_battles` below 10,000;
that is the number the decision rests on.
