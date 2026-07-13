# Genre Playbooks

Select the sections that match the game's actual loops. Use one primary playbook, then add secondary systems that materially change the numerical model.

## Contents

1. RPG, MMO, ARPG, and turn-based games
2. Action, shooter, and fighting games
3. Roguelikes, roguelites, and survivor-likes
4. RTS, 4X, SLG, tactics, and tower defense
5. Card games, deckbuilders, and auto-battlers
6. Idle and incremental games
7. Puzzle, match-3, and casual games
8. Simulation, management, survival, and crafting games
9. Sports and racing games
10. Sandbox, social, and cooperative games
11. PvP and live-service cross-cutting rules
12. Hybrid-game integration

## 1. RPG, MMO, ARPG, And Turn-Based Games

Model first:

- Player power by level, gear, skills, collection, party role, build, and execution.
- Damage, EHP, healing, control, action economy, uptime, and resource horizon.
- Enemy tiers, composition pressure, boss phases, and mechanics budget.
- XP, upgrade cadence, useful-drop rate, tier replacement, and catch-up.
- Solo, group, progression, farm, raid, seasonal, and competitive states separately.

Key targets:

- Turns/seconds and resources per encounter.
- Blind and learned boss clear, fail margin, and mechanic response.
- Power contribution by progression layer.
- Time to viable build, intended build, next tier, and cap.
- Role viability, minimum composition, and coordination burden.

Watch for gear-score cliffs, speed/action breakpoints, mandatory buffs, healing stalemates, permanent control, multiplicative stat stacks, carry/boost exploits, low-value drops, and content invalidated by overleveling.

For MMO/live RPG economies, trace bind/trade, crafting, auction supply, raid lockouts, alt accounts, catch-up, and season/reset value. For turn-based combat, prioritize action economy and initiative over paper DPS. For ARPGs, test density, area scaling, proc cascades, movement, and maximum entity interactions.

## 2. Action, Shooter, And Fighting Games

Model first:

- TTK by range, accuracy, hit location, armor, weapon state, and input cohort.
- Burst, sustained output, reload/recovery, ammo/resource, and exposure time.
- Movement, range, collision, startup/active/recovery frames, cancel windows, and latency.
- Map/arena geometry, spawn, objective access, sight lines, and target concurrency.

Key targets:

- Hits/shots/combos to kill and breakpoint probabilities.
- Time-to-damage, punish window, escape/recovery, and neutral/advantage value.
- Weapon/character role across range, reliability, mobility, setup, and team utility.
- Core versus expert performance and input/platform differences.

For shooters, nominal DPS is secondary to first-shot value, peek exposure, magazine breakpoints, recoil, spread, aim assist, travel, and target access. For fighting games, model frame advantage, damage scaling, meter, guard/stun, combo routes, wakeup, throw/strike risk, and corner value.

Watch for one-frame or one-input deaths, spawn traps, zero-to-death loops, aim-assist cliffs, permanent pressure, safe universal options, animation/frame mismatch, and balance changes that punish novices while preserving expert dominance.

## 3. Roguelikes, Roguelites, And Survivor-Likes

Model first:

- Run power by room/time, offer cadence, rarity, rerolls, and build completion.
- Enemy density, spawn budget, elite cadence, boss checks, arena pressure, and performance.
- Within-run decision power versus meta-progression power.
- Win probability and failure cause by seed, unlock state, archetype, and cohort.

Key targets:

- Probability of receiving at least one viable answer before each check.
- Dead-offer, forced-pick, reroll, build convergence, and pivot rates.
- Power trajectory and pressure trajectory over run time.
- Win/abandon by seed percentile and meta state.

Protect adaptation. A successful build may be rare, but ordinary viability should not require one untelegraphed rare roll unless high variance is the explicit mode.

Watch for early RNG determining the run, meta grind replacing mastery, exponential projectile/proc growth, invulnerability or healing loops, entity/performance collapse, unreadable density, and rewards that favor only already-winning builds.

## 4. RTS, 4X, SLG, Tactics, And Tower Defense

Model first:

- Resource income, production time, build order, action economy, travel, and reinforcement.
- Unit/tower capability and counters by cost, timing, information, position, and execution.
- Territory, objective, research, population, maintenance, logistics, and attrition.
- Advantage conversion, snowball, comeback access, and time-to-effective-decision.

Key targets:

- Payback time for economy/research upgrades.
- Equal-cost and equal-time combat plus realistic staggered engagement.
- Counter access before threat timing.
- First-player/first-mover advantage, map/resource variance, and match duration.
- Time between meaningful strategic decisions.

For 4X/SLG, simulate long horizons, compounding, diplomacy/alliances, protection, server age, whales/strong players, new entrants, offline vulnerability, and season migration. For tactics, test initiative, action denial, terrain, focus fire, and irreversible unit loss. For tower defense, test path length, target logic, area scaling, leak value, and wave composition.

Watch for positive resource loops, dominant openings, turtling stalemates, inaccessible counters, area scaling without limit, initiative locks, maintenance spirals, alliance concentration, punitive offline losses, and comeback rules that erase earned decisions.

## 5. Card Games, Deckbuilders, And Auto-Battlers

Model first:

- Resource curve, card advantage, tempo, consistency, draw/filter density, and dead-card rate.
- Synergy payoff, setup, disruption, opportunity cost, and execution turn.
- Matchup matrices by skill, going-first state, map/mode, and collection access.
- Shop/offer odds, shared pool, depletion, rerolls, upgrade completion, and pity.

Key targets:

- Probability of drawing/assembling a line by turn or shop round.
- Viable cards/units per cost band and inclusion concentration.
- First-player advantage, matchup polarization, and non-game rate.
- Time/cost to a competitively viable collection.

Evaluate packages and curves, not cards in isolation. Include mulligans, tutors, generated resources, replacement effects, discover pools, and hidden shared-pool state.

Watch for infinite loops, zero-interaction kills, universal staples, overly consistent combos, polarized matchups, hidden pool effects, rarity as balance compensation, and collection access mistaken for skill balance.

## 6. Idle And Incremental Games

Model first:

- Production and cost curves on a log scale.
- Online, offline, active, idle, new, returning, and optimized rates.
- Upgrade payback, prestige recovery, and new-frontier gain.
- Capacity, offline cap, boosts, stacking order, event injection, and currency sinks.

Key targets:

- Time between meaningful decisions by phase.
- Time to recover the previous frontier after reset.
- Relative contribution of each production layer.
- Progress stalls, stock-days, and active-versus-wait time.

Use piecewise phases for onboarding, optimization, prestige, and long tail. Define large-number precision and overflow behavior. Make multiplier order inspectable.

Watch for runaway compounding, upgrade payback beyond useful horizon, dead clicking, clock manipulation, offline-claim exploits, event multiplier explosions, and selling relief from an intentionally unusable baseline.

## 7. Puzzle, Match-3, And Casual Games

Model first:

- Success by level, attempt, move/time budget, booster, initial board, and cohort.
- Goal composition, blocker pressure, spawn rules, solvability, and variance.
- Level funnel, fail margin, retry, lives/energy, hint use, and session cadence.

Key targets:

- First and learned pass, attempts-to-clear, moves short, and abandon.
- Probability of solvable and fair initial/generated boards.
- Booster-free versus booster-assisted clear and booster dependency.
- Mechanic introduction/practice/combine/test sequence.

Use difficulty waves rather than monotonic growth. Test generated boards with actual policies, cascades, reshuffles, and blocker interactions.

Watch for impossible seeds, outcomes decided by first random board, one-move spikes, hidden booster dependence, punitive streak/life loss, stale goals, and retries designed primarily to interrupt flow or sell relief.

## 8. Simulation, Management, Survival, And Crafting Games

Model first:

- Stocks, flows, capacities, labor/actions, maintenance, logistics, storage, and decay.
- Production chains, conversion, bottlenecks, market feedback, and specialization.
- Risk frequency, severity, preparation, leading indicators, cascades, and recovery.
- Steady, growth, crisis, recovery, and late-game states.

Key targets:

- Meaningful decision interval and planning horizon.
- Capacity utilization, bottleneck diversity, and strategy viability.
- Crisis preparation and recovery time.
- Craft-versus-buy, resource scarcity, and stock resilience.

Preserve several operating strategies. Surface leading indicators before catastrophic failure. Let players understand why a chain is unstable.

Watch for one optimal ratio, positive feedback without brakes, invisible irreversible collapse, dominant early openings, resource overflow, save/load abuse where relevant, craft/salvage arbitrage, and threats that bypass all preparation.

## 9. Sports And Racing Games

Model first:

- Player/vehicle attributes, input execution, physics envelope, stamina/fuel/tires, and track/venue.
- Event duration, scoring, possession, pace, catch-up, contact, penalties, and AI policies.
- Upgrade/setup tradeoffs and homologation/equalization rules.
- Matchmaking by skill, assists, input, vehicle/team strength, and track familiarity.

Key targets:

- Lap/time/score distributions and outcome calibration.
- Overtake/chance creation, lead changes, and decisive error cost.
- Setup/vehicle viability by track/event and skill cohort.
- Assist advantage, first/last position experience, and disconnect handling.

Avoid rubber-banding that invalidates mastery or secretly changes physics. If catch-up exists, make its rules bounded and compatible with competitive integrity.

Watch for dominant setups, pay-to-compete rosters/vehicles, input/assist cliffs, collision exploits, time-trial cheating, side/venue bias, scoring edge cases, and AI that targets outcomes instead of plausible play.

## 10. Sandbox, Social, And Cooperative Games

Model first:

- Creation/resource tools, sharing, discovery, social graph, group capacity, and moderation constraints.
- Contribution, ownership, permissions, group goals, and free-rider/grief behavior.
- Cooperative role value, scaling by party size, join/leave, and carry.
- User-generated economy, ranking, and discovery feedback loops.

Key targets:

- Time to first successful creation or social connection.
- Contribution fairness and group-goal completion.
- Small/large group viability and late-join experience.
- Discovery concentration and creator reward distribution.

Do not reduce social value to currency. Model coordination, trust, visibility, identity, and option value.

Watch for rich-get-richer discovery, group-size dominance, alt-account farming, grief incentives, mandatory social chores, creator exploitation, and rewards that distort cooperative play into competition.

## 11. PvP And Live-Service Cross-Cutting Rules

Always segment by rating/skill, uncertainty, party, role, input, latency, platform, region, map, side, version, option mastery, and access.

Use expected win near 45-55% as a diagnostic band for ordinary even matches, not a personal outcome controller. Inspect calibration and tails.

Track conditional option lift, pick/ban, matchup, composition, queue, surrender, disconnect, smurf, and substitution. Keep required counters accessible and competitive power within the declared fairness contract.

For live ops, sum all overlapping time, economy, reward, and power effects. Version configs, preserve player investments, stage changes, and maintain rollback.

Watch for aggregate metrics hiding expert dominance, population composition shift, rating inflation, side/map bias, role scarcity, stale resets, inaccessible counters, and monetization becoming competitive counterplay.

## 12. Hybrid-Game Integration

Identify one primary loop and list secondary loops. Create a cross-system dependency table:

| Source system | Destination system | Value transferred | Clock | Risk |
| --- | --- | --- | --- | --- |

Common hybrid risks:

- PvE progression leaking uncontrolled power into PvP.
- Idle income collapsing active economy pricing.
- Gacha collection determining strategy access.
- Roguelike meta-progression erasing run decisions.
- Social/guild rewards becoming mandatory solo progression.
- Live events injecting value into permanent markets.

Balance the transfer boundary, not each loop in isolation. Simulate player policies that optimize across systems.
