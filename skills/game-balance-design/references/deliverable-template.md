# Balance Deliverable Template

Use this template for an implementation-ready design, audit, or live patch. Omit systems that do not exist, but never omit assumptions, formula ownership, validation, and rollback for live changes.

## Contents

1. Choose deliverable depth
2. Decision brief
3. Experience targets
4. Player and policy models
5. System architecture
6. Formula specification
7. Parameter registry
8. Curves and content bands
9. Domain ledgers
10. Scenario and simulation results
11. Audit findings or recommended changes
12. Validation and telemetry
13. Production, rollout, and migration
14. Risks and open decisions

## 1. Choose Deliverable Depth

Use a lean response for one decision:

1. Facts and assumptions.
2. Target and guardrails.
3. Formula/breakpoint.
4. Recommended values and safe range.
5. Scenarios and predicted movement.
6. Validation and rollback.

Use a full pack for a system or game:

```text
00-brief-and-targets.md
01-player-and-system-model.md
02-formulas.md
parameters.csv
content-curves.csv
scenario-matrix.csv
economy-ledger.csv          # when applicable
reward-tables.csv           # when applicable
telemetry-catalog.csv
validation-and-rollout.md
```

Use project-native names and formats when they already exist.

## 2. Decision Brief

- Product/mode/content:
- Build/version/platform/region:
- Lifecycle stage:
- Assignment: Create / Audit / Rebalance / Operate
- Decision this enables:
- In scope / out of scope:
- Primary loop and secondary loops:
- Audience and session context:
- Competitive and monetization contract:
- Technical/runtime constraints:

### Evidence Ledger

| ID | Value/claim | Status | Source/version | Confidence | Impact if wrong | Validation |
| --- | --- | --- | --- | --- | --- | --- |

Use only `Observed`, `Assumed`, `Derived`, or `Recommended` as status.

## 3. Experience Targets

| ID | Cohort | Eligibility/state | Intended decision | Metric/distribution | Baseline | Target band | Attempt/time | Guardrail | Rationale |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |

Describe the intended emotional cadence, learning signal, acceptable failure margin, recovery, and what changes from first exposure to mastery.

Reject targets without a denominator or context.

## 4. Player And Policy Models

| Profile | Execution | Knowledge | Power/access | Resources | Time pattern | Intent | Policy/error model |
| --- | --- | --- | --- | --- | --- | --- | --- |

Include minimum legal, reference, high legal, novice, core, expert, blind, learned, regular, intermittent, optimizer, returning, and adversarial profiles that apply.

State how policies change after feedback, failure, affordability, or opponent information.

## 5. System Architecture

Show:

```text
source tunables -> derived state -> offers/constraints -> player policy -> outcome -> telemetry
```

List:

- Stocks, flows, state machines, and clocks.
- Positive/negative feedback loops.
- Multiplicative stacks and high-blast-radius parameters.
- Irreversible player state and reset boundaries.
- Server/client authority and config snapshot boundary.

### Dependency Registry

| Source ID | Derived/output ID | Formula/version | Clock | Owner | Blast radius | Regeneration/test |
| --- | --- | --- | --- | --- | --- | --- |

## 6. Formula Specification

For every formula include:

- Formula ID/version and purpose.
- Inputs, types, units, clocks, and legal ranges.
- Exact operation order.
- Additive/multiplicative grouping.
- Caps, floors, stacking, and state transitions.
- Integer/fixed-point/float precision and rounding stage.
- RNG distribution, seed, and independence/correlation.
- Worked ordinary and boundary examples.
- Runtime/tool/spreadsheet implementation owner.

### Formula Table

| Formula ID | Expression/order | Inputs | Output/unit | Caps/rounding | Example | Tests |
| --- | --- | --- | --- | --- | --- | --- |

## 7. Parameter Registry

| ID | System | Meaning | Current | Recommended | Safe range | Step | Type/unit/clock | Status | Owner | Dependencies | Player-facing effect |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |

Separate source parameters from generated values. Mark hot-reload, server authority, introduced version, migration, and deprecation when relevant.

Use `assets/templates/parameter-registry.csv` as a starting schema.

## 8. Curves And Content Bands

| Stage/tier | Reference profile | Source inputs | Player power/rate | Content pressure/cost | Reward | Active/calendar time | Cumulative total | Intended job |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

Include early, middle, late, cap, minimum, reference, and high legal rows. Show value, first difference, relative difference, and cumulative total for important curves.

Attach generated config/CSV for large tables and state the source formula/version.

## 9. Domain Ledgers

Include applicable ledgers.

### Combat/Encounter

| Entity/action | Role | EHP | Burst | Sustain | Control/resource | Timing | Counter | Budget |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |

### Progression

| Goal/step | Requirement | Cost | Reward/power | Interval | Cumulative | Access | Catch-up/reset |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |

### Economy

| Stock | Source/sink/exchange | Amount/rate | Cadence | Eligibility | Cap | Cohort share | Transaction ID/reason |
| --- | --- | ---: | --- | --- | ---: | ---: | --- |

### Rewards

| Table/stage | Outcome | Eligibility | Weight/final probability | Utility | Duplicate | Pity/reset | Maximum exposure |
| --- | --- | --- | ---: | ---: | --- | --- | --- |

### PvP

| Option/map/side | Availability | Pick | Conditional lift | Matchups | Skill curve | Counter access | Confidence |
| --- | --- | ---: | ---: | --- | --- | --- | --- |

## 10. Scenario And Simulation Results

| Scenario ID | Profile/policy | Build/access | State/content | Seed/matchup | Expected behavior | Result distribution | Margin/tail | Guardrail | Pass? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Report model type, horizon, sample count, seeds, policy distribution, correlations, omissions, mean/median, relevant percentiles, confidence, and sensitivity.

Call out breakpoints, maximum stacks, feedback loops, degenerate strategies, and unacceptable tails.

## 11. Audit Findings Or Recommended Changes

For audits, order by player impact and confidence:

| Priority | Finding | Evidence | Mechanism | Cohorts | Recommendation | Predicted movement | Side effects | Confidence | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

For greenfield design, replace `Finding` with `Decision` and show alternatives considered.

Prefer the smallest coherent change. Explain interactions and ordering.

## 12. Validation And Telemetry

- Static/schema validators:
- Invariants and golden cases:
- Simulation scenarios and policies:
- Playtest cohorts/tasks/questions:
- Required events/properties/versions:
- Data-quality and reconciliation checks:
- Primary metric and practical effect:
- Guardrails, stop, and rollback thresholds:
- Minimum sample/duration and unit of analysis:

### Telemetry Catalog

| Event | Trigger | Required properties | Config/formula version | Sampling | Retention | Metric/diagnosis |
| --- | --- | --- | --- | --- | --- | --- |

## 13. Production, Rollout, And Migration

- Authored source and generated outputs:
- Config/formula/content version:
- Snapshot and hot-reload boundary:
- Client/server parity tests:
- Diff and approvers:
- Exposure stages:
- Existing inventory/progress/pity/rating/market behavior:
- Migration and idempotency:
- Respec/refund/compensation:
- Rollback target and created-state handling:
- Monitoring owner and response time:

## 14. Risks And Open Decisions

| Risk/unknown | Probability | Impact | Evidence needed | Cheapest next test | Owner | Decision deadline |
| --- | ---: | ---: | --- | --- | --- | --- |

End with the highest-risk assumption and what would disprove the model. Do not hide uncertainty inside exact-looking values.

## Completeness Gate

- Targets name cohort, state, distribution, time/attempt, and guardrail.
- Player models separate skill, knowledge, power, resources, time, and payment/access.
- Formula order, units, caps, stacking, rounding, and examples are complete.
- Source parameters regenerate curves and runtime config.
- Cumulative totals, tails, breakpoints, feedback loops, and exploits are tested.
- Existing player state has migration and compensation behavior.
- Telemetry distinguishes eligibility, exposure, choice, result, repeat, and abandonment.
- Rollout has practical success, guardrail, stop, and rollback thresholds.
