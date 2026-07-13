# Foundations And Player Models

Use this reference before assigning values. Numerical design starts with player decisions and system state, not a spreadsheet curve.

## Contents

1. Experience-to-number stack
2. Design brief and lifecycle
3. Player state and policy models
4. Target specification
5. System maps and ledgers
6. Anchors and budgets
7. Top-down and bottom-up reconciliation
8. Evidence, confidence, and assumptions
9. Common failure patterns

## 1. Experience-To-Number Stack

Trace every consequential number through four layers:

```text
experience -> decisions -> system behavior -> source parameters
```

Use the layers as a review test:

| Layer | Required question | Example |
| --- | --- | --- |
| Experience | What should the player feel or learn? | "The boss initially feels overwhelming but fair." |
| Decision | Which informed action changes the outcome? | Save interrupt for the telegraphed heal. |
| System | Which state transition rewards that action? | Interrupt removes heal and opens a damage window. |
| Parameters | Which owned values control the transition? | Cast time, heal %, interrupt duration, boss EHP. |

If a parameter cannot be connected upward, it may be accidental complexity. If an experience cannot be connected downward, it is not yet a numerical specification.

## 2. Design Brief And Lifecycle

Lock these fields before choosing detailed values:

- Product and mode, platform/input, genre and primary loop.
- Intended audience, session length, social context, and accessibility requirements.
- Lifecycle: paper design, prototype, vertical slice, alpha, soft launch, mature live game, or sunset.
- Content topology: linear, branching, repeatable, run-based, seasonal, competitive, or sandbox.
- Failure/retry cost, persistence, loss severity, and recovery paths.
- Progression horizon, content cadence, season length, and reset policy.
- Competitive integrity and monetization boundaries.
- Technical limits: tick rate, entity count, integer width, server authority, hot-config support, and offline behavior.
- Decision the work must enable and what remains out of scope.

Change the method by lifecycle:

| Stage | Primary evidence | Appropriate precision | Main risk |
| --- | --- | --- | --- |
| Paper/prototype | Design anchors and analogs | Wide ranges | False precision |
| Vertical slice | Instrumented playtests | Reference cases | Building the wrong loop |
| Alpha/beta | Cohort distributions | Curves and boundaries | Content scaling |
| Soft launch | Real telemetry and experiments | Confidence bands | Economy and retention health |
| Mature live | Versioned causal evidence | Small reversible changes | Player investment and migration |

## 3. Player State And Policy Models

Represent a player profile as several independent dimensions:

```text
player_state = {
  execution_skill,
  system_knowledge,
  available_power,
  resources,
  collection_access,
  time_budget,
  social_coordination,
  intent,
  risk_tolerance
}
```

Do not collapse this vector into one "player level." Two players with equal power can differ in knowledge and policy; two equal-skill players can have different legal options.

Create reference profiles across at least:

- **Execution**: novice, intended/core, expert.
- **Power/access**: minimum legal, expected, high but legal.
- **Knowledge**: blind, informed, mastered.
- **Policy**: aggressive, safe, greedy, economy-first, objective-first, or genre-specific alternatives.
- **Time pattern**: short-session, regular, intermittent, optimizer, returning.

Keep payment or acquisition source separate. Use it to test access and fairness, not as a proxy for skill or desired difficulty.

Model behavior with explicit policies. Examples:

- Use heal below 35% HP; otherwise attack.
- Buy the cheapest upgrade with payback below the remaining content horizon.
- Reroll only when all offers fail the current build's minimum utility.
- Queue with a party only when role coverage is available.

For simulation, use policy distributions and error models rather than uniformly random actions. Include correlated mistakes, learning between attempts, and policy changes after feedback.

## 4. Target Specification

Write a target as a tuple:

```text
(cohort, eligibility, state, metric, distribution, time/attempt, target band, guardrail)
```

Examples:

- Among eligible core players at reference power, target 30-50% blind clear and 65-80% clear by attempt 5; keep median failed margin at 5-15% boss EHP and first-failure abandonment below 15%.
- For active day-14 core players, target one meaningful upgrade every 1.8-2.2 days; keep p90 required-cost failure below 5%.
- For solo ranked players with rating uncertainty below the threshold, target p50 expected win probability at 47-53%; keep p90 queue time under 120 seconds.

Distinguish:

- **Input metric**: tunable or player state, such as damage or income.
- **Intermediate metric**: TTK, affordability, completion probability, or match expectation.
- **Outcome metric**: clear, choice, progression, match result, or abandonment.
- **Experience metric**: perceived fairness, comprehension, confidence, or mastery.
- **Guardrail**: a result that must not degrade while optimizing the target.

Avoid population metrics whose denominator mixes eligibility, exposure, attempt, and completion.

## 5. System Maps And Ledgers

Map all primary and secondary loops:

```text
action -> immediate outcome -> reward/cost -> persistent state -> new options -> next action
```

Maintain separate ledgers:

- **Stat ledger**: source stats, modifiers, derived stats, caps, stacking, display.
- **Combat ledger**: damage, healing, control, resources, cooldowns, targets, timing.
- **Progression ledger**: XP, level, unlock, gear, collection, enhancement, prestige.
- **Economy ledger**: stocks, sources, sinks, exchanges, claims, refunds, expiry.
- **Reward ledger**: table, roll stage, rarity, utility, duplicate, pity, guarantee.
- **Time ledger**: active time, wait, cooldown, energy, retry, travel, queue.
- **Competitive ledger**: rating, uncertainty, party, role, input, latency, map and side.

Draw dependencies between source parameters and derived outputs. Mark:

- Positive and negative feedback loops.
- Multiplicative stacks.
- Shared parameters with high blast radius.
- Reset and migration boundaries.
- Server-authoritative and client-display values.
- Irreversible player investments.

## 6. Anchors And Budgets

Choose a small set of player-visible anchors:

- Combat: hits/turns to kill, burst window, encounter duration, recovery cadence.
- Progression: minutes/sessions per level, meaningful upgrades per week, power per tier.
- Economy: spendable income, time-to-goal, stock-days, sink and source concentration.
- Rewards: useful reward interval, maximum drought, duplicate conversion, choice frequency.
- Difficulty: first clear, learned clear, fail margin, retry time, failure-cause mix.
- PvP: expected match quality, match length, queue budget, side advantage, rating confidence.
- Live ops: event completion time, currency surplus, catch-up, season-end distribution.

Allocate budgets before individual numbers. Examples:

```text
boss_ehp_budget = party_effective_dps * target_damage_uptime * target_duration
upgrade_price_budget = spendable_income_per_day * target_days_per_upgrade
season_points_budget = target_active_days * target_points_per_active_day
```

Reserve budget for variance, mechanics, downtime, mistakes, and optional strategies. Do not spend 100% of a theoretical maximum on the reference path.

## 7. Top-Down And Bottom-Up Reconciliation

Use both directions:

1. **Top-down**: start from experience anchors and allocate system budgets.
2. **Bottom-up**: calculate actual output from legal builds, actions, tables, and schedules.
3. **Reconcile**: change source parameters or the experience anchor; do not hide disagreement with ad hoc content multipliers.

Example:

```text
Top-down boss EHP = 90 seconds * 1,000 effective party DPS = 90,000
Bottom-up boss EHP after phases and adds = 108,000
```

Resolve the 20% gap by changing duration, uptime, phase budget, or source stats. Do not silently assume players produce impossible DPS.

Perform reconciliation at early, middle, late, cap, low-power, reference, and high-power points.

## 8. Evidence, Confidence, And Assumptions

Label values:

- `Observed`: measured from versioned source data or telemetry.
- `Assumed`: necessary working hypothesis not yet measured.
- `Derived`: deterministic result of declared inputs and formula.
- `Recommended`: design decision proposed for testing.

For each assumption, record impact, confidence, and the cheapest test that could invalidate it. Use wide ranges when uncertainty is high. Tighten only after evidence.

When using benchmarks, distinguish transferable structure from title-specific values. Version and cite live-game facts. Use `game-remake-research` before treating reverse-engineered values as confirmed.

## 9. Common Failure Patterns

- Choosing a growth curve before defining target time and power cadence.
- Treating content difficulty as enemy HP alone.
- Modeling perfect play while targeting ordinary players.
- Balancing a stat or item globally when its value is contextual.
- Using expected value while ignoring drought, burst, or wealth tails.
- Mixing earned skill, persistent power, knowledge, and payment into one segment.
- Fixing economy surplus with a punitive universal sink instead of tracing sources and goals.
- Fixing a high PvP win rate without controlling for player strength and selection.
- Adding more knobs when existing source ownership is unclear.
- Tuning retention directly rather than repairing the decision, pacing, clarity, or trust mechanism.
