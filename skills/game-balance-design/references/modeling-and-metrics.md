# Modeling And Metrics

Use this reference for mathematical choices shared by all systems. Domain references define how to apply them.

## Contents

1. Units and numerical contracts
2. Curve selection
3. Growth, accumulation, and discounting
4. Probability and distributions
5. Utility, budgets, and normalization
6. Sensitivity and breakpoints
7. Cohorts, aggregates, and uncertainty
8. Numerical implementation traps

## 1. Units And Numerical Contracts

Define for every variable:

`id | meaning | type | unit | clock | source/derived | valid range | default | precision | owner`

Keep different clocks explicit: per hit, action, second, tick, wave, encounter, run, session, day, week, event, or season. Never add or compare rates with different clocks before conversion.

Use decimal probabilities internally. State whether a displayed `20%` means `0.2`, `20`, additive percentage points, or a multiplicative percentage change.

Define calculation order, for example:

```text
base -> additive modifiers -> multiplicative groups -> caps -> rounding -> display
```

Group multipliers intentionally. If all multipliers stack independently, legal combinations can grow exponentially.

## 2. Curve Selection

Choose a curve because its marginal behavior matches the intended experience:

| Curve | Formula | Use | Main risk |
| --- | --- | --- | --- |
| Linear | `a + b*x` | Constant absolute gain | Relative gain collapses over time |
| Geometric | `a*(1+g)^x` | Constant percentage growth | Runaway values and obsolescence |
| Power | `a*(x+c)^p` | Smooth accelerating/decelerating growth | Hard-to-explain marginal changes |
| Logistic | `L + (U-L)/(1+exp(-k*(x-m)))` | Bounded adoption, caps, easing | Midpoint/steepness can hide cliffs |
| Hyperbolic | `U*x/(x+K)` | Diminishing returns | Soft cap can become opaque |
| Piecewise | Different formulas by phase | Distinct onboarding/mid/end behavior | Discontinuities and maintenance |
| Lookup table | Explicit authored points | Breakpoints and bespoke content | Manual drift without generation |

Check value, first difference, relative difference, and cumulative total. Plot or tabulate early, middle, late, and boundary points.

Prefer piecewise curves when the game changes phase. Do not force one elegant formula across onboarding, mastery, and endgame if their jobs differ.

## 3. Growth, Accumulation, And Discounting

Common formulas:

```text
geometric_value(n) = base * (1 + growth_rate)^n
cumulative_geometric(N) = base * ((1 + growth_rate)^N - 1) / growth_rate
relative_gain = new_value / old_value - 1
payback_period = upfront_cost / net_gain_per_period
present_utility = future_utility / (1 + discount_rate)^periods
```

Use cumulative totals for costs, XP, rewards, and time. A reasonable next-step price can still create an impossible cumulative journey.

For repeating loops, test steady state and transient state. A system can be stable after convergence but unusable during the first days, or healthy early and divergent later.

## 4. Probability And Distributions

For an independent event with probability `p`:

```text
expected_attempts = 1 / p
probability_at_least_once_by_n = 1 - (1 - p)^n
attempts_for_quantile(q) = ceil(log(1 - q) / log(1 - p))
variance_binomial = n * p * (1 - p)
```

With a hard guarantee at attempt `N`:

```text
expected_attempts = (1 - (1 - p)^N) / p
maximum_attempts = N
```

For a weighted table:

```text
P(item_i) = weight_i / sum(weights)
expected_value = sum(P(item_i) * utility(item_i))
```

Do not equate face value with utility. Account for duplicates, inventory state, build relevance, conversion value, and obsolescence.

Use the full distribution for high-stakes outcomes. Report mean, median, relevant percentiles, maximum exposure, and the probability of unacceptable tails. Model correlations and state transitions when rolls are not independent.

## 5. Utility, Budgets, And Normalization

Use a budget only within a declared context. A universal power score usually fails because damage, control, range, reliability, mobility, and economy change value by encounter and cohort.

For a local anchor, estimate marginal utility:

```text
marginal_utility(stat_i) = change_in_target_metric / change_in_stat_i
normalized_cost(stat_i) = stat_amount * local_weight_i
```

Recompute weights across low/reference/high states and relevant contexts. If weights vary sharply, expose the tradeoff instead of forcing equal point costs.

Evaluate an option with a context vector:

```text
utility = [burst, sustain, survival, control, mobility, reliability, economy, team_value]
```

Option A strictly dominates B if it is no worse in every intended context after opportunity cost and better in at least one. Pick rate alone does not prove dominance.

## 6. Sensitivity And Breakpoints

Measure local sensitivity:

```text
elasticity = (% change in output) / (% change in parameter)
```

Sweep important tunables at least at `-10%, -5%, baseline, +5%, +10%`, then test interacting parameters. Flag:

- Integer hits/turns/actions to completion.
- Speed thresholds that grant an extra action.
- Cooldown rotations and permanent uptime.
- Resource thresholds that enable loops.
- Price/stock points that change affordability.
- Rating or queue thresholds that change population pools.
- Caps, floors, rounding, overflow, and underflow.

Continuous averages can miss the actual player-visible breakpoint. Always calculate both.

## 7. Cohorts, Aggregates, And Uncertainty

Weighting cohorts produces an aggregate but can conceal opposite movement:

```text
aggregate_metric = sum(cohort_weight_i * cohort_metric_i)
```

Always inspect the components before acting. Control for eligibility, exposure, acquisition, skill, progression, platform, region, version, and selection effects.

For observed metrics, report numerator, denominator, time window, version, and uncertainty. Use confidence intervals for rates, bootstrap or suitable intervals for skewed distributions, and player-level rather than event-level sample sizes when repeated observations are correlated.

Do not compare a post-patch population with a pre-patch population without checking composition shift.

## 8. Numerical Implementation Traps

- Floating-point drift in currency or deterministic combat.
- Banker's rounding differing from design expectations.
- Rounding at multiple stages rather than once at the declared boundary.
- Inclusive/exclusive cap mismatch.
- Additive percentages accidentally multiplied, or independent multipliers accidentally added.
- Client and server using different formula versions.
- Integer overflow in exponential progression or idle games.
- Probability tables that do not sum to the intended total after filters.
- Seed reuse, non-deterministic iteration order, or platform-specific RNG.
- Time-zone, daylight-saving, clock rollback, offline claim, and reset races.
- Derived values copied into spreadsheets and configs, then edited independently.

Test zero, one, negative where legal, maximum, maximum stack, empty, full, simultaneous events, reconnect, migration, reset, and repeated idempotent processing.
