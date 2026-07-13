# Economy And Monetization

Use this reference for currencies, inventories, sources, sinks, pricing, crafting, markets, energy, live events, inflation, monetization, and economy operations. Read the rewards reference for randomized acquisition.

## Contents

1. Economy contract and topology
2. Ledger identities and reconciliation
3. Currency and resource roles
4. Pricing and time-to-goal
5. Source design
6. Sink design
7. Exchange, crafting, and player markets
8. Energy, time gates, and capacity
9. Monetization and fairness
10. Events, seasons, and compensation
11. Exploits and operational controls
12. Economy validation and health dashboard

## 1. Economy Contract And Topology

Define each stock and flow:

`id | owner | unit | source/sink/exchange | eligibility | cadence | cap | expiry | authority | purpose`

Draw a transaction graph with currencies, resources, items, time, and real-money entry points as nodes. Label conversion direction, rate, fee, cap, and reversibility. Cycles require explicit arbitrage tests.

Separate:

- **Closed economies**: mostly system-issued and system-consumed.
- **Player markets**: value and supply emerge from player exchange.
- **Hybrid economies**: system price floors/ceilings, taxes, bind rules, or market makers coexist with trade.

State the desired player decisions: spend now versus save, specialize versus diversify, craft versus buy, active versus idle, safe versus risky, or personal versus group investment.

## 2. Ledger Identities And Reconciliation

Use append-only transaction reasoning:

```text
ending_stock = opening_stock + credits - debits + migration_adjustment
```

Every mutation needs a stable transaction ID, reason, config version, before/after balance, timestamp, and correlation ID. Retries must be idempotent.

Reconcile per player and globally. An unexplained delta is a data or integrity defect, not an economy trend.

Keep these separate:

- Earned, purchased, granted, refunded, compensated, migrated, and converted value.
- Balance stock, period income, period spend, and lifetime flow.
- Liquid, bound, expiring, pending, and escrow state.
- Required, optional-power, convenience, cosmetic, social, and prestige spend.

## 3. Currency And Resource Roles

Create a currency only when it supports a distinct decision, cadence, audience, or reset boundary. Common roles:

- Broad soft currency for frequent flexible spend.
- Hard/premium currency for purchased or scarce flexible value.
- Mode currency to preserve a mode's reward loop.
- Seasonal/event currency with an explicit conversion or expiry.
- Crafting materials that express recipe choices or scarcity.
- Energy/tickets that control cadence or capacity.
- Social/guild resources that coordinate group goals.

Too few currencies can cause one optimal farm to solve everything. Too many create cognitive load, stranded value, exchange opacity, and maintenance cost.

For each currency, define desirable stock-days and goal coverage:

```text
stock_days = current_stock / trailing_spendable_income_per_day
goal_coverage = current_stock / next_meaningful_goal_cost
```

## 4. Pricing And Time-To-Goal

Derive prices from target time and spendable income:

```text
spendable_income = gross_income - required_operating_costs
price = target_periods_to_goal * spendable_income_per_period
time_to_goal = max(0, price - current_stock) / spendable_income_per_period
```

Model the exact acquisition schedule when income or costs change with progression. Calculate cumulative price, calendar time, active time, and opportunity cost.

Price by intended cohort and content stage, then test all cohorts against the same public price. Do not personalize prices to frustration, spending propensity, or hidden difficulty.

For repeatable upgrades, align cost and income growth intentionally:

```text
next_interval / current_interval = (next_cost / current_cost) / (next_income / current_income)
```

If cost grows 12% while income is flat, every interval grows 12%. Decide whether that slowdown is intended.

## 5. Source Design

Classify sources:

- First-clear, repeatable, daily/weekly, event, achievement, catch-up, social, purchased, refund, and compensation.
- Guaranteed versus random.
- Active, passive, offline, market, or competitive.
- Capped, diminishing, or uncapped.

Measure source share by cohort and stage. Avoid one source dominating all value unless it is the intended core loop. Check:

- Optimizer amplification from speed, power, party, or schedule.
- Multi-account, bot, AFK, reconnect, and duplicate-claim behavior.
- Offline cap, clock rollback, time-zone, and reset races.
- Event stacking, boost multiplication, and refund loops.

Use diminishing credit or caps only after defining the legitimate high-engagement experience. Communicate them and keep compensation/refunds in separate ledger types.

## 6. Sink Design

Give every sink a player-facing purpose:

- Operating cost that shapes a decision.
- Deterministic progression or access.
- Optional optimization and experimentation.
- Collection, cosmetic, prestige, social, or convenience.
- Market tax that controls velocity or speculation.
- Value conversion, salvage, or reroll.

Do not add an invisible tax solely to force sink coverage. A healthy economy can support saving.

Measure:

```text
net_flow = sources - sinks
sink_coverage = sinks / sources
source_concentration = largest_source / total_sources
sink_concentration = largest_sink / total_sinks
```

Interpret ratios against desired stock and goals. `sink_coverage = 100%` is not a universal target.

Avoid regressive flat mandatory sinks that consume most novice income but barely affect optimizers. Prefer transparent costs connected to activity, progression, market value, or optional surplus goals.

## 7. Exchange, Crafting, And Player Markets

For every conversion, record:

`input -> output | rate | fee | limit | cooldown | bind | reversibility | price authority`

Test every directed cycle. A cycle with net positive value after fees creates arbitrage. Include bulk discounts, quality changes, salvage, crafting crits, taxes, listings, cancellation, refunds, and cross-region prices.

For crafting, model:

- Recipe input supply and opportunity cost.
- Output usefulness, quality distribution, failure, byproducts, and salvage.
- Crafting capacity and progression.
- Make-versus-buy equilibrium and specialist value.

For player markets, monitor price, volume, spread, time-to-sale, concentration, velocity, listed supply, completed supply, and wealth distribution. Segment new entrants, ordinary traders, specialists, market makers, and suspected manipulators.

Plan gold/currency creation and destruction independently from item creation and destruction. Taxes remove currency but do not remove item supply.

## 8. Energy, Time Gates, And Capacity

Define:

- Maximum capacity, regeneration, overflow, refill, claim, and expiry.
- Cost per activity, failure refund, disconnect behavior, and party cancellation.
- Natural sessions per day and time to full.
- Free, earned, event, and paid refills.

Calculate:

```text
natural_attempts_per_day = daily_regeneration / cost_per_attempt
time_to_full = capacity / regeneration_rate
wasted_regeneration = max(0, generated_while_full)
```

Tune energy around intended cadence and server/content constraints, not as punishment for enjoying the game. Do not sell relief from deliberately unusable retry friction or obscure failure.

Test time zones, daylight-saving changes, clock manipulation, offline duration, multiple devices, reset overlap, and partial-cost refunds.

## 9. Monetization And Fairness

State the monetization contract:

- What money can buy: content, cosmetics, convenience, time, options, random outcomes, or direct power.
- Which modes require equalized access or power.
- Maximum power/access gap and time-to-parity for non-paying players.
- Purchase caps, refund behavior, regional prices, and platform fees.

Track fairness metrics such as:

```text
paid_power_gap = paid_reference_power / nonpayer_reference_power - 1
days_to_parity = time_for_nonpayer_to_reach_paid_reference_state
required_counter_access = share_of_active_players_with_access_to_needed_counter
```

Use payment cohorts to audit access and harm, not to manipulate difficulty or outcomes. Never make a purchase the required answer to a deliberately created failure.

For convenience/time sales, preserve meaningful play and avoid making the baseline intentionally tedious. For direct power, define competitive boundaries, caps, and non-paying access. For randomized purchases, follow the rewards reference and verify current regional law, age protections, disclosure, refunds, and platform policy before launch.

Do not infer that higher short-term spend proves healthier design. Monitor regret, refund, complaint, churn, progression compression, competitive access, and long-term trust.

## 10. Events, Seasons, And Compensation

Budget event supply and sinks before launch:

```text
event_completion_time = required_event_value / attainable_value_per_active_day
event_surplus = attainable_total - required_total
```

Model late joiners, missed days, new players, capped players, optimizers, purchasers, and time-zone boundaries. State carryover, conversion, expiry, mailbox, and unclaimed behavior.

Do not stack events without summing all injected value and required time. Check competition with permanent goals and player fatigue.

For compensation, choose the least destabilizing form that restores loss: affected item, bounded claim, progress-only credit, or targeted replacement. Keep compensation out of normal source metrics and make claims idempotent.

At season reset, specify stock handling, exchange, caps, market closure, pending trades, recipes, expiring claims, and migration.

## 11. Exploits And Operational Controls

Test:

- Duplicate transactions and retry storms.
- Client-trusted prices, balances, or timestamps.
- Negative quantities, integer overflow, rounding arbitrage, and fractional remnants.
- Buy/sell, craft/salvage, convert/reconvert, and cross-market loops.
- Refund after consumption, chargeback, mailbox duplication, and trade rollback.
- Clock changes, offline claims, reset overlap, and multi-device races.
- Party reward duplication, reconnect, and instance reset.
- Bot amplification and market concentration.

Use stable transaction IDs, server authority, atomic mutations, idempotency, velocity limits, anomaly alerts, and reconciliation. Keep fraud enforcement separate from ordinary high-skill optimization.

## 12. Economy Validation And Health Dashboard

Simulate 30/60/90-day and season horizons for new, core, intermittent, optimizer, returning, purchaser, non-purchaser, saver, spender, crafter, trader, and adversarial policies.

Report by cohort and stage:

- Opening stock, credits, debits, ending stock, and reconciliation error.
- p10/p50/p90/p99 income, spend, balance, and stock-days.
- Time-to-goal and purchase interval distributions.
- Source/sink shares, concentration, and legal maximum envelope.
- Item supply, useful output, trade price/volume/velocity, and wealth concentration.
- Required-cost failure, stranded currency, and unclaimed/expired value.
- Paid access, power gap, time-to-parity, refund, and complaint guardrails.

Roll out economy changes gradually. Shadow-calculate first, then limit exposure. Define migration, compensation, stop, and rollback before changing prices, sources, sinks, or exchange rates.
