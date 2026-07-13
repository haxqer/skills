# Progression And Content

Use this reference for XP, levels, power growth, gear, affixes, upgrades, enhancement, unlocks, catch-up, prestige, seasons, and content requirements.

## Contents

1. Progression contract
2. XP and level pacing
3. Power architecture
4. Gear tiers, item level, and rarity
5. Affixes, sets, and sockets
6. Upgrade and enhancement systems
7. Content requirements and difficulty bands
8. Unlocks, collections, and horizontal growth
9. Catch-up, returning players, and resets
10. Content lifespan and obsolescence
11. Progression validation

## 1. Progression Contract

Define what progression changes:

- Numerical power, available verbs, build breadth, convenience, status, collection, or access.
- Player decisions now versus future planning.
- Permanent, seasonal, run-based, match-based, or temporary state.
- Expected time horizon and content consumed while progressing.
- Minimum, median, optimized, and capped acquisition paths.

Separate progression types:

- **Vertical**: larger numbers or stronger capabilities.
- **Horizontal**: more options with contextual tradeoffs.
- **Mastery**: player knowledge or execution.
- **Access**: content, modes, features, or social roles.
- **Prestige**: status without required power.

Avoid presenting a mastery problem as vertical progression or making earlier decisions irrelevant after every tier.

## 2. XP And Level Pacing

Derive XP requirements from target time and observed earning rate:

```text
xp_required(level) = target_minutes(level) * reference_xp_per_minute(level)
cumulative_xp(L) = sum(xp_required(level), start..L-1)
```

Choose the curve after defining target minutes, sessions, and content per level. Model:

- Main path, side path, repeatable/farm, social, event, and catch-up XP.
- Active time, queue/travel time, failure time, and offline/calendar gates.
- New, regular, optimized, returning, and group players.
- Early unlock cadence, midgame routine, late mastery, and cap transition.

Check XP rate changes caused by power growth. If stronger players clear faster, a fixed per-kill reward can create accelerating level speed even when the XP table rises.

Do not rely on averages that mix players who stop, cap, boost, or play event content. Use time-to-level distributions among eligible active players.

## 3. Power Architecture

Decompose player power:

```text
player_power_state = {
  base_and_level,
  gear,
  skills,
  collection,
  temporary_buffs,
  team_synergy,
  execution,
  encounter_fit
}
```

Keep execution and encounter fit outside persistent power score when possible.

Avoid uncontrolled multiplication. Prefer a declared hierarchy such as:

```text
base_stat = level_base + allocated_stats
gear_added = sum(item_stats)
pre_multiplier = base_stat + gear_added
final_stat = pre_multiplier * progression_multiplier * temporary_multiplier
```

Cap or group multiplicative systems deliberately. Test all maximum legal combinations.

Track power contribution share by system and stage. If one layer supplies 80% of late-game power, other progression layers may become decorative. If too many layers each multiply, returning-player gaps can explode.

## 4. Gear Tiers, Item Level, And Rarity

Create an item budget at a declared combat anchor:

```text
item_budget(item_level, slot) = base_budget(item_level) * slot_multiplier
rarity_budget = item_budget * rarity_multiplier
```

Use rarity to control budget, affix count, reliability, uniqueness, or acquisition difficulty. Do not assume rarity alone justifies competitive imbalance.

Define:

- Slot budget and slot scarcity.
- Primary versus secondary stat allocation.
- Required baseline stats versus optional affixes.
- Minimum/maximum roll, distribution, precision, and reroll rules.
- Bind, trade, salvage, duplicate, upgrade, and obsolescence behavior.
- Displayed item score and what it intentionally excludes.

Validate item-score weights around multiple builds and encounters. A score that ranks one role correctly can mislead another.

Use tier gaps that support the desired replacement cadence. Measure probability and time to a useful replacement, not merely time to any higher-rarity drop.

## 5. Affixes, Sets, And Sockets

For each affix, record:

`id | family | eligible slots | tier | range | local budget weight | tags | exclusivity | cap | proc rules`

Separate additive stat affixes, conditional multipliers, procs, utility, and build-enabling effects. Conditional effects need an assumed uptime and trigger policy:

```text
expected_proc_value = proc_effect * proc_probability * trigger_rate * useful_uptime
```

Test proc cooldown, multi-hit triggers, area triggers, pets/summons, snapshotting, refresh, simultaneous targets, and maximum trigger rate.

For sets, price the opportunity cost of occupying multiple slots. Test partial sets, full sets, mixed sets, and whether one set becomes mandatory for a role.

For sockets, account for socket availability, gem acquisition, removal cost, reuse, and the option value of flexibility. A flexible socket can be worth more than the inserted stat.

## 6. Upgrade And Enhancement Systems

Define each step's:

- Cost by currency/material and source.
- Success probability, pity, guarantee, and displayed odds.
- Failure outcome: no change, durability loss, downgrade, destruction, or protection item.
- Maximum attempts, expected attempts, p50/p90/p99 cost, and time.
- Transfer, refund, inheritance, reset, and migration behavior.

Expected material cost is insufficient when the failure tail can destroy weeks of progress. Report the full exposure and bound high-stakes RNG.

For deterministic upgrades:

```text
upgrade_interval = upgrade_cost / spendable_income_rate
power_per_day = relative_power_gain / upgrade_interval
```

For an upgrade sequence, calculate cumulative cost and cumulative power. Keep meaningful gain per interval within the intended cadence; small upgrades can feel dead even when their total is correct.

For prestige or rebirth:

```text
payback_time = time_to_recover_previous_frontier
prestige_gain = new_long_run_rate / old_long_run_rate - 1
```

Set a target payback and verify the reset creates new decisions rather than replaying an unchanged script.

## 7. Content Requirements And Difficulty Bands

Create content bands against player-state distributions, not a single required score:

| Band | Player state | Intended outcome |
| --- | --- | --- |
| Entry | Minimum legal with correct policy | Possible but demanding |
| Reference | Expected power and core execution | Target experience |
| High | High legal power or expert execution | Faster/safer, not mechanically broken |
| Overcap | Maximum stack | No exploit, lock, or reward collapse |

Separate hard eligibility from soft recommendation. If using a power score, verify it predicts the relevant outcome across roles and builds; otherwise show component requirements.

Map player power and content pressure over time. Check:

- Power ratio and clear probability by stage.
- Failure cause: knowledge, execution, build, resource, or stat.
- Content skipped by overleveling and walls requiring unrelated grind.
- Reward usefulness when content becomes farmable.
- Group carry, boosting, and low-level participation rules.

## 8. Unlocks, Collections, And Horizontal Growth

Schedule new verbs early enough to teach them before combining them. Avoid unlocking many interdependent systems simultaneously.

For horizontal options, measure:

- Time to first viable build and time to intended build breadth.
- Acquisition overlap and duplicate conversion.
- Respec, loadout, experimentation, and failure cost.
- Context coverage, dominance, and collection pressure.

Collection bonuses create hidden vertical power. Budget their cumulative maximum, returning-player gap, and competitive effect. Keep cosmetics/status separate when power is not intended.

## 9. Catch-Up, Returning Players, And Resets

Define a catch-up target:

`A returning player absent for X days reaches Y% of current reference power in Z active days without invalidating current-player investment.`

Use mechanisms such as accelerated obsolete tiers, targeted drops, rested rewards, boosted first clears, deterministic choice, or temporary access. Avoid raw currency grants that destabilize unrelated systems.

For seasons and resets, specify:

- What resets, persists, converts, expires, or compensates.
- Start-state compression and end-state spread.
- Placement/rating reset separately from power reset.
- Returning and late-joiner paths.
- Inventory and claim behavior at the boundary.

Simulate players joining at several dates, skipping weeks, and returning near season end.

## 10. Content Lifespan And Obsolescence

Track how progression affects content and rewards:

- Time until a tier is replaced.
- Fraction of drops that remain useful.
- Old content participation after rewards lose power value.
- Power compression or stat squish requirements.
- Cost of maintaining many obsolete currencies, materials, and recipes.

Use horizontal rewards, evergreen utility, collection, or conversion when old content should remain relevant. Do not preserve participation through mandatory chores alone.

## 11. Progression Validation

Simulate at least:

- New regular, optimized, intermittent, returning, and late-start players.
- Minimum, median, p90, and capped earning rates.
- Buy-now, save-for-goal, completionist, and experimental policies.
- Zero stock, typical stock, hoarded stock, and compensated/migrated stock.
- Early, middle, late, cap, and season boundary.

Report:

- Time and sessions per level, unlock, meaningful upgrade, tier, and cap.
- Cumulative XP, cost, rewards, and active/calendar time.
- Power contribution by system and relative gain per interval.
- Useful-drop/replacement rate and build breadth.
- Catch-up and payback time.
- Failure tails, dead zones, and obsolescence.

Reject curves that meet median time while producing unacceptable tails, mandatory optimization, runaway gaps, or long stretches without a meaningful decision.
