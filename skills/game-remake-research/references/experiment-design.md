# Experiment Design

## Contents

- `Purpose`
- `Core Experiment Types`
- `Working Rules`
- `Minimal CSV Workflow`
- `Anti-Patterns`

Use this reference when research needs disciplined sampling instead of narrative-only notes.

## Purpose

A remake pack gets stronger when evidence is reproducible. Use experiments to turn claims such as:

- "combat feels snappy"
- "the economy is grindy"
- "the onboarding is smooth"
- "the run has good pacing"

into measurements that can be reviewed, challenged, and iterated.

## Core Experiment Types

### Timing Capture

Use for action timing, anticipation, active windows, recovery, interrupts, and cancels.

- Best for: MMO combat classes, ARPG skills, roguelike combat verbs.
- Unit: `frames-or-ms`
- Common sample: `3-10 representative actions`

### Route And Density Sample

Use for representative farming or traversal routes.

- Best for: MMO and ARPG
- Unit: `minutes-and-enemies`
- Common sample: `3 representative routes`

### Faucet And Sink Sample

Use for economy health across currencies, materials, and mandatory friction.

- Best for: all archetypes
- Unit: `currency-plus-items`
- Common sample: `10-30 observations`

### Progression Band Mapping

Use for pacing and system unlock structure.

- Best for: all archetypes
- Unit: `bands-or-stages`
- Common sample: full onboarding through endgame pass

### Onboarding Funnel Observation

Use for first-session structure and friction.

- Best for: all archetypes
- Unit: `steps-and-minutes`
- Common sample: first `10-60` minutes

### UI Flow Step Count

Use for inventory, upgrade, deckbuilding, matchmaking, crafting, and similar interfaces.

- Best for: all archetypes
- Unit: `steps-per-task`
- Common sample: `5-10 critical tasks`

### Failure-To-Reentry Timing

Use for wipe, defeat, failed run, or lost match restart costs.

- Best for: all archetypes
- Unit: `seconds-to-control`
- Common sample: `3-5 representative failures`

### Encounter Or Match State Log

Use for exact reconstruction of encounter rules, board state changes, or run-state transitions.

- Best for: all archetypes
- Unit: `state-snapshots`
- Common sample: `5-10 representative scenarios`

## Working Rules

1. Lock the region, platform, and version before sampling.
2. Prefer one experiment sheet per claim family.
3. Record source IDs and timestamps with every sample.
4. Separate raw observations from interpretation.
5. Write observed band first, remake target second.

## Minimal CSV Workflow

Use `data/experiment-plan.csv` to define:

- what to measure
- how many samples to collect
- which unit to use
- current status

Use `data/experiment-observations.csv` to log:

- experiment registry
- detail file path
- status
- owner
- last-updated marker

Use typed experiment sheets under `data/experiments/` for raw observations:

- `timing-capture.csv`
- `route-density-sample.csv`
- `economy-sampling.csv`
- `progression-band-map.csv`
- `onboarding-funnel.csv`
- `ui-flow-count.csv`
- `failure-reentry.csv`
- `state-log.csv`

Write raw measurements into the typed sheet first. Use `data/experiment-observations.csv` as the index, not as the raw-measurement dump.

Use `data/archetype-metrics.csv` when the experiment feeds a quantitative archetype baseline.

## Anti-Patterns

- Sampling one clip and treating it as representative.
- Mixing versions or regions in one metric band.
- Writing remake targets before observing the original band.
- Collapsing raw data and interpretation into one statement.
- Treating vague adjectives as evidence.
