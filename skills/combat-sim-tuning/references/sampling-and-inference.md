# Sampling And Inference

Running a scenario ten thousand times is cheap. Drawing a correct conclusion from those ten
thousand runs is the actual work. This file covers how many samples you need, how to spend fewer of
them, and the inference mistakes that make a simulation confidently wrong.

## 1. The Floor Is 10,000 Battles

No number gets quoted from fewer than 10,000 battles. That is the reporting floor the tools default
to (`sim_runner.py --battles`, `--min-battles`), and it is the point where a win rate is precise to
about +/-1 percentage point, which is roughly the resolution a balance decision needs.

Runs below the floor have exactly two legitimate uses, both intermediate and neither quotable:
search evaluations inside `sim_search.py`, and smoke-checking that a scenario file parses and
resolves. Every such run is followed by a full-floor verification before any conclusion is drawn.

## 2. Sample Size Above The Floor Is A Consequence, Not A Choice

The floor is a minimum, not a target. The number of battles is whatever makes the interval tight
enough to decide the question. For a win rate, the 95% Wilson half-width near 0.5 is roughly
`0.98 / sqrt(n)`:

| Battles | Half-width near p=0.5 | Can distinguish |
| --- | --- | --- |
| 1,000 (below floor) | ~0.031 | 50% from 55% |
| 2,000 (below floor) | ~0.022 | 50% from 53.5% |
| **10,000 (floor)** | **~0.010** | **50% from 51.5%** |
| 40,000 | ~0.005 | 50% from 50.7% |
| 100,000 | ~0.003 | 50% from 50.5% |
| 400,000 | ~0.0015 | 50% from 50.2% |

Read it in reverse: if the band you are tuning to is +/-0.5 points of win rate, the floor is not
enough and you need roughly 400,000 battles. Precision costs quadratically, so every halving of the
interval costs four times the compute. Decide what precision the decision actually needs first.

Use the Wilson interval, never the normal approximation `p +/- z*sqrt(p(1-p)/n)`. Near 0 and 1 the
normal form produces intervals that extend past the unit interval and understate uncertainty
exactly where rare-event tuning happens.

Rates other than the win rate need their own sample budget, and rare events need far more than the
floor. A 2% timeout rate measured over 10,000 battles has an interval of roughly 1.75% to 2.29%,
which still straddles a 2% threshold. Deciding that threshold needs 40,000 or more.

## 3. Sequential Sampling

`sim_runner.py --target-half-width` adds samples in chunks until the win-rate interval is tight
enough or `--max-battles` binds:

```bash
python3 sim_runner.py scenario.json --team party \
  --target-half-width 0.010 --min-battles 10000 --max-battles 200000 --workers 8
```

If the cap binds first, the run summary reports `converged: false` and the markdown output prints
a NOT CONVERGED banner. Report that state. Quoting the point estimate from a non-converged run as
though it settled the question is the single most common way a simulation misleads a team.

Sequential stopping does inflate the false-positive rate slightly if you also use the stopping
statistic as your significance test. Use it to control precision, then judge the result against
the band you declared beforehand, not against a p-value computed at the stopping point.

## 4. Common Random Numbers

To compare variant A against variant B, run both with the same `--seed-base` so battle *i* faces
the identical random stream in both. The shared noise cancels in the paired difference, and small
real effects become visible at sample sizes where the two unpaired intervals still overlap.

```bash
python3 sim_runner.py scenario.json --seed-base 0 --records-out a.json
python3 sim_runner.py scenario.json --seed-base 0 --set teams.boss.0.hp=11000 --records-out b.json
python3 sim_report.py compare a.json b.json --team party
```

`paired_compare` reports the mean paired delta with an interval, plus `outcome_flips`, which
counts how many individual battles changed result and in which direction. A change where flips run
overwhelmingly in one direction is a real monotone effect; roughly balanced flips with a near-zero
mean is noise, no matter how different the two point estimates look. At the 10,000-battle floor the
paired interval on a win-rate delta is roughly +/-0.008, tight enough to resolve a one-point effect.

Common random numbers only pair correctly when the change does not alter how much randomness each
battle consumes. Adding a skill, changing a policy, or changing hit counts shifts the random
stream, and the pairing degrades toward an ordinary unpaired comparison. That is not an error, but
do not claim paired precision for it: say the comparison is unpaired and size it accordingly.

## 5. Seed Hygiene

Tuning against a fixed seed block overfits to that block. The parameters end up exploiting the
specific sequence of crits and misses in those battles.

Split seeds into three disjoint blocks and never mix their roles:

| Block | Use | Example |
| --- | --- | --- |
| Tuning | Sensitivity and search evaluations | `--seed-base 0` |
| Verification | Confirm the proposal on unseen seeds | `--seed-base 1000000` |
| Acceptance | Regression gate before release | `--seed-base 2000000` |

`sim_search.py search` does this automatically: it searches on `seed_base` and re-scores the
winning proposal on `verify_seed_base` at `verify_battles`, reporting `held_on_fresh_seeds`. A
proposal that satisfies every objective during the search and fails verification is overfitted, not
finished. In practice a drop of a few points of win rate between search and verification is normal;
a proposal that only clears its band on the tuning block should be treated as not clearing it.

## 6. Distributions, Not Averages

The mean is the least informative number in the report. Two encounters with identical mean length
of 20 rounds are different games if one has p90 of 24 and the other has p90 of 45.

Always read, and always report:

- `p10`, `p50`, `p90` alongside the mean for every duration metric.
- `cv` (standard deviation over mean). Above roughly 0.5, individual outcomes are mostly noise
  around the design intent, and the median player experience is not the mean.
- The tail rates: `timeout_rate`, `blowout_rate`, `close_rate`.

A balance change that moves the mean while widening the tail usually makes the game worse. Judge
the change on the distribution it produces, not on the anchor it hits.

## 7. Multiple Comparisons

A report contains dozens of metrics. Scanning all of them for anything that moved and then
reporting the movers guarantees false positives: at a 5% threshold, one metric in twenty crosses
by chance.

Rules that keep this honest:

- Declare the primary metric and its band before running.
- Treat every other movement as a hypothesis for a targeted follow-up run, not as a finding.
- When comparing many variants, either raise the threshold (divide the target alpha by the number
  of comparisons) or re-run only the survivors on a fresh seed block.
- Do not compare each of twelve characters against every other and report the significant pairs.
  Compare each against the roster mean, then confirm the outliers.

## 8. When The Simulation Cannot Answer The Question

Say so and stop. A simulation cannot tell you:

- Whether players will find the intended strategy. It measures the strategy you programmed.
- Whether a fight is fun. It measures length, variance, contribution, and outcome.
- How real players will adapt across attempts. Learning is not in the model unless you modeled it.
- Anything about a mechanic you did not implement.

The honest output is a bounded claim: "under the modeled policies and stated assumptions, the
reference cohort clears at 55.2% +/- 1.0% over 10,000 battles with a median of 18 rounds."
Everything past that boundary
needs a playtest or telemetry, not more battles.
