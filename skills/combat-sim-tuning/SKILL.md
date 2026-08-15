---
name: combat-sim-tuning
description: "Validate and rebalance existing game numbers by simulation instead of intuition. Use for 数值仿真, 蒙特卡洛, 跑数, 平衡验证, 自动调参, 胜率模拟, 战斗模拟, 数值回归, combat simulation, Monte Carlo balance, win rate simulation, TTK and battle length distributions, per-character damage share, roster concentration and dead weight, dominated builds, parameter sensitivity, constrained parameter search, seed hygiene and overfitting checks, convergence and confidence intervals, and balance regression gates. Turn a config, stat table, or candidate patch into a seeded simulation harness, at least ten thousand battles per reported result, distribution-level metrics with confidence intervals, a ranked sensitivity table, a minimal verified parameter proposal, and a baseline plus acceptance thresholds that later changes are gated against. Use game-balance-design instead when the task is to design the system, formulas, economy, or experience targets in the first place; hand its output here to be measured, tuned, and regression-gated."
---

# Combat Sim Tuning

Act as the numerical designer who refuses to ship a number that has not been measured. Build an
executable model, run it at least ten thousand times, report distributions with intervals, propose
the smallest change that moves the named mechanism, and prove it holds on seeds the tuning never saw.

## Boundary With game-balance-design

`game-balance-design` owns design: experience targets, system architecture, formula selection,
economy loops, progression curves, and rollout strategy. This skill owns evidence: turning an
existing or candidate configuration into simulated data, statistical conclusions, tuning proposals,
and regression gates.

Route by what the user is asking for. "Design a combat system for my roguelike" is
`game-balance-design`. "Is this boss tuned right", "why does one character do all the damage",
"find values that hit a 55% clear rate", "did this patch break anything" is this skill. When a
request needs both, design first, then hand the parameter set here to be measured. When simulation
proves no legal parameter set can satisfy the targets, hand it back: that is a design problem.

## Non-Negotiable Rules

- Never invent input data. Every value is `Observed`, `Assumed`, `Derived`, or `Recommended`, and
  every consequential assumption carries a range and a validation method.
- Never quote a number from fewer than 10,000 battles. Below that floor, runs are intermediate
  only: search evaluations and scenario smoke checks, always followed by a full-floor verification.
- Never report a mean alone. Sample size, confidence interval, and seed base accompany every
  number; p10/p50/p90 accompany every duration.
- Never report a point estimate from a run that did not converge. Report `NOT CONVERGED` and either
  raise the sample cap or widen the band.
- Never quote a result from the seed block it was tuned on. Search, verify, and accept on three
  disjoint seed blocks.
- Never claim the simulation measured player behavior. It measured the policy you programmed.
  Declare the policy, the cohort, and the mechanics the model omits.
- Never present a proxy as the thing. `outcome_entropy` and `effective_contributors` are proxies
  for playability, not measurements of fun.
- Prefer the smallest coherent change, name the causal mechanism, predict side effects before
  confirming them, and check the neighboring grid points.
- Report failures to reach the target as prominently as successes.

## Classify The Assignment

1. **Audit**: measure an existing configuration and find what is wrong.
2. **Diagnose**: attribute a known symptom to a causal parameter or a structural cause.
3. **Tune**: search for values that satisfy declared objectives, then verify them.
4. **Gate**: check a candidate against a baseline and acceptance thresholds.

Audit before tuning. A tuning run against undiagnosed symptoms optimizes the wrong lever.

## Route To The Right References

Always read [references/modeling-and-resolution.md](references/modeling-and-resolution.md) before
building or editing a model, and
[references/sampling-and-inference.md](references/sampling-and-inference.md) before quoting any
number.

| Need | Read |
| --- | --- |
| Scenario schema, resolution order, mitigation curves, determinism, calibration, engine limits | [references/modeling-and-resolution.md](references/modeling-and-resolution.md) |
| Sample size, Wilson intervals, convergence, common random numbers, seed hygiene, multiple comparisons | [references/sampling-and-inference.md](references/sampling-and-inference.md) |
| What every metric means and the failure it exposes | [references/metrics-catalog.md](references/metrics-catalog.md) |
| Modeling player skill, cohort ladders, policy sensitivity, what policies cannot represent | [references/policies-and-agents.md](references/policies-and-agents.md) |
| Sensitivity ranking, objectives, constrained search, reading an unsatisfiable result | [references/search-and-tuning.md](references/search-and-tuning.md) |
| Baselines, acceptance thresholds, the gate, report contract, honest language | [references/regression-and-reporting.md](references/regression-and-reporting.md) |
| A full pass with real numbers from the bundled scenario | [references/worked-example.md](references/worked-example.md) |

## End-To-End Workflow

**1. Lock the question and the band.** State the decision this run informs, the focus team, the
cohort and policy, the primary metric, and its acceptable band. "Make it harder" is not a question.
"Move the core cohort's first-clear rate from 68% to 55% +/- 3% without raising median length above
21 rounds" is.

**2. Build and calibrate the model.** Confirm calculation order, rounding, caps, stacking, action
economy, and random source with the implementation owner. Encode the scenario as JSON. Calibrate in
five steps: hand arithmetic, deterministic trace, single mechanic, whole encounter, distribution.
Report which steps you ran.

**3. Audit the baseline.** Run at least 10,000 battles, more when the band is tight or the metric
is a rare event. Read the distribution, the tails, the contribution table, and roster concentration
before forming a hypothesis.

**4. Rank the levers.** Run sensitivity under common random numbers. A parameter with near-zero
effect cannot fix the problem regardless of how far it moves.

**5. Test candidates paired.** Compare variants on shared seeds. Read `outcome_flips` for direction,
not just the mean delta.

**6. Search under constraints.** Declare objectives that include the guardrails, not only the
primary band. Use multiple restarts, and read the restart table: wide disagreement means a rugged
surface and a basin-dependent answer.

**7. Verify on unseen seeds.** Re-score the proposal on a fresh seed block at no fewer than 10,000
battles. A proposal that only clears its band on the tuning block has not cleared it.

**8. Baseline and gate.** Record the converged report, thresholds, run parameters, and tool commit.
Run the gate on every later change, across the whole scenario matrix, on a seed block reserved for
acceptance.

## Use The Bundled Resources

Scripts are Python 3, standard library only. Each has `--help`. Run
`python3 -m unittest discover -p "test_*.py"` from `scripts/` after any change.

| Script | Purpose |
| --- | --- |
| `scripts/sim_engine.py` | Deterministic combat engine; CLI runs one seeded battle with `--trace` |
| `scripts/sim_runner.py` | Batches, parallelism, sequential convergence, `--set` and `--scale` overrides |
| `scripts/sim_report.py` | Aggregation, intervals, concentration metrics, paired comparison |
| `scripts/sim_search.py` | Sensitivity ranking and multi-start constrained search with verification |
| `scripts/sim_diff.py` | Regression gate; exit 0 pass, 1 error, 2 threshold violated |

Copy and extend `assets/templates/`: `scenario-template.json` (runnable reference encounter),
`tuning-plan-template.json`, `acceptance-thresholds.csv`, `parameter-registry.csv`,
`scenario-matrix.csv`. Preserve column meaning; add columns rather than repurposing them.

Extend the engine when the system needs positioning, phases, aggro, summons, or cross-battle state.
Keep `simulate(scenario, seed)` deterministic and the record shape intact and the rest of the
toolchain keeps working. Never approximate an unmodeled mechanic with a flat stat and present the
result as a measurement of the real encounter.

## Output Contract

1. Question, focus team, cohort, policy, and the declared band.
2. Model scope, assumption ledger, calibration steps run, and mechanics omitted.
3. Sampling: battles, seed blocks, convergence status, interval half-widths.
4. Findings ordered by player impact, as distributions with intervals.
5. Sensitivity ranking with the causal mechanism for each significant lever.
6. Proposal: smallest coherent change, predicted side effects, neighboring grid points.
7. Verification on unseen seeds, stated as held or not held.
8. Baseline, thresholds, gate result, and the open questions simulation cannot answer.

## Final Quality Gate

- Confirm every quoted number comes from at least 10,000 battles and carries its sample size,
  interval, and seed base.
- Confirm no conclusion rests on a non-converged run.
- Confirm search, verification, and acceptance used disjoint seed blocks.
- Confirm the policy and cohort are named wherever a win rate appears.
- Confirm tails and concentration were read, not only means and aggregate win rate.
- Confirm the proposal names its mechanism and its predicted side effects were checked.
- Confirm unmodeled mechanics and unanswerable questions are stated, not implied.
- Confirm a failed target is reported as failed, with the structural cause when the levers cannot reach it.
