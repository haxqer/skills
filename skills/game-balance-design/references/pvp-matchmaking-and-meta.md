# PvP, Matchmaking, And Meta

Use this reference for competitive balance, ratings, matchmaking, team assembly, queue quality, parties, smurfs, maps, sides, metas, seasons, and balance patches.

## Contents

1. Competitive contract
2. Ratings and uncertainty
3. Match quality and queue expansion
4. Teams, parties, roles, and inputs
5. Smurfs, new players, and integrity
6. Conditional balance metrics
7. Matchups and meta health
8. Maps, sides, modes, and objectives
9. Competitive progression and access
10. Patch design and migration
11. Seasons and rating resets
12. Validation and telemetry

## 1. Competitive Contract

Define:

- Ranked, unranked, tournament, social, asymmetrical, co-op competitive, or mixed mode.
- Solo/party rules, team size, role requirements, crossplay, input pools, region, and latency.
- What persistent power, collection, payment, loadout, randomness, and map selection affect outcomes.
- Match length, surrender, disconnect, backfill, remake, leaver, and draw rules.
- Rating purpose: skill estimate, visible progression, rewards, matchmaking, or several separate values.

Do not use hidden forced-loss or forced-win scheduling to control streaks or retention. Matchmaking should estimate fair/appropriate opponents under queue constraints, not predetermine outcomes.

## 2. Ratings And Uncertainty

For an Elo-style baseline:

```text
expected_A = 1 / (1 + 10^((rating_B - rating_A) / scale))
new_rating_A = rating_A + K * (score_A - expected_A)
```

Treat `scale` and `K` as design parameters tied to calibration and convergence, not tradition. Team games, inactivity, role, party, uncertainty, and changing skill often need Glicko/TrueSkill-like uncertainty or a proven rating system rather than plain Elo.

Keep visible rank separate from hidden skill estimate when their jobs differ, but communicate progression enough to preserve trust.

Validate calibration:

- Players assigned 60% expected win should win near 60% over matched contexts.
- Calibration should hold by rating, uncertainty, party, region, input, mode, role, and season phase.
- Rating residuals should not systematically favor maps, sides, platforms, or queue times.

Do not evaluate a rating system only by rank distribution.

## 3. Match Quality And Queue Expansion

Matchmaking is a constrained optimization:

```text
quality = skill_balance + uncertainty_fit + latency + party_fit + role_fit + input_fit + rematch_diversity
```

Weights and hard constraints depend on mode and population. Define which constraints expand with wait time, at what thresholds, and for whom.

Report the distribution of pre-match expected win probability, not only average difference. A diagnostic starting target for ordinary symmetrical matches is p50 near 47-53%, with explicit tail limits.

Measure:

- Queue p50/p90/p99 by region, time, rating, party, role, and input.
- Expected-win distribution and rating uncertainty.
- Latency, backfill, rematch, role autofill, and cancellation.
- Population pool size and expansion stage at match creation.

Avoid improving aggregate queue time by creating unacceptable tails for rare roles or high-skill players without transparent tradeoffs.

## 4. Teams, Parties, Roles, And Inputs

Do not model a team only by average rating. Include rating spread, uncertainty, role fit, party coordination, input, latency, and composition synergy.

Estimate party advantage from data conditional on skill and party size. Match parties symmetrically where population permits or include a calibrated party adjustment.

For role queues, model:

- Role supply/demand and wait distribution.
- Autofill frequency and performance penalty.
- Role-specific skill estimates where roles differ materially.
- Swap, flex, dodge, and queue manipulation.

For crossplay/input, measure conditional performance and aim/movement mechanics. Do not assume equal average win means equal experience; skill curves and specific weapon roles can differ.

## 5. Smurfs, New Players, And Integrity

New players need rapid but bounded uncertainty resolution. Use onboarding matches, provisional uncertainty, broad behavior signals, or accelerated rating movement while protecting ordinary low-skill players.

Detect smurfs with multiple signals such as outcome residuals, mechanics, speed of learning, account linkage where permitted, and repeated dominance. Avoid punishing genuinely improving players or alternate play styles.

Separate:

- Smurfing, boosting, account sharing, win trading, botting, intentional deranking, dodge abuse, and party manipulation.
- Competitive enforcement from ordinary matchmaking correction.

Test surrender, disconnect, remake, backfill, and rating protection for exploitability.

## 6. Conditional Balance Metrics

For characters, weapons, decks, or strategies, inspect:

- Pick, ban, win, encounter, availability, and mastery.
- Conditional win lift over pre-match expectation.
- Performance by skill band, experience with the option, matchup, map, side, party, input, and composition.
- Early adoption, novelty, selection, and survivor bias.

Useful metric:

```text
conditional_win_lift = actual_result - pre_match_expected_win
```

Aggregate win rate can hide expert dominance or novice frustration. A 56% win rate on an option selected mainly by stronger players is not causal proof; a 50% overall win can hide 65% at expert level and 40% at novice level.

Use player-level or match-level confidence intervals and correct for repeated observations. Avoid acting on small samples after many unplanned comparisons.

## 7. Matchups And Meta Health

Build matchup matrices by skill band and context. Measure:

- Pairwise advantage and confidence.
- Counter availability, acquisition, recognition, and execution burden.
- Composition and team synergy.
- First-pick, last-pick, flex, and ban value.
- Strategy transition after a patch.

Normalized pick entropy can describe diversity:

```text
normalized_entropy = -sum(p_i * log(p_i)) / log(number_of_options)
```

High entropy is not sufficient; all options can be equally picked in polarized or frustrating matchups. Also track dominance, counter concentration, matchup polarization, viable composition count, and skill expression.

A counter is not healthy if it is inaccessible, useful only on one map, requires much higher execution, or creates a binary non-game.

## 8. Maps, Sides, Modes, And Objectives

Measure option balance conditional on map, side, spawn, mode, objective order, and overtime. Audit:

- Side/first-player advantage and map-specific rating residual.
- Spawn safety, travel, sight lines, cover, objective access, and resource positions.
- Overtime, tie-break, sudden death, and comeback rules.
- Map veto/selection and player specialization.

Do not solve a map-specific dominance problem with a global character nerf unless the mechanic is unhealthy elsewhere.

For asymmetrical games, set role-specific outcome targets and rotate sides when possible. Equal aggregate win does not guarantee equal agency or satisfaction.

## 9. Competitive Progression And Access

Define whether progression affects ranked power. If it does, measure:

- Time and cost to a viable roster/loadout and required counters.
- Paid versus non-paid access and time-to-parity.
- New-season reset and returning-player access.
- Ban/pick format requirements and roster depth.

Keep required competitive counters reasonably accessible. Do not use rarity or payment as balance compensation.

Rewards should not make losing intentionally optimal, encourage deranking, or force unhealthy volume. Separate visible progression from skill estimation if needed.

## 10. Patch Design And Migration

Patch the causal mechanism while preserving identity. Before changing values:

1. Verify data quality, population selection, and confidence.
2. Identify whether power, reliability, access, map, composition, or mastery causes the symptom.
3. Find the smallest parameter that crosses the relevant breakpoint.
4. Predict substitution and affected cohorts.
5. Define migration, respec/refund, communication, and rollback.

Avoid simultaneous broad buffs and nerfs that make attribution impossible. Bundles are acceptable when the mechanic only functions as a coherent package.

Protect player investments. If a purchased/unlocked option changes identity or viability, define compensation or respec behavior.

## 11. Seasons And Rating Resets

Use resets to handle uncertainty, population return, and visible goals, not to manufacture grind. Specify:

- Hidden rating carryover, uncertainty increase, placement, and visible-rank compression.
- New, returning, inactive, and high-end player treatment.
- Party and role estimates.
- Reward thresholds and anti-derank controls.

Simulate early-season pool mixing, late joiners, region/time populations, and repeated resets. A reset that is too hard creates poor matches; too soft can remove progression meaning.

## 12. Validation And Telemetry

Validate offline with historical replay, counterfactual pairing where feasible, synthetic population simulation, and adversarial queue policies. Then stage limited live tests at match-level assignment so both teams share one ruleset.

Emit and analyze:

```text
queue_enter: rating, uncertainty, role, party, input, region, constraints
match_created: all player estimates, expansion stage, expected win, map, side, config
match_result: result, duration, surrender, disconnect, rating delta, objective state
option_usage: option, loadout, availability, mastery, map, matchup, outcome contribution
```

Set success and rollback for match quality, queue tails, conditional option lift, pick/ban diversity, side/map balance, disconnect/surrender, substitution, and affected cohorts.

Do not declare success from aggregate 50% win rate while calibration, queue tails, expert dominance, access, or match quality worsens.
