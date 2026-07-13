# Combat And Encounters

Use this reference for combat architecture, characters, skills, items, enemies, waves, bosses, and PvE encounter tuning. Read the PvP reference as well when combat is competitive.

## Contents

1. Combat contract and clocks
2. Damage and hit resolution
3. Offense, burst, and uptime
4. Defense, healing, and recovery
5. Resources, actions, and status effects
6. Character, skill, and item budgets
7. Enemy and wave budgets
8. Boss and mastery-gate design
9. Spatial and real-time pressure
10. Parties, roles, and target selection
11. Combat scenario matrix
12. Acceptance checks

## 1. Combat Contract And Clocks

Define before assigning stats:

- Real-time, tick-based, turn-based, simultaneous, initiative-based, or hybrid resolution.
- Target selection, range, area, collision, line of sight, and valid target state.
- Action start, hit frame, recovery, cancel, cooldown, reload, global cooldown, and queue rules.
- Server/client authority, prediction, rollback, latency compensation, and frame/tick rounding.
- Death, downed, revive, invulnerability, shield, overkill, and simultaneous-lethal rules.
- Resource spend/refund timing and behavior on miss, interrupt, cancel, or target death.

Write one canonical calculation pipeline and use it for simulation, server logic, client preview, tooltips, and tests.

## 2. Damage And Hit Resolution

Specify a complete order. Example only:

```text
base = ability_coefficient * attack + flat_damage
rolled = base * random_roll
critical = rolled * critical_multiplier if critical else rolled
after_flat = max(0, critical - flat_reduction)
after_defense = after_flat * K / (defense + K)
after_modifiers = after_defense * product(vulnerability_groups) * product(reduction_groups)
final = clamp(round_once(after_modifiers), minimum_damage, damage_cap)
```

Do not adopt this order automatically. Decide whether crit, armor, vulnerability, shields, and rounding apply before or after one another.

Common defense model:

```text
damage_reduction = defense / (defense + K)
post_defense_damage = raw_damage * K / (defense + K)
effective_health = hp / (1 - damage_reduction)
```

Choose `K` so the intended defense range has meaningful marginal value. Test negative defense, penetration, shred, and cap order.

Choose an accuracy model intentionally:

- Fixed hit chance for simple readable combat.
- Clamped accuracy-minus-evasion for explicit thresholds.
- Ratio or logistic model for smooth relative scaling.
- Deterministic aim/collision for action games, where observed accuracy belongs in the player model rather than the stat formula.

Define glance, block, parry, dodge, miss, immunity, and critical interactions. Avoid layered binary defenses that produce extreme outcome variance without counterplay.

## 3. Offense, Burst, And Uptime

Expected baseline:

```text
expected_hit_damage = (1 - crit_chance) * normal_damage + crit_chance * crit_damage
expected_dps = attempts_per_second * accuracy * expected_hit_damage * damage_uptime
required_dps = encounter_ehp / available_damage_time
```

Also calculate:

- Damage per landed hit and per input attempt.
- Hits, actions, turns, and magazines to kill.
- Burst in 0.25, 1, 3, 5, and encounter-relevant windows.
- Sustained output after reloads, downtime, resource regeneration, and target transitions.
- Overkill, cleave scaling, target-count scaling, and execute thresholds.
- Low/reference/high execution and correlated miss streaks.

For a repeating attack cycle:

```text
cycle_dps = total_cycle_damage / (active_time + recovery + reload + forced_downtime)
```

Do not buff paper DPS when the real problem is low uptime, unreliable range, target access, or an unfavorable breakpoint.

## 4. Defense, Healing, And Recovery

Model survival as a timeline, not HP alone:

```text
survival_time = effective_health / incoming_sustained_dps
net_pressure = incoming_damage_rate - effective_healing_rate
healing_required = damage_taken - allowed_end_health_loss
```

Check burst survival separately. A build can meet average survival while dying inside one control window.

Value healing by effective, not nominal, output:

```text
effective_heal = min(heal_amount, missing_health)
healing_efficiency = effective_heal / resource_or_action_cost
```

Include overheal, anti-heal, shields, delayed healing, lifesteal, regen, revive, cleanse, mitigation uptime, and healer opportunity cost. Test stalemates and self-sustain loops.

Use recovery windows as encounter budget. If damage is intended to teach avoidance, ensure recovery does not erase every mistake and attrition does not make one early mistake deterministically fatal many minutes later.

## 5. Resources, Actions, And Status Effects

For resource-limited actions:

```text
net_resource_rate = generation_rate - spend_rate
time_to_empty = current_resource / max(spend_rate - generation_rate, epsilon)
sustainable_use_rate = generation_rate / cost_per_use
```

For turn/action economy:

```text
value_per_turn = effect_per_action * usable_actions_per_turn
tempo_swing = own_value_created + opponent_value_denied
```

Model status value through state change:

- Hard control: actions or seconds denied, plus setup value.
- Slow: change in exposure, escape, pursuit, or attack count.
- Vulnerability: extra team damage during actual overlap.
- Displacement: positional and objective value, not distance alone.
- Silence/disarm: probability the denied action would have been used.

Define application, resistance, duration, refresh, stacking, diminishing returns, immunity windows, cleanse, boss rules, and simultaneous resolution. Test permanent control and cooldown-reset loops.

## 6. Character, Skill, And Item Budgets

Preserve identities through capability profiles rather than equal paper output. Evaluate:

```text
[burst, sustain, survival, control, mobility, range, reliability, setup, team_value, economy]
```

Build local stat weights at declared anchors:

```text
weight(stat_i, context) = change_in_target_outcome / change_in_stat_i
spent_budget = sum(stat_amount_i * local_weight_i)
```

Do not reuse one weight table across all levels, roles, or encounters. Recalculate around low/reference/high states and discrete breakpoints.

For skills, specify:

- Target count and selection reliability.
- Coefficient, flat component, hit cadence, duration, cooldown, charges, and resource cost.
- Cast, travel, tell, recovery, interruption, cancel, and counterplay.
- Self-risk, positional requirement, setup, combo dependency, and failure refund.
- PvE/PvP rules if they differ, with the smallest possible rules split.

Price versatility. An option useful in every context should pay in peak output, cost, setup, risk, or availability. Price reliability and range, not only maximum damage.

## 7. Enemy And Wave Budgets

Define enemy roles such as pressure, tank, artillery, controller, support, summoner, assassin, objective threat, or mechanic carrier. Give each role a counter and a readable priority signal.

Budget encounter pressure:

```text
unit_pressure = effective_dps + control_pressure + positional_pressure + objective_pressure
wave_pressure = sum(unit_pressure_i * concurrency_i * active_uptime_i)
```

The terms need not share a universal score. Use them to force explicit accounting, then validate behaviorally.

Set encounter anchors:

- Time to first threat, peak concurrency, safe/recovery windows, and total duration.
- Expected player resource spend and recovery after completion.
- Maximum simultaneous mechanics and target-priority decisions.
- Spawn location, travel time, target access, and composition synergy.

Test waves with enemies arriving early/late, support protected, priority target missed, player resources depleted, and one party member down. Avoid compositions whose difficulty comes only from unreadable overlap.

## 8. Boss And Mastery-Gate Design

Derive the first EHP estimate from effective player output:

```text
boss_ehp = reference_party_dps * target_damage_uptime * target_duration
```

Reserve time for mechanics, movement, adds, transitions, and learning. Calculate each phase separately when uptime or rules change.

For every mechanic, define:

`tell -> decision window -> valid responses -> outcome -> feedback -> next opportunity`

Budget mistakes in lost health, lost actions, lost uptime, resource debt, or objective progress. Decide how many ordinary mistakes and major mistakes the reference cohort may recover from.

For a learnable near miss, target all of:

- Blind and learned clear bands by cohort.
- Attempts-to-first-clear distribution.
- Median and tail failure margin.
- Correct-response clear rate and incorrect-response clear rate.
- Failure-cause mix and player comprehension.
- Retry time and abandonment.

A useful initial milestone hypothesis is 30-50% blind clear for the intended eligible cohort, 60-80% within 3-5 attempts, and median failed margin near 5-15% objective remaining or one to two correct actions. Change these bands for retry cost and audience. Arithmetic cannot guarantee behavior; playtest recognition and adaptation.

Do not make the solution "gain 5% more stats" unless the gate explicitly tests progression. A mastery gate should become easier mainly because the player changes policy.

## 9. Spatial And Real-Time Pressure

Account for:

- Effective range, sight lines, cover, exposure time, movement speed, and arena size.
- Projectile travel, collision size, tracking burden, recoil, spread, and input device.
- Spawn safety, retreat route, flank time, objective distance, and camera visibility.
- Entity density, VFX readability, target occlusion, and performance limits.

Measure damage opportunity rather than nominal DPS:

```text
realized_output = nominal_output * target_access * aim_execution * uptime * survival_uptime
```

Validate on supported frame rates, latency bands, inputs, and accessibility settings.

## 10. Parties, Roles, And Target Selection

Test intended, missing-role, duplicate-role, low-coordination, and optimized compositions. Measure:

- Tank survival and threat/target-control reliability.
- Healing throughput, burst response, cleanse, and mana/resource horizon.
- Damage contribution including buffs, debuffs, and mechanic duties.
- Role substitution and minimum viable composition.
- Coordination tax and whether public groups can discover required behavior.

Avoid mandatory hidden synergies. If role checks are strict, communicate them before commitment and provide recovery or matchmaking support.

Define enemy target selection and threat. Random targeting changes damage variance and mechanic responsibility; deterministic targeting can be exploited. Model both the intended strategy and adversarial manipulation.

## 11. Combat Scenario Matrix

Cross:

- Execution: novice/core/expert.
- Power: minimum/reference/high legal.
- Build: baseline, burst, sustain, control, defensive, unconventional.
- State: full/depleted resources, cooldowns ready/spent, full/chipped health.
- Encounter: single, group, boss, priority target, add phase, adverse overlap.
- RNG: low/reference/high rolls and correlated streaks.
- Attempt: blind, informed, mastered, farm.

Record TTK, survival, resource end state, failure cause, margin, actions taken, and policy change.

## 12. Acceptance Checks

- Verify formula order and client/server parity with golden cases.
- Verify discrete kill/action breakpoints and maximum legal stacks.
- Verify every intended character, skill, or item has a use context and counter.
- Verify low-power correct play and high-power poor play behave as intended.
- Verify mechanics remain readable at peak concurrency and supported performance.
- Verify no infinite control, healing, resource, cooldown, reflect, summon, or on-hit loop.
- Verify boss learning changes outcomes more than hidden grind for mastery gates.
- Verify instrumentation attributes damage, healing, control, mechanics, failure, and config version.
