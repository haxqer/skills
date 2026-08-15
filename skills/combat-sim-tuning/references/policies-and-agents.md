# Policies And Agents

The policy is the model of the player. It matters more than most stat edits, and it is the
assumption most often left implicit. A win rate is a statement about a policy facing a policy, not
a property of the numbers alone.

## 1. Why The Policy Is The Result

Change nothing but the target-selection rule and the same roster can swing tens of points of win
rate. Focusing the lowest-HP enemy removes damage sources faster than spreading; focusing the
highest-attack enemy removes the largest threat but leaves more bodies alive. Neither is "correct":
they are different players.

So every reported number carries an implicit clause: *under this policy*. Write the clause down.
A report that says "the encounter clears at 55%" without naming the policy is not reproducible and
not actionable.

## 2. Available Policies

Skill selection (`skill_policy` on a unit):

| Policy | Behavior | Models |
| --- | --- | --- |
| `priority` | Highest `priority` among usable skills, declaration order breaks ties | A player following a rotation |
| `max_damage` | Greedy estimate of immediate damage on the chosen target | A player optimizing the next hit only |
| `weighted_random` | Sampled by `weight` | A distribution over an unknown population |
| `cycle` | Round-robin over usable skills | A fixed rotation with no reads |

Target selection (`target_policy` on a unit, overridable per skill):

| Policy | Behavior | Models |
| --- | --- | --- |
| `lowest_hp` | Absolute lowest health | Finishing blows, greedy last-hitting |
| `lowest_hp_pct` | Lowest fraction | Focusing whoever is closest to dying |
| `highest_hp` | Highest health | Spread damage, no focus discipline |
| `highest_atk` | Largest attack stat | Threat assessment |
| `lowest_def` | Softest target | Optimizing damage per action |
| `first` | Declaration order | Deterministic control case |
| `random` | Uniform among living enemies | An unskilled or inattentive player |

`max_damage` is greedy and single-step: it does not evaluate whether saving a cooldown for the next
turn produces more total damage. It is a competent-player floor, not an optimal policy. Do not
present its results as the skill ceiling.

## 3. Building A Policy Ladder

Model skill as a ladder of policies, not as a stat multiplier. Multiplying a stat to represent a
worse player produces a player who is worse at everything uniformly, which no real cohort is.

A workable four-rung ladder:

| Rung | Skill policy | Target policy | Also |
| --- | --- | --- | --- |
| Floor | `weighted_random` | `random` | No cooldown discipline |
| Casual | `cycle` | `highest_hp` | Uses skills, does not focus |
| Core | `priority` | `lowest_hp_pct` | The reference cohort |
| Expert | `max_damage` | `lowest_def` | Optimizes per action |

Run the whole ladder, not just the core rung. The spread between floor and expert win rates is the
skill expression of the encounter. A near-zero spread means execution does not matter, which is a
design finding. A spread of 80 points means the encounter is a skill check, which is fine if
intended and a retention problem if it is a required gate.

Vary policies with `--set`:

```bash
python3 sim_runner.py scenario.json --team party --battles 10000 \
  --set teams.party.0.skill_policy=weighted_random \
  --set teams.party.0.target_policy=random
```

## 4. Cohorts Are Not Just Policies

Skill is one axis. Model these separately and cross them, rather than folding them into one
"player strength" number:

| Axis | Represent as |
| --- | --- |
| Execution | Skill and target policy |
| Available power | `--scale` on stat paths for gear or level tier |
| Composition knowledge | Which units are in the team at all |
| Build knowledge | Skill loadout and priority ordering |

`--scale` multiplies the current value, which is the right tool for a tier shift:

```bash
python3 sim_runner.py scenario.json --team party --battles 10000 \
  --scale teams.party.0.atk=0.85 --scale teams.party.0.hp=0.85
```

Crossing two power tiers with four policy rungs gives eight cells. Run all eight. Balancing only
the on-tier core cell is how an encounter ships that is trivial for the top cohort and impossible
for the bottom one.

## 5. Policy Sensitivity Is A Result, Not A Nuisance

After tuning, re-run the final configuration across the policy ladder and report the spread. Two
patterns deserve explicit callouts:

- **Policy-fragile**: win rate swings widely across rungs. The encounter is measuring execution.
  Correct for optional content, dangerous for a mandatory gate.
- **Policy-flat**: win rate barely moves. Nothing the player does matters; the outcome is decided
  by the stat sheet. This usually reads to players as an unfair or hollow fight even when the win
  rate is exactly on target.

A configuration that only meets its band under one policy has not met its band. Say which rungs it
passes and which it fails.

## 6. What Policies Cannot Represent

- **Learning**: real players change policy across attempts. A fixed policy cannot show the
  first-attempt-to-fifth-attempt curve that difficulty tuning actually cares about. Approximate it
  by reporting the ladder rungs as attempt bands, and label the approximation.
- **Reaction and timing**: no input latency, no missed reactions, no panic.
- **Information**: the modeled agent reads exact HP and stats. Real players read health bars.
- **Adaptation within a fight**: policies do not switch mid-battle unless you implement it.

When a conclusion depends on any of these, it needs a playtest. Naming the gap is part of the
deliverable, not a caveat to bury at the end.
