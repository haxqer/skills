# Regression And Reporting

Turning a tuning result into a baseline that future changes are measured against, and into a
report a reader can act on and disagree with.

## 1. The Baseline Snapshot

A baseline is the aggregated report plus everything needed to reproduce it. Store all of it under
version control next to the config it describes:

| Artifact | File | Why |
| --- | --- | --- |
| Scenario | `scenarios/<id>.json` | The model under test |
| Aggregated report | `baselines/<id>.report.json` | The numbers to diff against |
| Acceptance thresholds | `baselines/<id>.thresholds.csv` | What counts as a regression |
| Run parameters | Recorded in `report.run` | Battles, seed base, overrides, convergence |
| Tool version | Commit hash of the scripts | An engine change invalidates every baseline |

```bash
python3 sim_runner.py scenarios/warden.json --team party \
  --target-half-width 0.010 --min-battles 10000 --max-battles 200000 \
  --seed-base 2000000 --workers 8 \
  --report-out baselines/warden.report.json --format markdown
```

Record a baseline only from a converged run. A baseline built on a wide interval makes every later
comparison ambiguous, because you cannot tell a real regression from the noise you baked in.

Re-baseline when the design intent changes, never to make a failing gate pass. If a gate fails and
the new behavior is correct, that is a deliberate re-baseline with a stated reason in the commit
message, not a threshold edit.

## 2. Acceptance Thresholds

`assets/templates/acceptance-thresholds.csv` has one row per checked metric:

| Column | Meaning |
| --- | --- |
| `metric` | Dotted path into the report |
| `min` / `max` | Absolute bounds, blank for unbounded |
| `max_delta` | Largest allowed absolute change from the baseline |
| `max_delta_pct` | Largest allowed relative change from the baseline |
| `note` | Why the bound exists |

Absolute bounds encode design intent. Delta bounds catch drift that stays technically in range
while walking steadily in one direction across releases. Use both: a metric with only a wide
absolute bound can move 80% of its allowance in one patch and nobody notices.

Always gate `win_rate.half_width`. Without it, a run with too few battles passes every other check
by being too imprecise to fail. A bound of 0.01 enforces the 10,000-battle floor without naming a
battle count, and tightens automatically when a metric needs more.

Write the `note` for a reader who was not in the tuning session. "A timeout is an unreadable
outcome" survives a year; "keep under 2%" does not.

## 3. Running The Gate

```bash
python3 sim_diff.py candidate.report.json thresholds.csv --baseline baselines/warden.report.json
```

Exit codes are distinct on purpose: `0` all checks passed, `1` a tool error, `2` at least one
threshold violated. That separation lets the gate run unattended without a broken file path
masquerading as a passing run.

The output names every failing metric with its baseline value, candidate value, delta, and the
specific bound that was crossed. A metric absent from the report is reported as `missing` rather
than passing silently, which is what catches a renamed unit or a typo in a path.

If the candidate run did not converge, the gate says so and marks every verdict provisional. Fix
the sample size rather than reading the table.

## 4. The Report Contract

Every simulation deliverable states, without being asked:

1. **Question**: the specific decision this run informs.
2. **Model and assumptions**: what is modeled, what is not, which calibration steps were run, and
   which values are Observed, Assumed, Derived, or Recommended.
3. **Policies and cohorts**: the exact policy ladder and power tiers run.
4. **Sampling**: battles, seed blocks, convergence status, interval half-widths.
5. **Findings**: distributions, not just means, ordered by player impact.
6. **Proposal**: smallest coherent change, mechanism, predicted side effects, neighbors checked.
7. **Verification**: fresh-seed confirmation, and whether it held.
8. **Limits**: what this run cannot answer, and what would answer it.

Lead with the finding, not the method. A reader who stops after the first paragraph should have the
number, its interval, and whether it clears the band.

## 5. Language That Stays Honest

| Do not write | Write |
| --- | --- |
| "Win rate is 55%" | "Win rate 55.2% (95% CI 54.2-56.2, n=10000, converged)" |
| "Balanced" | "Within the 52-58% band under the core policy; fails at the floor rung (31%)" |
| "The rogue is overpowered" | "Rogue mean damage share 44% (CI 43-45), above the 40% cap" |
| "Simulations show players will..." | "Under the modeled policies, the simulated outcome is..." |
| "Fun improved" | "Effective contributors rose 1.9 to 3.1; fun was not measured" |
| "Fixed" | "Meets four of six objectives; rounds.p90 and max_damage_share still fail" |

Report a failure to reach the target as prominently as a success. The value of this method is that
it can say no; a workflow that only ever produces good news has stopped measuring anything.

## 6. Regression Rhythm

- Run the gate on every config change that touches a tuned parameter, before review.
- Keep the acceptance run on a seed block never used for tuning or verification.
- Re-run the whole scenario matrix, not only the scenario you edited. Combat parameters couple, and
  the encounter you did not touch is where the side effect shows up.
- When a gate fails, first check whether the candidate run converged, then whether the failure
  reproduces on a second seed block, then investigate the mechanism. Two of three failures
  investigated straight from a single non-converged run are noise.
- Archive every gate result with its commit. The history of a metric across releases is how you
  catch slow drift that no single patch triggered.
