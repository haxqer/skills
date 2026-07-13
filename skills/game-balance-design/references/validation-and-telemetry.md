# Validation And Telemetry

Use this reference to validate numerical systems with deterministic tests, simulation, playtests, statistics, telemetry, experiments, rollout, and diagnosis.

## Contents

1. Validation ladder
2. Model and simulation types
3. Scenario and policy design
4. Sensitivity, stress, and adversarial tests
5. Statistical uncertainty
6. Telemetry contracts and data quality
7. Playtest protocol
8. Experiment design and causal traps
9. Rollout and rollback
10. Diagnosis patterns

## 1. Validation Ladder

Validate in increasing-cost order:

1. **Static rules**: schema, units, range, references, probability totals, and ownership.
2. **Invariants**: conservation, monotonicity where intended, caps, no impossible state.
3. **Analytical cases**: TTK, cumulative cost, expected drops, stock-flow, rating expectation.
4. **Deterministic golden tests**: calculation order, rounding, reset, migration, and simultaneous events.
5. **Seeded simulation**: policies, outcomes, tails, sensitivity, and feedback loops.
6. **Structured playtest**: decisions, comprehension, behavior, emotion, and usability.
7. **Historical/telemetry comparison**: calibration against real cohorts and versions.
8. **Limited rollout**: guarded live exposure with stop and rollback.

Do not use a large playtest to discover arithmetic or data errors. Do not use telemetry to answer a question the event schema cannot distinguish.

## 2. Model And Simulation Types

Choose the simplest model that preserves the causal state:

- **Closed-form calculation**: simple expectations, curves, budgets, and breakpoints.
- **Spreadsheet model**: transparent authored scenarios and sensitivity.
- **Deterministic state machine**: formula order, cooldowns, pity, transactions, resets.
- **Monte Carlo**: RNG distributions and interacting uncertain inputs.
- **Discrete-event simulation**: queues, cooldowns, waves, sessions, markets, and time gates.
- **Agent/policy simulation**: builds, purchase strategies, match populations, and adaptation.
- **Historical replay**: apply a candidate rule to versioned prior states when counterfactual limits are understood.

Document model boundary, state, policies, random variables, correlations, seeds, horizon, sample count, outputs, and known omissions.

Do not randomize player actions uniformly. Use observed or hypothesized policies with error and learning models. Validate that simulated choice frequencies resemble real behavior before trusting outcome forecasts.

## 3. Scenario And Policy Design

Construct a scenario matrix:

```text
cohort x power/access x policy/build x content/state x attempt/time x RNG/matchup x version
```

Cover:

- Low/reference/high and maximum legal state.
- Intended, alternative, naive, optimized, exploit, and stop/hoard policies.
- First exposure, learned, repeated/farm, returning, and season-boundary behavior.
- Favorable/reference/adverse seeds and correlated streaks.
- Empty/full inventory, depleted resources, disconnect, retry, and migration.

For each scenario, record inputs, expected behavior, target outcome, guardrail, result, margin, and pass/fail reason.

Prefer a compact orthogonal matrix to many redundant cases. Add a case when it tests a new mechanism or boundary.

## 4. Sensitivity, Stress, And Adversarial Tests

Sweep high-leverage parameters at `-10%, -5%, baseline, +5%, +10%` or domain-appropriate bands. Calculate:

```text
elasticity = (% change in outcome) / (% change in parameter)
```

Test known interacting parameters jointly, especially multipliers, proc rates, income/cost growth, party composition, and population size.

Stress:

- Zero, one, min, max, cap, overflow, underflow, and rounding boundary.
- Maximum legal stacking and minimum viable state.
- Long horizon and repeated resets.
- Low population, high latency, high concurrency, and delayed events.
- Duplicate requests, retries, clock changes, partial deploy, and stale config.
- Adversarial market cycles, reward filters, build combos, and queue policies.

Identify breakpoints where tiny changes move an integer outcome: one fewer hit, one extra action, affordability a day earlier, pity reached, or a queue pool expanded.

## 5. Statistical Uncertainty

Always report numerator, denominator, unit of analysis, version, cohort, and time window.

For a binary proportion with estimate `p_hat`, sample `n`, and normal quantile `z`, use a Wilson interval when appropriate:

```text
center = (p_hat + z^2/(2n)) / (1 + z^2/n)
half_width = z/(1 + z^2/n) * sqrt(p_hat*(1-p_hat)/n + z^2/(4n^2))
interval = center +/- half_width
```

A conservative planning approximation for margin `m` is:

```text
n ~= z^2 * 0.25 / m^2
```

Adjust for clustering and repeated observations. Ten thousand matches from a small set of players do not equal ten thousand independent players.

Use suitable methods:

- Wilson/exact intervals for rates.
- Bootstrap or quantile intervals for skewed time, spend, and balance.
- Survival analysis for time-to-event with censoring.
- Calibration curves for predicted win/clear probability.
- Multiple-comparison control or predeclared hypotheses when scanning many options.

Show practical effect size and guardrails, not p-values alone. A precise tiny change may not matter; a large uncertain harm may still require stopping.

Check Simpson's paradox and composition shift before comparing aggregates.

## 6. Telemetry Contracts And Data Quality

Version formulas, configs, content, experiments, and event schemas. Emit stable IDs, not localized display names.

Common events:

```text
encounter_start: content_id, config, cohort_features, build, resources, attempt
mechanic_event: mechanic_id, offered_state, response, timing, outcome
effect_event: source, target, raw, modifiers, final, state
encounter_end: result, duration, margin, cause, retry_path
progression_event: source, requirement, before, delta, after, goal
economy_transaction: transaction_id, reason, before, delta, after, config
reward_roll: table, probability_path, pity_before, outcome, pity_after
queue_and_match: rating, uncertainty, constraints, expected_win, map, result
choice_event: options_visible, chosen, costs, unavailable_reason
```

Separate:

- Eligibility, exposure, offer, attempt, choice, result, repeat, and mastery.
- Earned, purchased, granted, refunded, compensated, and migrated value.
- Actual session end, disconnect, crash, abandon, and content switch.
- Build availability from build selection.
- Expected match outcome from realized result.

Create data-quality checks for duplicate IDs, missing versions, impossible values, probability mismatch, ledger reconciliation, event ordering, clock skew, sample loss, bot traffic, and schema drift.

Do not derive sensitive cohorts when game behavior and progression state suffice. Follow privacy, retention, consent, age, and regional requirements.

## 7. Playtest Protocol

State the hypothesis and cohort before recruiting. Record relevant genre familiarity, build/power state, and prior exposure without coaching the answer.

Observe:

- Decisions considered, chosen, delayed, and ignored.
- Attempt result, duration, margin, failure cause, and retry.
- Mechanic comprehension before and after feedback.
- Strategy or build changes between attempts.
- Confidence, fairness, frustration, boredom, and perceived agency.
- UI/tooltips needed to calculate or compare choices.

Ask after observation:

- What did you think happened?
- What would you change next?
- Which options did you consider and why?
- What outcome did you expect?

Do not rely only on "fun" or "hard" ratings. Compare stated belief with behavior and model prediction.

For a near miss, require the player to name a plausible corrective action and show improved behavior on a later attempt.

## 8. Experiment Design And Causal Traps

Write the hypothesis:

`Changing [source parameter/rule] from A to B should move [primary metric] for [eligible cohort] by [meaningful range], while [guardrails] remain bounded, because [mechanism].`

Predefine:

- Unit of assignment, eligibility, exposure, and contamination risk.
- Primary metric, practical effect, guardrails, and stop conditions.
- Sample/duration covering weekly, season, novelty, and learning cycles.
- Stratification by key cohorts and version.
- Interaction with other events, patches, and acquisition changes.

Use match-level assignment when both teams must share rules. Use account-level assignment for persistent economies only when cross-account trade/social contamination is handled. Some economy or marketplace changes require region/server-level staging.

Watch for:

- Selection, survivorship, novelty, learning, and regression to the mean.
- Composition shift, seasonality, concurrent patches, and event overlap.
- Peeking, repeated testing, multiple comparisons, and metric substitution.
- Network interference in parties, guilds, markets, or matchmaking.
- Players crossing cohorts because the treatment changes behavior.

Do not bundle unrelated changes unless the bundle is the actual decision. If bundled, do not claim component-level causality.

## 9. Rollout And Rollback

Use stages appropriate to risk:

1. Offline calculation and tests.
2. Shadow computation/logging without changing outcomes.
3. Internal or test environment.
4. Small eligible cohort/region/mode/server.
5. Expanded exposure after guardrails pass.
6. Full rollout with continuing holdout where appropriate.

Define before release:

- Exposure and config snapshot rules.
- Success, guardrail, stop, and rollback thresholds.
- Minimum sample and maximum harm budget.
- Monitoring owner and response time.
- Migration, respec, compensation, and player communication.
- Rollback target and behavior for state created under the new version.

Rollback immediately for integrity, unrecoverable economy, paid-odds mismatch, data corruption, crash, exploit, or severe fairness failures. Do not wait for statistical significance when the mechanism is clearly harmful.

## 10. Diagnosis Patterns

| Symptom | Mechanisms to distinguish | Evidence |
| --- | --- | --- |
| Low clear | Knowledge, execution, build, stats, resources, RNG, performance | Attempt slope, response, build snapshot, failure margin/cause |
| Repeated same near miss | Hidden stat check, fixed breakpoint, no useful feedback | Margin by attempt, policy changes, breakpoints |
| High clear but low satisfaction | Low agency, excessive duration, reward mismatch, trivial choices | Choice distribution, time breakdown, replay, playtest |
| Dominant option | True power, reliability, access, ease, content bias, expert mastery | Conditional lift, context matrix, availability, skill band |
| Currency inflation | Source spike, sink obsolescence, exploit, event carryover, cohort concentration | Reconciled flow, source/sink shares, legal envelope |
| High balance tail | Hoarding, missing goals, market wealth, grants, exploit, metric error | Opening stock, ledger, stock-days, transactions |
| Gate churn | Difficulty, retry, clarity, reward, session boundary, performance | Funnel stages, failure, next action, retry time |
| PvP streaks | Rating uncertainty, party, smurf, tilt, population timing, map/side | Expected win sequence, pool, party/input/map |
| Reward complaints | Bad tail, duplicates, displayed-odds mismatch, low useful utility | Drought, collection state, probability path, pity |
| Patch fails | Wrong mechanism, composition shift, substitution, insufficient breakpoint | Conditional metrics, sensitivity, option migration |

Do not choose a fix until evidence separates the leading mechanisms. State confidence and the cheapest next test for unresolved causes.
