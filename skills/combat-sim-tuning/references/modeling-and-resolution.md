# Modeling And Resolution

How to turn combat rules into an executable model whose output can be trusted, and the exact
contract the bundled engine implements.

## 1. The Modeling Contract

A simulation is only evidence about the game if the model and the game resolve the same way.
Before running anything, write down and confirm with the implementation owner:

| Decision | Why it changes results |
| --- | --- |
| Calculation order | `(atk * power + flat - def) * crit` and `(atk * power + flat) * crit - def` diverge by the crit multiplier applied to defense |
| Rounding and integer truncation | Truncation at low damage creates breakpoints and dead zones invisible in float math |
| Cap and floor placement | A cap before stacking and a cap after stacking are different systems |
| Stacking rule | Additive `1 + a + b` vs multiplicative `(1+a)(1+b)` changes the value of the second copy |
| Action economy | Round-based, ATB, cast times, and cooldown-on-use vs cooldown-on-ready give different DPS |
| Random source | One roll per action vs one roll per hit changes variance without changing the mean |
| Tie-breaking | Equal speed, simultaneous death, and last-hit credit must be deterministic or results drift |
| Target selection | Focus rules change effective team HP more than most stat edits |

Anything on this list that you assume rather than confirm goes in the assumption ledger with a
validation method. An unconfirmed calculation order is the single most common reason a simulation
disagrees with the build.

## 2. Scenario Schema

`assets/templates/scenario-template.json` is the reference. Top level:

| Field | Default | Meaning |
| --- | --- | --- |
| `max_rounds` | 50 | Hard cap. Reaching it is a `timeout`, reported as a draw |
| `seconds_per_round` | 1.0 | Linear conversion from rounds to seconds for TTK targets |
| `damage_model` | `subtract` | `subtract`, `ratio`, or `multiplicative` |
| `damage_model_params` | `{}` | `min_damage_fraction`, `defense_constant`, `defense_coefficient`, `mitigation_cap` |
| `damage_variance` | 0.0 | Uniform multiplier in `[1-v, 1+v]` applied after crit |
| `teams` | required | Exactly two named teams, each a non-empty list of units |
| `trace` | false | Records a per-action log in the battle record |

Unit fields: `id`, `role`, `count`, `hp`, `atk`, `def`, `speed`, `accuracy`, `dodge`,
`crit_chance`, `crit_mult`, `resource`, `resource_regen`, `skill_policy`, `target_policy`,
`skills`. A unit with no `skills` gets a basic single-target attack at `power` 1.0.

Skill fields: `id`, `type` (`attack`, `heal`, `buff`, `debuff`), `power` (multiplier on `atk`),
`flat`, `hits`, `cooldown`, `cost`, `targets`, `target_policy`, `priority`, `weight`, `status`.

Status fields: `id`, `duration`, `dot`, `dot_power` (fraction of the victim's max HP),
`shield`, `stun`, `stat_mults` (`atk`, `def`, `speed`, `accuracy`, `dodge`, `crit_chance`),
`stack_rule` (`refresh`, `stack`, `ignore`), `max_stacks`.

Validation is strict on purpose: unknown stats, out-of-range probabilities, non-positive HP, and
a team count other than two all raise instead of silently producing a plausible number.

## 3. Mitigation Curves

| Model | Formula | Behavior |
| --- | --- | --- |
| `subtract` | `max(raw * min_damage_fraction, raw - def)` | Flat reduction; high def trivializes small hits, so the floor fraction matters |
| `ratio` | `raw * K / (K + def)` | Constant marginal value of defense in effective-HP terms; `def = K` halves damage |
| `multiplicative` | `raw * (1 - clamp(def * coef, 0, cap))` | Linear reduction to a hard cap; simple to communicate, easy to break past the cap |

Pick by the experience you want, not by convenience. `subtract` produces sharp counters and
breakpoint gameplay. `ratio` makes each point of defense worth a constant amount of effective HP,
which is what most progression curves silently assume. `multiplicative` reads clearly to players
but stops rewarding defense at the cap.

## 4. Resolution Order In The Engine

Per round, all living units act in descending effective speed, tie-broken by `(team, index)` so
the order is deterministic. For each actor, in order:

1. Statuses tick: damage over time is applied, then each status decrements its remaining duration
   and expires at zero. Death from a DoT is credited to no source.
2. Resource regenerates, capped at the unit's maximum.
3. Every skill's cooldown decrements by one.
4. If stunned, the turn ends here.
5. A skill is chosen from those that are off cooldown, affordable, and have a legal target.
6. Targets are resolved, the cost is paid, the cooldown is set to the skill's `cooldown`.
7. Resolution: per hit, accuracy check (`accuracy - target dodge`), then crit, then damage
   variance, then mitigation, then shield absorption, then health.

Consequences worth knowing before you read any output:

- `cooldown: N` means usable every `N + 1` turns, because the decrement happens on the actor's own turn.
- A status applied this round already ticks for units that act later this round.
- Shields absorb before health and are consumed in status order.
- Healing is capped by missing health; the excess is recorded as `overhealing`.
- Damage is credited capped at the target's remaining health; the excess is `overkill`.
- The battle ends the moment one team has no living units, mid-round.

## 5. What The Engine Does Not Model

The engine covers stat-and-skill combat with statuses, resources, cooldowns, and target policies.
It does not model: positioning and range, movement and terrain, area shapes, aggro tables,
summons and pets, multi-phase bosses with scripted transitions, player reaction latency, item use
mid-fight, inventories, cross-battle state, or economies.

When the system under test depends on any of those, extend the engine or write a project-specific
one. Do not approximate a spatial or phase-driven mechanic with a flat stat and present the result
as a measurement of the real encounter. State the omission in the report instead.

Extension points that stay compatible with the rest of the toolchain: add a skill `type`, add a
status field, add a `target_policy`, or add a `skill_policy`. As long as `simulate(scenario, seed)`
stays deterministic and the battle record keeps its shape, the runner, report, search, and diff
tools keep working unchanged.

## 6. Determinism Rules

Determinism is what makes paired comparison, convergence testing, and regression diffing valid.
The engine holds to these rules, and any extension must too:

- All randomness comes from one `random.Random(seed)` per battle. No global RNG, no wall clock.
- Availability checks never consume randomness, so adding an unusable skill cannot shift the
  random stream of every later action.
- Iteration order over units, skills, and statuses is stable.
- `run_batch` sorts records by seed, so worker count never changes the output.

Verify after any engine change: `run_batch(scenario, N, seed)` must be equal across
`workers=1` and `workers>1`, and equal across two calls. `test_sim_tools.py` asserts both.

## 7. Calibration Before Conclusions

A model that has not been checked against the build is a hypothesis. Calibrate in this order:

1. **Arithmetic**: reproduce three hand-computed damage numbers exactly, including rounding.
2. **Deterministic case**: set variance, crit, and dodge to zero and confirm the turn-by-turn
   sequence matches a manual trace. `sim_engine.py --trace` prints it.
3. **Single mechanic**: confirm one status, one cooldown, and one resource curve in isolation.
4. **Whole encounter**: compare simulated TTK and death order against a recorded real fight.
5. **Distribution**: compare the simulated spread of outcomes against telemetry, not just the mean.

Report which of these five steps you actually ran. A model calibrated only at step 1 can still be
wrong about every conclusion that matters.
