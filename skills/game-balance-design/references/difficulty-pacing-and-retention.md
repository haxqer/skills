# Difficulty, Pacing, And Retention

Use this reference for challenge curves, onboarding, mastery gates, near misses, retry, session cadence, long-term goals, fatigue, retention diagnosis, and adaptive difficulty.

## Contents

1. Difficulty dimensions
2. Learning and mastery ladder
3. Challenge bands and content jobs
4. Learnable near-miss protocol
5. Difficulty curves and pacing waves
6. Failure, retry, and recovery
7. Session and goal cadence
8. Retention as a diagnostic outcome
9. Dynamic difficulty and assistance
10. Live-ops pacing and fatigue
11. Validation and metrics

## 1. Difficulty Dimensions

Separate the sources of difficulty:

- **Execution**: timing, aim, movement, sequencing, input precision.
- **Knowledge**: rules, tells, counters, priorities, hidden state.
- **Planning**: build, loadout, deck, route, resource allocation.
- **Adaptation**: responding to uncertain offers, opponents, or states.
- **Coordination**: team roles, communication, shared timing.
- **Stat/power**: persistent numerical capability.
- **Endurance**: sustained performance, attrition, and concentration.
- **Information load**: simultaneous signals and decision bandwidth.
- **Punishment**: loss severity, retry time, and recovery cost.

Name the intended dimensions for each content unit. Do not accidentally solve execution with grind, knowledge with untelegraphed death, or planning with one mandatory build.

Difficulty is not only failure probability. Two encounters with equal clear rates can differ in readability, agency, variance, duration, punishment, and learning.

## 2. Learning And Mastery Ladder

Sequence mechanics through:

1. Introduce one rule with low pressure.
2. Practice the rule with variation.
3. Contrast correct and incorrect use.
4. Combine it with a previously learned rule.
5. Test recognition under meaningful pressure.
6. Ask for adaptation or optimization.
7. Remix it for mastery or optional challenge.

Track exposure count, correct response, response time, failure cause, and transfer to later contexts. Do not mark a mechanic learned because the player once survived it through excess power.

Control simultaneous novelty. Adding new enemies, new goals, new resources, new UI, and higher punishment at the same point creates diagnostic ambiguity.

## 3. Challenge Bands And Content Jobs

Use bands as starting hypotheses among eligible attempters:

| Content job | Blind/first clear | Learned/repeat clear | Purpose |
| --- | ---: | ---: | --- |
| Onboarding | 90-98% | 98%+ | Establish controls and rules |
| Fluency/routine | 70-90% | 90-99% | Maintain pace and reward competence |
| Stretch | 45-65% | 70-90% within 2-3 attempts | Make one choice or mechanic matter |
| Milestone mastery | 30-50% | 60-80% within 3-5 attempts | Require synthesis and adaptation |
| Expert opt-in | 5-25% | Define by practice budget | Serve mastery without blocking core progress |

Adjust for audience, genre, retry cost, content duration, social commitment, and failure loss. A 30% clear rate is far harsher in a 30-minute run with permanent loss than in a 60-second boss retry.

Track conditional clear by attempt and cohort, not one population completion metric.

## 4. Learnable Near-Miss Protocol

Design a near miss with six explicit components:

1. **Eligible reference state**: cohort, power, resources, legal build, and policy.
2. **Blind target**: intended first-attempt clear/fail distribution.
3. **Failure margin**: enemy EHP, timer deficit, moves short, objectives missed, or correct actions short.
4. **Causal signal**: the player can identify what happened and a valid next action.
5. **Learning delta**: correct adaptation materially changes the outcome without extra grind.
6. **Attempt budget**: target learned-clear and abandonment by a bounded attempt count.

Useful initial milestone hypotheses:

- Median failed attempt leaves 5-15% objective unresolved or needs one to two correct decisions.
- Correct-response reference players clear at least 85-95% in deterministic content.
- Incorrect-response clear remains low enough that the mechanic matters.
- Retry returns to a meaningful decision quickly and does not present a purchase as the primary correction.

Do not force every failed player into the same margin. A suspiciously narrow repeated margin can indicate a hidden stat check. Analyze the distribution and causes.

Near-miss feedback must be truthful. Do not secretly modify outcomes to fabricate closeness.

## 5. Difficulty Curves And Pacing Waves

Use waves rather than monotonic increase:

```text
introduce -> practice -> combine -> test -> release -> vary -> mastery
```

Map content units by pressure, novelty, complexity, punishment, duration, and reward. Change one or two dimensions at a time so failures remain diagnosable.

Check:

- Local spikes between adjacent units.
- Cumulative fatigue across a session or chapter.
- Back-to-back coordination or precision demands.
- Resource carryover and failure debt.
- Random seed/board variance.
- Difficulty after boosters, assists, overleveling, or optimized strategies.

For procedural content, generate within an authored difficulty envelope and validate solvability, counter availability, and maximum adverse combinations.

## 6. Failure, Retry, And Recovery

Budget total failure cost:

```text
failure_cost = lost_active_time + runback + resource_loss + opportunity_loss + social_cost
```

Higher cost requires higher clarity, agency, and pre-commitment information.

Define checkpoint, resource restore, consumable refund, reconnect, teammate continuation, and abandon behavior. Prevent the player from entering a mathematically unwinnable state without warning or recovery.

Use recovery to preserve learning:

- Fast retry for execution and recognition tests.
- Checkpoint or partial progress for long multi-stage content.
- Respec/loadout access for build tests.
- Practice or lower-stakes mode for coordination.
- Deterministic route around harmful RNG tails.

Do not use lives, energy, or runback primarily to interrupt useful learning.

## 7. Session And Goal Cadence

Layer goals:

- Seconds/minutes: feedback and micro-decisions.
- Session: one meaningful completion, upgrade, discovery, or attempt.
- Daily/weekly: variety and flexible progress, not mandatory chores.
- Chapter/run/tier: medium-term mastery and build formation.
- Season: aspiration, social comparison, collection, or narrative arc.
- Long-term: mastery, identity, creation, competition, or breadth.

Measure active time separately from loading, queue, travel, wait, inventory cleanup, and forced repetition.

Give players stopping points. A session can be compelling without making exit feel like failure. Avoid scheduling that requires unhealthy hours or exact-time attendance to remain viable.

Balance goal overlap so one action can sometimes progress several goals, while no single activity solves the whole game indefinitely.

## 8. Retention As A Diagnostic Outcome

Do not tune retention directly. Diagnose the player mechanism behind a funnel change:

- Comprehension, competence, autonomy, variety, social belonging, aspiration, trust, performance, content supply, or external cadence.
- Difficulty, reward mismatch, retry friction, grind, inventory burden, matchmaking, or technical failure.

Separate:

```text
eligible -> exposed -> attempted -> completed -> repeated -> mastered
```

Compare cohorts and versions. A lower completion rate can reflect optionality; a higher rate can coexist with boredom. Use outcome, behavior, and experience measures together.

Never infer that more time spent is always better. Distinguish active choice from waiting, repeated failure, menu friction, queue time, or forced maintenance.

## 9. Dynamic Difficulty And Assistance

Prefer explicit assists, difficulty selection, accessibility settings, practice, hints, and forgiving checkpoints. Preserve player agency and communicate effects.

If using dynamic difficulty:

- Keep it out of ranked/competitive outcomes unless rules are symmetric and explicit.
- Adapt assistance or content selection, not paid odds or hidden reward value.
- Define signals, minimum sample, adjustment bounds, cooldown, reset, and opt-out.
- Avoid punishing success, invalidating mastery, or fabricating wins/losses.
- Log the applied state and validate each cohort.

Use hints after evidence of misunderstanding, not merely after spending or waiting. Do not secretly weaken a boss while claiming the player overcame unchanged content.

## 10. Live-Ops Pacing And Fatigue

Budget overlapping events across time, difficulty, social obligation, and economy injection. Track:

- Required active/calendar time and exact-time windows.
- Repeated mechanics, modes, and reward types.
- Catch-up, late join, missed day, and rest paths.
- Competition with permanent goals.
- Event stacking and notification burden.

Alternate intensity and preserve unscheduled play. Avoid making every season longer, denser, or more punitive merely to maintain engagement metrics.

Use content reuse transparently and vary decisions, not just enemy HP or reward multipliers.

## 11. Validation And Metrics

Measure by cohort, power, attempt, content, and version:

- Clear, fail, abandon, retry, and attempts-to-clear.
- Failure margin and failure-cause distribution.
- Mechanic exposure, correct response, response time, and learning slope.
- Retry time, runback, resource loss, and session exit after failure.
- Difficulty perception, fairness, confidence, and next-action comprehension.
- Active versus passive/friction time.
- Goal completion, choice diversity, and repeated-play policy.

Playtest without coaching the answer. After failure, ask what the player thinks happened and what they would change. A successful mastery gate produces a plausible next action and improved behavior, not only stated frustration.

Roll back or retune when learned-clear does not improve, correct responses still fail unexpectedly, failure cause is dominated by opaque RNG/stat gaps, or guardrails worsen despite meeting aggregate clear rate.
