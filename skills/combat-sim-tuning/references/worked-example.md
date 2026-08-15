# Worked Example

A complete pass over the bundled scenario, `assets/templates/scenario-template.json`: a four-unit
party against a single boss. Every number below was produced by the bundled scripts at the
10,000-battle reporting floor. Reproduce any step by running the command shown.

## 1. Audit The Baseline

```bash
python3 sim_runner.py assets/templates/scenario-template.json --team party \
  --seed-base 0 --workers 8 --records-out base.json --report-out base.report.json
```

10,000 battles, about two seconds of wall clock on eight workers.

| Metric | Value |
| --- | --- |
| Win rate | 0.6824 (95% CI 0.6732-0.6915, +/-0.0091) |
| Rounds | mean 22.15, p50 22, p90 36, cv 0.457 |
| Timeout rate | 0.0020 |
| Max damage share | 0.4482 (rogue) |
| Min damage share | 0.0120 (cleric) |
| Effective contributors | 3.05 of 4 |
| Comeback rate | 0.885 |
| Blowout rate | 0.043 |

Three findings before touching anything. The encounter clears far above a 55% first-clear band, and
at this sample size that gap is not in doubt. The rogue owns 45% of party damage, over a 40% cap.
The p90 of 36 rounds against a p50 of 22 is a long tail: one clear in ten runs over 60% longer than
the typical one.

## 2. Establish What Precision Costs

```bash
python3 sim_runner.py assets/templates/scenario-template.json --team party \
  --target-half-width 0.005 --max-battles 30000 --workers 8
```

The run stops at the cap with a half-width of 0.00526 and reports **NOT CONVERGED**. Even 30,000
battles do not reach +/-0.005 at this win rate; roughly 33,000 would. That is the honest answer to
"how precise can we be": either budget the samples or widen the band. Do not quote the point
estimate as though the question were settled.

Note the shape of the cost. The floor of 10,000 battles buys +/-0.009. Halving that to +/-0.0046
costs four times as many battles. Precision is quadratic, so decide what the decision actually needs.

## 3. Rank The Levers

```bash
python3 sim_search.py sensitivity assets/templates/scenario-template.json \
  assets/templates/tuning-plan-template.json \
  --metric win_rate.point --metric rounds.mean --metric max_damage_share --workers 8
```

| Tunable | Baseline | abs_effect on win rate | Elasticity |
| --- | --- | --- | --- |
| `teams.boss.0.atk` | 800 | 0.167 | -0.0041 |
| `teams.boss.0.hp` | 10000 | 0.098 | -0.000185 |
| `teams.party.2.skills.0.power` | 0.55 | 0.026 | +1.16 |
| `teams.party.2.crit_chance` | 0.35 | 0.007 | +0.35 |

Boss attack is the strongest win-rate lever. Rogue crit chance moves the win rate by under a
percentage point, which matters: it is the obvious lever for the concentration problem but it will
not move the outcome band, so it must be paired with something that does.

## 4. Test The Obvious Fix, Paired

The reflex fix for a too-easy boss is more health. Test it under common random numbers rather than
assuming:

```bash
python3 sim_runner.py assets/templates/scenario-template.json --team party \
  --seed-base 0 --set teams.boss.0.hp=11000 --records-out cand.json
python3 sim_report.py compare base.json cand.json --team party
```

Win rate delta -0.1866 (95% CI -0.1942 to -0.1790) over 10,000 paired seeds. Outcome flips: 1,866
battles turned into losses, **zero** turned into wins. A flip count that one-directional is a real
monotone effect, not noise, and the paired interval is narrower than either unpaired interval.

But the same run pushes `rounds.mean` from 22.15 to 25.88, `rounds.p90` to 39 against a cap of 50,
and the timeout rate from 0.2% to 0.5%. The obvious fix overshoots the win rate and makes the pacing
problem worse. Health alone is the wrong lever.

## 5. Search Under Constraints

The bundled plan encodes six objectives: win rate 0.55 +/- 0.03 (double weight), rounds mean 18 +/- 3,
rounds p90 at most 32, timeout rate at most 0.02, max damage share at most 0.40, and at least 2.5
effective contributors. It searches at 2,000 battles per evaluation and verifies at 10,000.

```bash
python3 sim_search.py search assets/templates/scenario-template.json \
  assets/templates/tuning-plan-template.json --workers 8 --restarts 5 --out proposal.json
```

295 evaluations, about 590,000 battles, 103 seconds on eight workers. The restart table is the
interesting part of the output:

| Restart | Converged to | Objective |
| --- | --- | --- |
| 0 (baseline start) | hp 10000, atk 800, crit 0.18, power 0.54 | 2.87 |
| 1 | hp 10750, atk 740, crit 0.17, power 0.40 | 6.48 |
| **2** | **hp 8500, atk 860, crit 0.25, power 0.45** | **0.67** |
| 3 | hp 14000, atk 680, crit 0.26, power 0.50 | 15.14 |
| 4 | hp 11000, atk 780, crit 0.33, power 0.55 | 4.42 |

Descending from the baseline alone lands at 2.87 and stops. A different start reaches 0.67. Had the
searcher used a single start, it would have reported the worse configuration as its answer, with no
signal that a better basin existed four times closer to the targets.

Verification on a fresh seed block at 10,000 battles: win rate 0.5809 +/- 0.0097, rounds mean 22.01,
p90 33, max damage share 0.3613, effective contributors 3.13. The concentration problem is genuinely
fixed (0.448 to 0.361). The pacing objectives still fail, and the tool reports `satisfied: false`.
That is the correct output: the proposal is a real improvement that does not meet the brief.

## 6. Probe Where The Search Under-Explored

Sensitivity said boss attack and boss health are the two dominant levers, and the flip test showed
they pull the win rate and the pacing in opposite directions. The unexplored direction is moving
both together: less health to shorten the fight, more attack to hold the win rate down.

```bash
python3 sim_runner.py assets/templates/scenario-template.json --team party \
  --seed-base 2000000 --workers 8 \
  --set teams.boss.0.hp=7250 --set teams.boss.0.atk=940 \
  --set teams.party.2.crit_chance=0.25 --set teams.party.2.skills.0.power=0.47 \
  --report-out final.report.json
```

| Objective | Target | Result |
| --- | --- | --- |
| Win rate | 0.55 +/- 0.03 | 0.5714 +/- 0.0097 |
| Rounds mean | 18 +/- 3 | 18.67 |
| Rounds p90 | <= 32 | 28 |
| Timeout rate | <= 0.02 | 0.0000 |
| Max damage share | <= 0.40 | 0.3785 |
| Effective contributors | >= 2.5 | 3.09 |

All six objectives met, over 10,000 battles on a seed block used for neither search nor
verification. The lesson is not that the searcher failed; it narrowed a four-dimensional space to a
region and proved the concentration fix works. It is that a greedy search on a noisy surface produces
a candidate, and a candidate still needs a designer who reads the sensitivity table and tries the
direction the algorithm skipped.

## 7. Gate It

```bash
python3 sim_diff.py final.report.json assets/templates/acceptance-thresholds.csv
```

Thirteen of fifteen checks pass. Two fail, and both point at the same thing:

| Metric | Value | Bound |
| --- | --- | --- |
| `min_damage_share` | 0.0083 | min 0.08 |
| `units.party/cleric.survival_rate` | 0.1026 | min 0.25 |

The cleric contributes under 1% of party damage and dies in nine battles out of ten. None of the six
tuning objectives covered this, because `effective_contributors` at 3.09 of 4 looked healthy and
`max_damage_share` only watches the top of the roster. The gate caught what the objective set
missed.

That failure is not fixed by another search over the same four tunables. The cleric's problem is
that the boss targets the lowest health fraction, which is the healer as soon as it takes one hit;
the fix is a taunt, a threat rule, or a survivability floor. Structural, not numeric. Report it as
the next piece of work rather than relaxing the threshold to make the gate green.

## 8. What The Run Cannot Claim

Under the modeled `priority` policy with `lowest_hp_pct` targeting, at the reference power tier, the
proposal clears at 57.1% +/- 1.0% with a median of 19 rounds. It says nothing about whether players
discover the rotation, whether the fight reads clearly, how the clear rate moves across attempts as
players learn, or whether any of it is enjoyable. Those need the policy ladder in
`policies-and-agents.md` and a playtest.
