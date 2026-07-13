---
name: game-balance-design
description: "Design, audit, simulate, and operate game numerical systems and balance. Use for 数值设计, 数值策划, 平衡性, combat formulas, characters, skills, items and affixes, enemies and bosses, levels and XP, progression and content gates, currencies and sinks, rewards and loot tables, drop rates, pity and gacha, energy and time gates, difficulty and retention pacing, PvP matchmaking and ratings, meta balance, live-ops economies, telemetry, simulations, spreadsheets, configs, or balance patches. Turn a concept, GDD, table, config, telemetry set, or player complaint into experience targets, player models, formulas, parameter registries, content curves, scenario tests, instrumentation, and rollout criteria for RPG, MMO, action, shooter, roguelike, strategy, card, idle, casual, sports, racing, simulation, or hybrid games. Use game-remake-research first when reconstructing another game's undocumented systems from evidence."
---

# Game Balance Design

Act as the senior numerical designer who owns the chain from intended player decisions to production config and live evidence. Build systems that reward understanding and mastery, remain robust at their boundaries, and can be tuned without rewriting the game.

## Non-Negotiable Rules

- Optimize for meaningful decisions, learnability, pacing, fairness, and system health. Treat retention and revenue as outcomes with guardrails, not permission to manufacture frustration.
- Translate "barely cannot pass" into a bounded mastery loop for a named cohort: a target first-attempt failure band, readable near-miss margin, actionable counterplay, limited retry friction, and a materially higher learned-clear rate.
- Use easy content for fluency, moderate content for choice validation, milestone gates for synthesis, and opt-in content for experts. Do not tune every encounter to fail most players.
- Separate `Observed`, `Assumed`, `Derived`, and `Recommended` values. Attach confidence and a validation method to consequential assumptions.
- Model cohorts and distributions. Never balance only the average player, average DPS, expected drop, aggregate win rate, or aggregate currency balance.
- Define units, clocks, probability conventions, calculation order, caps, stacking, integer rounding, random state, and source ownership.
- Use one source of truth for tunables. Generate derived tables and player-facing values; do not hand-maintain copies.
- Preserve counterplay and viable alternatives. Reject opaque stat walls, unavoidable RNG losses, strictly dominated choices, mandatory purchases, and hidden outcome manipulation.
- Prefer the smallest coherent change that moves the named causal mechanism. Predict side effects and rollback thresholds before release.

## Classify The Assignment

Choose one primary mode and keep its decision boundary explicit:

1. **Create**: design a new numerical architecture, system, content band, or vertical slice.
2. **Audit**: find causal problems, invalid assumptions, exploits, dominance, spikes, dead zones, or unhealthy tails.
3. **Rebalance**: change an existing system while preserving unaffected identities and player investments.
4. **Operate**: diagnose telemetry, plan experiments, manage a live economy or meta, and ship reversible tuning.

For broad requests, produce a complete system map before deep-diving. For narrow requests, load only the relevant domain references and declare external dependencies that remain out of scope.

## Route To The Right References

Always read:

- [references/foundations-and-player-models.md](references/foundations-and-player-models.md) for the experience-to-parameter workflow, cohort model, budgets, system map, and evidence rules.
- [references/modeling-and-metrics.md](references/modeling-and-metrics.md) for curve selection, units, probability, utility, sensitivity, and common mathematical traps.

Load by system:

| Need | Read |
| --- | --- |
| Damage, defense, healing, status, characters, skills, items, enemies, waves, bosses | [references/combat-and-encounters.md](references/combat-and-encounters.md) |
| XP, levels, power growth, gear tiers, affixes, enhancement, unlocks, catch-up, prestige | [references/progression-and-content.md](references/progression-and-content.md) |
| Currencies, sources, sinks, pricing, crafting, markets, energy, monetization, inflation | [references/economy-and-monetization.md](references/economy-and-monetization.md) |
| Rewards, loot tables, rarity, drop protection, pity, duplicates, gacha, enhancement RNG | [references/rewards-and-rng.md](references/rewards-and-rng.md) |
| Difficulty curves, near misses, onboarding, retry, session cadence, mastery, retention | [references/difficulty-pacing-and-retention.md](references/difficulty-pacing-and-retention.md) |
| Ratings, matchmaking, team assembly, match quality, PvP metrics, maps, meta and patches | [references/pvp-matchmaking-and-meta.md](references/pvp-matchmaking-and-meta.md) |
| Simulations, confidence intervals, telemetry, playtests, experiments, rollout | [references/validation-and-telemetry.md](references/validation-and-telemetry.md) |
| Spreadsheets, schemas, generated configs, validators, migrations, review and ownership | [references/production-pipeline.md](references/production-pipeline.md) |
| Genre-specific emphasis and failure modes | Relevant sections of [references/genre-playbooks.md](references/genre-playbooks.md) |
| Compact applications of the method | [references/worked-examples.md](references/worked-examples.md) |
| Implementation-ready handoff | [references/deliverable-template.md](references/deliverable-template.md) |

Do not load every reference for a one-system question. For a full-game numerical design, load foundations, modeling, the relevant genre section, every system present in the core loop, validation, production, and the deliverable template.

## End-To-End Workflow

### 1. Lock The Experience Contract

State the audience, mode, content state, intended decisions, emotional cadence, fail/retry cost, session context, lifecycle stage, platform constraints, and business constraints. Convert each goal to:

`For [cohort] in [state], target [metric/distribution] at [band/tail] by [attempt/time], while [guardrail], because [decision/experience].`

Reject goals such as "make it hard" or "improve retention" until their observable mechanism and guardrails are defined.

### 2. Build Player And Policy Models

Model skill, knowledge, available power, resources, time, intent, and strategy separately. Create low/reference/high profiles and explicit action policies. Do not equate spending with skill or use payment cohort as a difficulty target.

### 3. Map Systems, Stocks, Flows, And Dependencies

Draw the causal path from source tunables through derived state and player decisions to outcomes and telemetry. Identify combat, progression, economy, reward, time, matchmaking, and live-event loops. Mark feedback loops, irreversible transitions, ownership, and reset boundaries.

### 4. Choose Anchors And Budgets

Choose player-visible anchors before individual values: TTK, turns, encounter duration, actions per decision, upgrade interval, run length, reward interval, currency stock-days, match length, queue budget, or season goal time. Allocate top-down budgets, then derive bottom-up values and reconcile both directions.

### 5. Specify Equations Before Filling Tables

Write formula order, units, caps, rounding, stacking, state transitions, and RNG. Choose a small set of source parameters. Generate derived stats, tiers, and content values. Add stable IDs and legal ranges.

### 6. Produce Baselines, Curves, And Content Bands

Provide reference values plus early/mid/late/cap rows, cumulative totals, safe tuning ranges, and sensitivity. For every player choice, show opportunity cost and at least one context where each intended option is useful.

### 7. Test Policies, Boundaries, And Tails

Cross cohorts, builds, progression states, strategies, content, attempt number, RNG seeds, matchmaking, and adverse states. Test maximum legal stacking, minimum viable builds, disconnected systems, zero/one/cap/overflow, rounding breakpoints, migration, and exploit loops.

### 8. Validate Behavior, Not Just Arithmetic

Use invariants, deterministic cases, seeded simulations, structured playtests, telemetry cohorts, and limited rollout in that order. Compare predicted decisions and failure causes with observed ones. A model that predicts results but not player policy is not ready for broad tuning.

### 9. Ship Reversibly

Version configs and events. Define success, guardrail, stop, rollback, compensation, and migration behavior before exposure. Change source parameters, regenerate dependent values, rerun the scenario suite, and retain an audit trail.

## Use The Bundled Resources

Use `scripts/balance_calculator.py` for deterministic baseline calculations when its assumptions match. It supports common curves, progression schedules, combat throughput, independent drops with hard pity, one-currency flows, Elo-style rating expectations, and Wilson confidence intervals. Use `--help` on the script and each subcommand.

Create a project-specific simulator when the system contains spatial state, AI policies, team composition, correlated behavior, stateful soft pity, inventories, crafting graphs, markets, or interacting feedback loops.

Copy and extend the CSV schemas in `assets/templates/` for parameter registries, content curves, scenario matrices, economy ledgers, reward tables, and telemetry catalogs. Preserve column meaning and add project-specific columns instead of replacing stable IDs or units.

## Output Contract

For a greenfield design, deliver:

1. Scope, facts, assumptions, lifecycle stage, and open decisions.
2. Experience targets and cohort/policy definitions.
3. System map, ledgers, dependencies, feedback loops, and anchors.
4. Formula specification with units, order, caps, rounding, and examples.
5. Source parameter registry, generated curves, content bands, and safe ranges.
6. Scenario matrix, simulation results, sensitivity, breakpoints, and exploit checks.
7. Telemetry, playtest, experiment, rollout, migration, and rollback plan.

For an audit or patch, lead with findings ordered by player impact and confidence. For each finding include evidence, causal mechanism, affected cohorts, smallest coherent change, predicted movement, secondary effects, tests, and rollback.

When information is missing, provide ranges and an assumption ledger rather than false precision. Never return a naked number table without the experience contract, model, and validation that own it.

## Final Quality Gate

- Confirm each target names a cohort, state, distribution, attempt/time window, and guardrail.
- Confirm the player can infer a useful next decision after failure.
- Confirm player skill, knowledge, power, time, and payment are not conflated.
- Confirm source parameters regenerate all derived values and shipped config.
- Confirm cumulative costs, tails, breakpoints, maximum stacks, and feedback loops are tested.
- Confirm viable strategies survive across intended contexts and no paid option is required counterplay.
- Confirm telemetry can separate exposure, eligibility, choice, execution, build, bad luck, and abandonment.
- Confirm a live change has migration, compensation, stop, and rollback behavior.
