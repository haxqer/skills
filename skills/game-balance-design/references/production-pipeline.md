# Production Pipeline

Use this reference to turn numerical design into maintainable spreadsheets, schemas, generated configs, validators, migrations, review, and live tuning.

## Contents

1. Artifact architecture
2. Parameter registry and schemas
3. Spreadsheet engineering
4. Derived tables and config generation
5. Validation and golden cases
6. Runtime configuration and authority
7. Versioning, migration, and compensation
8. Change workflow and ownership
9. Observability and audit trail
10. Handoff checklist

## 1. Artifact Architecture

Maintain one source of truth for each tunable. A practical pack contains:

```text
balance/
  brief-and-targets.md
  formulas.md
  parameters.csv
  content-curves.csv
  scenario-matrix.csv
  economy-ledger.csv
  reward-tables.csv
  telemetry-catalog.csv
  generated-config/
  tests/
```

These names are illustrative; follow the project structure. Keep authored source separate from generated output and runtime observations.

Classify artifacts:

- **Authored**: targets, source parameters, table membership, legal ranges, ownership.
- **Derived**: calculated stats, level rows, final odds, display summaries.
- **Generated**: engine/server/client config produced from authored and derived data.
- **Observed**: telemetry, playtest, experiment, and simulation outputs.

Do not edit generated output by hand. Regenerate it from source.

## 2. Parameter Registry And Schemas

Give every tunable a stable ID. Include:

```text
id, system, meaning, value, unit, value_type, clock,
minimum, maximum, step, default, source_status, owner,
formula_group, dependencies, server_authority, hot_reload,
introduced_version, deprecated_version, notes
```

Use explicit types and units. Distinguish integer, fixed-point, float, decimal probability, percentage points, enum, duration, timestamp, and currency minor units.

For content tables, use stable foreign keys rather than display names. Validate referential integrity and uniqueness.

For formulas, version the formula group separately from parameter values. A value-only rollback cannot restore behavior after calculation order changes.

## 3. Spreadsheet Engineering

Use spreadsheets for authoring and inspection, not as an unversioned runtime database.

Structure sheets:

- Inputs with clear ownership and editable formatting.
- Derived calculations protected from manual changes.
- Scenario cases and expected outputs.
- Charts for value, difference, relative growth, and cumulative total.
- Export views with stable column order and machine-readable values.

Avoid:

- Hard-coded constants buried inside many formulas.
- Merged cells, hidden rows as logic, color as the only meaning, or locale-dependent numbers.
- Copy/pasted formulas that drift by row.
- Volatile random functions for final exported config.
- Display rounding feeding later calculations.
- Circular references without an explicit iterative model.

Add data validation, named inputs, protected derived cells, formula consistency checks, and export hashes. Store probabilities as decimals and currency as integer minor units where possible.

## 4. Derived Tables And Config Generation

Generate repeated values from source parameters:

- Level/XP and cost curves.
- Player, item, enemy, and content tiers.
- Final reward probabilities after filters.
- Derived combat stats and tooltip values.
- Event schedules and caps.

The generation step should:

1. Parse and type-check source data.
2. Validate IDs, units, ranges, and references.
3. Calculate in one declared order.
4. Apply caps and rounding once at declared stages.
5. Emit deterministic output with stable ordering.
6. Produce a change summary and content hash.

Use the same formula library for tools and runtime when feasible. If implementations differ, maintain golden cases across languages/platforms.

Do not generate client-visible secret data such as undiscovered content or server-only anti-abuse thresholds into public config.

## 5. Validation And Golden Cases

Create validators for:

- Required fields, types, units, range, uniqueness, and foreign keys.
- Probability normalization and fallback pools.
- Monotonicity or intended piecewise exceptions.
- Cumulative cost/time/reward limits.
- Maximum stack and overflow.
- Economy cycles and legal flow envelopes.
- Content coverage and missing references.
- Runtime/client display parity.

Maintain golden cases with exact inputs, formula version, and expected outputs. Cover:

- Ordinary reference case.
- Zero, one, cap, minimum, maximum, and invalid state.
- Rounding boundary and discrete breakpoint.
- Simultaneous effects and order of operations.
- Reset, reconnect, duplicate transaction, and migration.

Fail generation on invalid data. Warnings need owners and explicit acceptance; do not accumulate ignored warnings.

## 6. Runtime Configuration And Authority

Classify tunables:

- Build-time only.
- Server-start configuration.
- Safe hot reload.
- Per-match/instance snapshot.
- Experiment override.

Snapshot one config version for an encounter, run, match, transaction, or reward roll. Do not change rules mid-resolution unless explicitly designed.

Use server authority for currencies, rewards, progression, competitive results, and anti-abuse. Client values may support preview and display but must not authorize mutation.

Define missing-config, stale-client, invalid-version, partial-deploy, and rollback behavior. Prefer fail-closed for high-value transactions and safe defaults for non-critical presentation.

## 7. Versioning, Migration, And Compensation

Version:

- Formula set.
- Parameter/config bundle.
- Content table.
- Economy/reward table.
- Experiment assignment.
- Telemetry schema.

For every live change, specify:

- Effective time and in-progress instance behavior.
- Existing inventory, progress, pity, rating, quest, and market treatment.
- Forward and backward compatibility.
- Migration script or lazy migration.
- Idempotency and restart behavior.
- Compensation eligibility, value, claim, and expiry.
- Rollback feasibility after new state has been created.

Test migrations on representative and adversarial snapshots. Verify totals before and after. Do not erase player investment silently.

## 8. Change Workflow And Ownership

Use this review sequence:

1. State target, cohort, baseline, mechanism, and guardrails.
2. Change source parameters or formula version.
3. Regenerate derived tables and config.
4. Review diff and blast radius.
5. Run validators, golden cases, scenarios, and simulation.
6. Review design, engineering, analytics, economy/security, QA, and legal/platform where relevant.
7. Approve rollout, monitoring, migration, compensation, and rollback.
8. Tag the released bundle and retain evidence.

Record owner and approver per system. Shared high-blast-radius parameters need explicit cross-system review.

Avoid spreadsheet attachments or chat values as final authority. Link decisions to versioned source.

## 9. Observability And Audit Trail

Every outcome needed for tuning should carry relevant versions and stable IDs. Record:

- Config/formula/content/experiment version.
- Player state snapshot or cohort features used by the model.
- Input values, calculation path where feasible, and final output.
- Transaction or encounter correlation ID.
- Migration and compensation reason.

Keep a deploy manifest containing source hash, generated hash, validator result, scenario suite result, approvers, exposure, and rollback target.

Monitor config load failures, version mismatch, invalid table fallback, reconciliation delta, impossible values, and telemetry schema drift.

## 10. Handoff Checklist

- Ensure stable IDs, units, types, clocks, ranges, owners, and dependencies exist.
- Ensure formulas define order, caps, stacking, rounding, and examples.
- Ensure authored, derived, generated, and observed artifacts are separated.
- Ensure validators and golden cases cover boundaries and exploits.
- Ensure client/server and spreadsheet/runtime parity is tested.
- Ensure configs are deterministic, versioned, snapshot, and auditable.
- Ensure migrations, compensation, and rollback handle existing state.
- Ensure telemetry carries config and formula versions.
- Ensure the team can regenerate the shipped values without manual reconstruction.
