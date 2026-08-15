# Metrics Catalog

Every metric `sim_report.py` produces: its definition, the dotted path used by objectives and
thresholds, how to read it, and the failure it exposes. Metric paths are addressable with
`sim_report.get_path`, so the same string works in a tuning plan and in an acceptance table.

## 1. Outcome

| Path | Definition | Read it for |
| --- | --- | --- |
| `win_rate.point` | Fraction of battles won by the focus team | The primary band |
| `win_rate.low` / `.high` | Wilson 95% bounds | Whether the band question is answerable at this sample size |
| `win_rate.half_width` | Half the interval width | Precision. Gate on this, not just on the point |
| `loss_rate.point` | Opponent wins | Asymmetry when draws exist |
| `draw_rate` | Neither team eliminated | A stalled resolution loop |
| `timeout_rate` | Battles that hit `max_rounds` | Unreadable outcomes |
| `outcome_entropy` | Binary entropy of the win rate, in bits | Whether the result is decided before play |

`outcome_entropy` is 1.0 at a coin flip and 0.0 at a certainty. Below roughly 0.7 (win rate outside
19%-81%) the encounter has a predetermined answer for the modeled cohort. That is correct for a
tutorial and wrong for a competitive match.

## 2. Length And Pacing

| Path | Definition |
| --- | --- |
| `rounds.mean` / `duration.mean` | Average battle length in rounds / seconds |
| `rounds.p10` / `.p50` / `.p90` / `.max` | Length distribution |
| `rounds.cv` | Standard deviation over mean |
| `rounds.ci_low` / `.ci_high` / `.half_width` | Confidence interval on the mean |

Tune the anchor players feel, which is p50 and p90, not the mean. A `cv` above 0.5 means length is
mostly determined by RNG rather than by design; players read that as inconsistency, not as depth.
A p90 far above p50 is the slog complaint before anyone files it.

## 3. Shape Of The Win

| Path | Definition | Failure it exposes |
| --- | --- | --- |
| `margin.mean` | Mean absolute gap in team HP fraction at the end | Whether fights end close or lopsided |
| `blowout_rate` | Decisive battles where the winner kept >= 70% HP | The encounter is a formality |
| `close_rate` | Decisive battles where the winner kept <= 20% HP | Whether clears feel earned |
| `comeback_rate` | Decisive battles where the winner was behind at some round end | Whether the fight is decided early |
| `lead_flips.mean` | Times the HP-fraction lead changed hands | Swinginess |
| `first_blood.focus_team_rate` | Share of battles where the focus team lands the first kill | Opening tempo |
| `first_blood.win_rate_with_first_blood` | Win rate given the focus team killed first | Snowballing |
| `first_blood.win_rate_without_first_blood` | Win rate given the focus team lost a unit first | Recoverability |

The gap between the two `first_blood` win rates is the snowball measure. A gap near 100 points means
the first kill decides the fight and everything after it is theatre. Note that against a
single-unit team the first kill *is* the end of the fight, so `win_rate_with_first_blood` is
trivially 1.0 there and carries no information.

`comeback_rate` near zero says the outcome is settled in the opening exchange. Near one says the
early game does not matter. Neither extreme is what players describe as a good fight.

## 4. Contribution

Per unit under `units.<team>/<id>`:

| Path suffix | Definition |
| --- | --- |
| `damage_share.mean` | Mean of the unit's per-battle share of its own team's damage |
| `damage_share.low` / `.high` | Confidence interval on that mean |
| `damage_share.p10` / `.p90` | Per-battle spread of the share |
| `damage_taken_share` | Mean share of damage absorbed by the team |
| `healing_share` | Mean share of team healing |
| `damage_per_battle`, `dps` | Absolute output, and output per second |
| `overkill_ratio` | Overkill divided by damage dealt |
| `survival_rate`, `death_rate`, `mean_death_round` | Durability |
| `actions_per_battle`, `hit_rate`, `crit_rate` | Uptime and roll outcomes |

Share is computed per battle and then averaged, not computed from summed totals. The two differ
whenever battle length correlates with composition, and the per-battle version is the one that
matches what a player experiences in a given fight.

`damage_share.p10` far below the mean identifies a unit whose contribution depends on a condition
that does not always occur. That is a design choice when intended and a reliability problem when
not.

High `overkill_ratio` on a burst unit means its damage budget is being spent on already-dead
targets: the number on the tooltip is bigger than the contribution.

## 5. Roster Health

| Path | Definition | Read it for |
| --- | --- | --- |
| `max_damage_share` | Largest mean share on the focus team | A single carry owning the encounter |
| `min_damage_share` | Smallest mean share | A slot that does nothing |
| `concentration.top1_share` / `top3_share` | Concentration at the head | Dominance |
| `concentration.gini` | 0 = perfectly even, 1 = one contributor | Overall spread |
| `concentration.effective_contributors` | Perplexity of the share vector | How many units actually carry the fight |
| `concentration.roster_size` | Units on the focus team | The denominator |
| `dead_weight` | Units below half an even share with under 10% of healing | Named candidates for cutting or buffing |

`effective_contributors` is the most useful of these. A four-unit team at 3.1 means roughly three
units matter. A four-unit team at 1.4 means one carry plus decoration, whatever the roster screen
says. Compare it against `roster_size` and against the design intent for the composition: a
deliberate carry-plus-support design should show a low number, and should say so in advance.

`dead_weight` is a heuristic, not a verdict. A unit with no damage and no healing may still be
providing the shield or the crowd control that wins the fight. Check `damage_taken_share` and its
status effects before acting on it.

## 6. Metrics The Catalog Does Not Contain

There is no `fun`, no `engagement`, no `depth`. The closest available proxies are
`outcome_entropy` (is the result in doubt), `effective_contributors` (does the roster matter),
`comeback_rate` (is the fight live throughout), and `rounds.cv` (is the length consistent). Use
them as proxies and name them as proxies. A report that claims to have measured playability has
overstated what the simulation did.

Player-facing questions the catalog cannot answer: readability, input feel, clarity of failure
cause, satisfaction of a mechanic, and whether the intended strategy is discoverable. Those need
playtests. State them as open questions rather than leaving the impression the numbers covered them.
