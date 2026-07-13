# Rewards And RNG

Use this reference for reward cadence, loot tables, rarity, weighted selection, pity, duplicate protection, randomized monetization, crafting/enhancement chance, and bad-luck protection.

## Contents

1. Reward contract and utility
2. Reward cadence and choice
3. Loot table architectures
4. Probability and useful-value math
5. Multi-stage tables and filtering
6. Pity and bad-luck protection
7. Duplicates, targeting, and collection
8. Enhancement and crafting RNG
9. Randomized monetization and gacha
10. Adaptive rewards and streak breakers
11. Validation and telemetry

## 1. Reward Contract And Utility

Give every reward a job:

- Immediate power, long-term progress, build option, access, recovery, expression, collection, social value, or prestige.
- Teach or reinforce a mode, mechanic, or goal.
- Create a choice, surprise, anticipation, completion, or relief cadence.

Distinguish face value from player utility:

```text
useful_utility = direct_use + option_value + conversion_value + collection_value - inventory_cost
```

Utility depends on inventory, build, progression stage, duplicate state, trade rules, and content horizon. Track useful-drop rate, not only rarity rate.

Define whether a reward is guaranteed, random, chosen, targeted, traded, bound, expiring, duplicated, converted, or protected.

## 2. Reward Cadence And Choice

Budget rewards over several clocks:

- Per action/kill for immediate feedback.
- Per encounter/match for completion.
- Per session for a meaningful goal.
- Daily/weekly for return cadence.
- Per tier/run/season for mastery and aspiration.

Avoid making every action noisy or every meaningful reward distant. Use minor rewards for feedback and meaningful rewards for decisions.

Track:

- Time and attempts between useful rewards.
- Maximum drought and p50/p90/p99 drought.
- Choice frequency and number of viable options.
- Inventory cleanup and comparison burden.
- Reward relevance when content becomes farmable.

Choices can reduce variance while preserving surprise. Targeted rewards, rerolls, wishlists, tokens, and deterministic exchanges let players act on knowledge.

## 3. Loot Table Architectures

Choose an architecture explicitly:

- **Independent rolls**: each item rolls separately; multiple outcomes may occur.
- **Weighted single selection**: one item chosen proportional to weight.
- **Hierarchical table**: choose rarity/category, then item; verify final displayed odds.
- **Without replacement**: draws remove entries until pool reset.
- **Fixed slots**: guaranteed categories plus random sub-rolls.
- **Conditional/filter table**: eligibility, ownership, class, or progression changes the pool.
- **Stateful table**: pity, streak breaker, or adaptive targeting changes odds.

Document roll order, eligibility, normalization, fallback, empty pool, duplicates, rerolls, and state updates. Final probability is the product/sum across all paths, not merely the first-stage rarity chance.

For a weighted table:

```text
P(item_i) = eligible_weight_i / sum(eligible_weights)
```

For multiple independent chances:

```text
P(at_least_one_in_r_rolls) = 1 - (1 - p)^r
```

For without-replacement sampling with `K` desired items among `N` and `n` draws:

```text
P(at_least_one) = 1 - C(N-K, n) / C(N, n)
```

## 4. Probability And Useful-Value Math

For independent chance `p`:

```text
expected_attempts = 1 / p
P(drop_by_n) = 1 - (1 - p)^n
attempts_for_quantile(q) = ceil(log(1-q) / log(1-p))
```

Expected reward utility:

```text
EV = sum(P(outcome_i) * useful_utility(outcome_i, player_state))
```

Report:

- Nominal and final probability.
- EV in declared utility units.
- p50/p90/p99 attempts and cost.
- Maximum exposure with protection.
- Probability of no useful result by target time.
- Probability of completing a set or intended build.

Do not add the EVs of mutually exclusive rewards or ignore inventory-dependent utility. Simulate collection completion when states interact.

## 5. Multi-Stage Tables And Filtering

For every outcome, enumerate paths:

```text
P(item) = sum(P(path_to_item))
P(path) = product(P(stage | prior_state))
```

Filters can change normalization. Verify odds for:

- New player, ordinary collection, nearly complete collection, and complete collection.
- Eligible and ineligible class/role/level.
- Full inventory, banned duplicate, and empty fallback pool.
- Rate-up, event overlap, and banner transition.

If displayed odds are rounded, ensure totals and individual probabilities remain truthful. State whether odds are per slot, per pack, per ten-pull, or conditional on a rarity.

## 6. Pity And Bad-Luck Protection

Define state and scope:

- Counter key: account, banner, item class, rarity, mode, or season.
- Increment event, reset event, carryover, expiry, migration, and simultaneous draw order.
- Hard guarantee, soft-pity schedule, featured guarantee, or token exchange.
- Behavior when several rewards drop in one batch.

For hard pity `N` with constant chance `p`:

```text
expected_attempts = (1 - (1 - p)^N) / p
maximum_attempts = N
```

For soft pity with attempt-dependent `p_k`:

```text
P(first_success_at_k) = p_k * product(1 - p_j, j=1..k-1)
expected_attempts = sum(P(no_success_before_k), k=1..maximum)
```

Implement the state machine and calculate exact or simulated percentiles. Do not substitute base chance in a stateful system.

Choose pity from acceptable maximum cost/time and desired distribution, not only the mean. Make the rule understandable and log state transitions.

## 7. Duplicates, Targeting, And Collection

Define duplicate outcomes:

- Required copies, upgrade value, conversion, trade, protection, reroll, or no value.
- First-copy guarantee, duplicate cap, and completion protection.
- Value after maximum upgrade or collection completion.

Measure useful-copy probability by collection state. A stable rarity probability can produce sharply falling utility as ownership grows.

Use targeting tools when build access matters:

- Wishlist or path selection.
- Choice chest or token exchange.
- Smart loot by eligible role/build.
- Duplicate protection or without-replacement pools.
- Deterministic crafting after bounded random progress.

Targeting should reduce harmful variance without secretly changing published odds. State which stage it affects.

## 8. Enhancement And Crafting RNG

For each attempt, define cost, chance, outcome, protection, counter state, and recovery. Model:

- Success, no change, downgrade, destruction, durability, byproducts, and refunds.
- Protection item opportunity cost.
- Expected and p50/p90/p99 total cost.
- Maximum loss and time to recover.
- Failure-streak behavior and stop policy.

High-stakes irreversible loss requires strong disclosure, bounded tails, and an alternative path. Do not use sunk cost and opaque odds as core engagement design.

For recipes with random quality, evaluate useful output after salvage and market value. Test craft/salvage cycles for positive arbitrage.

## 9. Randomized Monetization And Gacha

Treat paid randomness as a high-risk system. Define:

- Exact final odds, guarantee, featured split, pity carryover, duplicate value, and maximum cost.
- Currency purchase path, bonus currency, ten-pull rules, free pulls, tickets, and mixed balances.
- Age, region, platform, refund, chargeback, gifting, and spending-limit behavior.
- Free deterministic access and competitive impact.

Research current law and platform policy for every launch region; do not rely on this reference as legal advice.

Do not use hidden odds, near-miss fabrication, personalized loss schedules, undisclosed state, misleading currency conversions, or competitive necessity. Do not tune frustration to drive purchases.

Report cost distributions in real currency and earned time, including p50/p90/maximum for the featured target and collection goals. Monitor regret, refunds, complaints, excessive spend, and access fairness as guardrails.

## 10. Adaptive Rewards And Streak Breakers

Use adaptation to protect experience, not secretly manipulate high-stakes outcomes. Acceptable patterns include:

- Prevent impossible starting boards.
- Guarantee a minimum useful category after a drought.
- Avoid identical low-value rewards several times in a row.
- Offer a choice after repeated non-useful outcomes.

Version and test the state machine. In competitive or paid contexts, disclose material probability effects and preserve equal rules.

Do not fake a near miss, secretly reduce odds after success, or personalize outcomes from spend propensity.

## 11. Validation And Telemetry

Use exact enumeration for small finite tables and seeded simulation for stateful or combinatorial systems. Test:

- Probability sums, empty pools, filtering, fallback, and normalization.
- First draw, pity-minus-one, pity, post-pity, multi-pull, simultaneous success, and reset.
- New, partial, near-complete, and complete collections.
- Inventory full, duplicated transaction, reconnect, migration, banner end, and compensation.
- Maximum legal boosts and overlapping events.

Emit:

```text
reward_offer: table_id, config_version, eligible_pool_hash, player_state_tags
reward_roll: transaction_id, seed_ref, stage_results, final_outcome, probability_path
pity_change: counter_id, before, reason, after, reset_scope
reward_resolution: item_id, quantity, duplicate_state, conversion, inventory_result
```

Dashboard final odds, useful-drop rate, drought percentiles, pity-trigger share, duplicate/conversion share, completion time, real/earned cost, refund/complaint, and discrepancies between expected and realized distributions.
