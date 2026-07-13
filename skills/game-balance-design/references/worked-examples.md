# Worked Examples

Use these examples to see the expected reasoning shape. Treat values as demonstrations, not universal targets.

## Contents

1. Learnable boss gate
2. XP curve derived from time
3. Item and affix budget
4. Multi-cohort economy diagnosis
5. Pity and duplicate protection
6. PvP breakpoint patch

## 1. Learnable Boss Gate

Given a core party with `1,800` damage per round and eight player action phases, design a gate where missing one telegraphed mechanic causes a narrow failure.

Assume:

- Correct response costs 25% of round-4 damage.
- Incorrect response heals the boss for `3,000` and reduces rounds 5-8 damage to 75%.

Correct damage:

```text
7 * 1,800 + 0.75 * 1,800 = 13,950
```

Incorrect effective damage against original HP:

```text
4 * 1,800 + 4 * 0.75 * 1,800 - 3,000 = 9,600
```

Choose boss HP near `10,400`. Incorrect core play loses with `800 HP` remaining (`7.7%`), while correct play clears. Then verify survivability, action order, novice/expert bypass, mechanic recognition, and learned-clear behavior. Arithmetic creates the margin; playtests determine whether it teaches.

## 2. XP Curve Derived From Time

Target level times:

| Phase | Target minutes/level | Reference XP/min |
| --- | ---: | ---: |
| Levels 1-5 | 8 | 100 |
| Levels 6-15 | 20 | 140 |
| Levels 16-20 | 45 | 180 |

Derive:

```text
xp_required = target_minutes * xp_per_minute
```

This gives phase anchors of `800`, `2,800`, and `8,100 XP` per level. Interpolate or author within phases, then calculate cumulative XP and actual time for main-path, side-content, optimized, and intermittent policies.

Do not start with `XP = 100 * 1.2^level`; that curve has no guarantee of producing the intended time after earning rates change.

## 3. Item And Affix Budget

Suppose a level-20 two-handed weapon has a local budget of `100 points`. At the reference encounter, marginal testing estimates:

| Stat | Amount per point |
| --- | ---: |
| Attack | 1.0 |
| Crit chance | 0.08 percentage points |
| Cooldown reduction | 0.05 percentage points |

A rare weapon receives a `1.2` rarity multiplier, giving `120 points`. Reserve `80` for required base attack and `40` for affixes.

Candidate A spends all `40` on attack. Candidate B spends `20` on attack and `20` on crit. Do not declare them equal from points alone. Recalculate TTK and burst breakpoints for low/reference/high crit builds, then price reliability and build synergy. If crit crosses a kill breakpoint, its local weight is no longer linear.

## 4. Multi-Cohort Economy Diagnosis

Given daily gross income `8k/20k/60k` for novice/core/optimizer and a flat `4k` mandatory sink:

```text
net income = 4k / 16k / 56k
sink burden = 50% / 20% / 6.7%
```

A `70k` first upgrade takes `17.5 / 4.38 / 1.25` days. If the core target is one upgrade every two days, the current price misses before any growth curve is considered.

Set early core prices near `2 * 16k = 32k`, then author a target interval curve. If price rises 12% per purchase while income is flat, each interval rises 12%; validate whether that slowdown is intended.

If day-30 p99 stock exceeds the maximum legal flow envelope, stop price tuning and audit opening stock, grants, boosts, duplicate claims, clock exploits, and metric definition.

## 5. Pity And Duplicate Protection

For base chance `p=0.02` and hard pity `N=80`:

```text
expected_attempts = (1 - 0.98^80) / 0.02 = 40.07
P(drop by 50) = 1 - 0.98^50 = 63.58%
maximum_attempts = 80
```

The mean alone does not describe cost. Report p50, p90, maximum, and real/earned cost.

If the target has four possible featured items and duplicates are allowed, a rarity guarantee does not guarantee the desired item. Specify featured split, target selection, duplicate conversion, and whether pity carries across banners. Simulate nearly complete collections, where nominal rare rate can remain stable while useful utility collapses.

## 6. PvP Breakpoint Patch

In a `100 HP` shooter, a weapon dealing `55` body damage always kills in two landed hits. Lowering damage to `50` changes no fresh-target breakpoint; lowering to `49` makes body-body deal `98` but may preserve two-hit kills for expert headshot users.

If the weapon is disproportionately strong for experts because an eight-round magazine permits four fresh-target kills, reducing magazine `8 -> 7` removes the four-kill breakpoint while preserving first-duel TTK and weapon identity.

Before shipping:

- Control win lift for player rating, option mastery, map, input, latency, party, and composition.
- Simulate accuracy bands and chipped targets.
- Predict substitution to other weapons.
- Set success/rollback for top-cohort conditional lift, core performance, pick rate, and forced-reload deaths.

The example illustrates mechanism-first tuning: change the breakpoint causing expert chain value, not a stat that mainly hurts lower-skill users.
