#!/usr/bin/env python3
"""Create a remake-research document pack for a target game."""
from __future__ import annotations

import argparse
import csv
import re
from io import StringIO
from pathlib import Path
from textwrap import dedent, indent


SKILL_ROOT = Path(__file__).resolve().parent.parent


ARCHETYPE_CHOICES = ("mmo", "arpg", "roguelike", "card")
ARCHETYPE_FILE_NAME = "07-archetype-specific-template.md"
ARCHETYPE_METRIC_FILE_NAME = "08-archetype-metric-baselines.md"
EXPERIMENT_FILE_NAME = "09-experiment-design.md"
EXPERIMENT_SUMMARY_FILE_NAME = "10-experiment-summary.md"
DOSSIER_TEMPLATE_FILE_NAME = "remake-dossier-template.md"
PRIORITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}

ARCHETYPE_SPECS = {'mmo': {'display': 'MMO',
         'reference': 'template-mmo.md',
         'summary': 'Massively multiplayer lens focused on social dependency, economy durability, '
                    'content cadence, and service topology.',
         'must_capture': ['World topology: hubs, zones, channels, shards, matchmaking, and '
                          'instancing.',
                          'Social dependency: party roles, guild loops, trade, raids, and how solo '
                          'play coexists with group play.',
                          'Retention spine: daily, weekly, seasonal, expansion, and endgame ladder '
                          'structure.',
                          'Economy pressure: sinks, inflation controls, trade restrictions, and '
                          'anti-bot assumptions.',
                          'Content cadence: how the live game stays alive after the honeymoon '
                          'period.'],
         'extra_outputs': ['Social dependency map.',
                           'Currency and sink matrix.',
                           'Endgame ladder and cadence calendar.',
                           'Class or role ecology matrix.'],
         'failure_modes': ['Copying grind volume without the social or market cushion that made it '
                           'tolerable.',
                           'Flattening multiplayer loops into solo content without replacing the '
                           'missing motivation.',
                           'Ignoring economy leakage, inflation, or content cadence when proposing '
                           'the remake.'],
         'checklist_rows': [('world-topology',
                             'Map hubs, zones, channels, shards, and instance boundaries.'),
                            ('social-loop',
                             'Explain party, guild, trade, raid, and solo coexistence.'),
                            ('economy-durability',
                             'Document sinks, inflation controls, and trade rules.'),
                            ('content-cadence',
                             'Capture daily, weekly, seasonal, and endgame cadence.')]},
 'arpg': {'display': 'ARPG',
          'reference': 'template-arpg.md',
          'summary': 'Action RPG lens focused on combat feel, loot chase, buildcraft, pacing '
                     'density, and endgame repeatability.',
          'must_capture': ['Moment-to-moment feel: responsiveness, cancels, hit stop, movement '
                           'commitment, and camera language.',
                           'Loot chase: rarity ladder, affix pools, deterministic crafting, and '
                           'inventory pressure.',
                           'Buildcraft: skill tags, synergies, passive systems, and failure '
                           'recovery when a build stalls.',
                           'Density and pacing: pack size, traversal downtime, burst windows, and '
                           'boss cadence.',
                           'Endgame repeatability: maps, dungeons, ladders, seasonal modifiers, '
                           'and chase goals.'],
          'extra_outputs': ['Skill-tag and affix synergy matrix.',
                            'Loot ladder and crafting funnel.',
                            'Combat pacing benchmark table.',
                            'Endgame loop map.'],
          'failure_modes': ['Copying loot color tiers while missing the actual chase structure.',
                            'Under-specifying combat timings, making the remake feel floaty or '
                            'stiff.',
                            'Designing endgame as a content list instead of a repeatable reward '
                            'loop.'],
          'checklist_rows': [('combat-feel',
                              'Capture responsiveness, cancels, hit pause, and movement '
                              'commitment.'),
                             ('loot-chase',
                              'Document rarity tiers, affixes, crafting, and inventory pressure.'),
                             ('buildcraft',
                              'Map skill tags, passive layers, synergies, and reset costs.'),
                             ('endgame-loop',
                              'Describe repeatable endgame structures and chase goals.')]},
 'roguelike': {'display': 'Roguelike',
               'reference': 'template-roguelike.md',
               'summary': 'Run-based lens focused on randomness governance, run rhythm, '
                          'fail-forward structure, and meta progression boundaries.',
               'must_capture': ['Run rhythm: floor structure, biome cadence, encounter escalation, '
                                'and recovery moments.',
                                'Randomness governance: seed surfaces, draft pools, reward '
                                'weighting, and anti-brick measures.',
                                'Failure meaning: what a loss teaches, what carries over, and how '
                                'the player re-enters.',
                                'Meta progression boundaries: permanent unlocks, power creep '
                                'limits, and mastery versus grind.',
                                'Build pivots: when and how a run can change direction without '
                                'collapsing.'],
               'extra_outputs': ['Run structure timeline.',
                                 'Reward-draft and anti-brick matrix.',
                                 'Meta progression cap table.',
                                 'Seed or RNG surface inventory.'],
               'failure_modes': ['Confusing randomness volume with meaningful variance.',
                                 'Letting meta progression overpower run-to-run mastery.',
                                 'Removing recovery windows and making every bad roll '
                                 'unrecoverable.'],
               'checklist_rows': [('run-rhythm',
                                   'Map floor cadence, biome pacing, escalation, and rest points.'),
                                  ('rng-governance',
                                   'Record seeds, reward weighting, and anti-brick measures.'),
                                  ('meta-progression',
                                   'Explain carryover, unlocks, caps, and reset friction.'),
                                  ('build-pivot',
                                   'Document how runs pivot and recover from weak starts.')]},
 'card': {'display': 'Card Game',
          'reference': 'template-card.md',
          'summary': 'Card-game lens focused on rules clarity, timing windows, resource curve, '
                     'card-pool ecology, and matchup health.',
          'must_capture': ['Rules engine: turn structure, phases, timing windows, stack or '
                           'resolution order, and hidden information rules.',
                           'Resource curve: mana, energy, tempo, draw smoothing, mulligan, and '
                           'snowball controls.',
                           'Card ecology: card types, copy limits, keyword systems, archetypes, '
                           'and hate or tech answers.',
                           'Collection or drafting loop: acquisition, crafting, rarity, rotation, '
                           'and onboarding deck quality.',
                           'Readability: board state clarity, log visibility, targeting rules, and '
                           'mobile or PC information density.'],
          'extra_outputs': ['Turn-state diagram.',
                            'Keyword glossary and timing reference.',
                            'Resource-curve target table.',
                            'Archetype and matchup matrix.'],
          'failure_modes': ['Copying card fantasy without reconstructing a precise rules engine.',
                            'Leaving timing windows implicit and creating ambiguous interactions.',
                            'Ignoring collection friction or onboarding deck quality when remaking '
                            'a live card game.'],
          'checklist_rows': [('rules-engine',
                              'Define phases, timing windows, resolution order, and hidden '
                              'information.'),
                             ('resource-curve',
                              'Document mana or energy curve, mulligan, draw smoothing, and '
                              'anti-snowball.'),
                             ('card-ecology',
                              'Map card types, keywords, copy limits, archetypes, and tech '
                              'answers.'),
                             ('collection-loop',
                              'Explain acquisition, crafting, rarity, rotation, and onboarding '
                              'deck quality.')]}}

ARCHETYPE_METRICS = {'mmo': {'reference': 'metrics-mmo.md',
         'rows': [('MMO-M1',
                   'retention-cadence',
                   'Daily route completion time',
                   'minutes/session',
                   'Time a representative mandatory daily route from login to completion.',
                   'Measures daily burden and long-term fatigue risk.'),
                  ('MMO-M2',
                   'social-gating',
                   'Time to first mandatory group gate',
                   'hours-to-unlock',
                   'Record when solo progress first meaningfully stalls without party, guild, or '
                   'raid access.',
                   'Shows how much the product depends on social progression rather than solo '
                   'persistence.'),
                  ('MMO-M3',
                   'economy-durability',
                   'Mandatory sink pressure',
                   'percent-of-gross-currency',
                   'Estimate required sinks as a share of gross currency earned in a '
                   'representative progression band.',
                   'Reveals whether the economy survives without runaway inflation.'),
                  ('MMO-M4',
                   'trade-reliance',
                   'Market dependency for progression-critical upgrades',
                   'percent-of-upgrades',
                   'Sample how many meaningful upgrades are realistically sourced through trade or '
                   'services.',
                   'Important when converting an online economy into a self-sufficient remake.'),
                  ('MMO-M5',
                   'reset-structure',
                   'Major reset cadence',
                   'days/reset',
                   'Record daily, weekly, and seasonal reset intervals tied to progression or '
                   'rewards.',
                   'Defines the live-service rhythm the remake must preserve or replace.')]},
 'arpg': {'reference': 'metrics-arpg.md',
          'rows': [('ARPG-M1',
                    'combat-tempo',
                    'Representative farming loop duration',
                    'minutes/run',
                    'Time one representative map, dungeon, or farming route from start to reward '
                    'resolution.',
                    'Defines repeatability and session pacing.'),
                   ('ARPG-M2',
                    'density',
                    'Average combat pack density',
                    'enemies/engagement',
                    'Sample average enemies per meaningful engagement across a representative '
                    'route.',
                    'Tracks whether the remake preserves tempo and crowd pressure.'),
                   ('ARPG-M3',
                    'power-spike',
                    'Time to first meaningful build spike',
                    'minutes-or-levels',
                    'Record when the build first gains a clearly felt jump in clear speed or '
                    'survivability.',
                    'Measures onboarding excitement and early retention.'),
                   ('ARPG-M4',
                    'loot-chase',
                    'Meaningful upgrade frequency',
                    'upgrades/hour',
                    'Count drops, crafts, or rerolls that materially improve the current build '
                    'over a representative hour.',
                    'Shows whether loot chase feels alive or dry.'),
                   ('ARPG-M5',
                    'build-friction',
                    'Respec or build pivot cost',
                    'currency-plus-minutes',
                    'Record the full cost to pivot into another viable build path.',
                    'Controls experimentation and failure recovery.')]},
 'roguelike': {'reference': 'metrics-roguelike.md',
               'rows': [('ROGUE-M1',
                         'run-rhythm',
                         'Full run duration',
                         'minutes/run',
                         'Time a representative successful run from start to ending or victory '
                         'screen.',
                         'Defines session expectation and pacing envelope.'),
                        ('ROGUE-M2',
                         'decision-density',
                         'Meaningful choice interval',
                         'minutes/decision',
                         'Measure time between draft, shop, pathing, or loadout decisions that '
                         'materially change the run.',
                         'Shows whether the run has enough agency between fights.'),
                        ('ROGUE-M3',
                         'recovery-structure',
                         'Recovery node frequency',
                         'count/run',
                         'Count heal, shop, rest, reroll, or bailout opportunities in a '
                         'representative run.',
                         'Reveals how forgiving the structure is after bad luck or mistakes.'),
                        ('ROGUE-M4',
                         'anti-brick',
                         'Pre-boss anti-brick opportunities',
                         'count-before-first-boss',
                         'Count guaranteed or likely systems that rescue weak starts before the '
                         'first major gate.',
                         'Important for preventing dead runs that feel predetermined.'),
                        ('ROGUE-M5',
                         're-entry',
                         'Loss-to-retry time',
                         'seconds/retry',
                         'Measure time from failure screen to regained player control in a fresh '
                         'run.',
                         'Defines how painful failure feels and how fast mastery loops restart.')]},
 'card': {'reference': 'metrics-card.md',
          'rows': [('CARD-M1',
                    'turn-pace',
                    'Median turn duration',
                    'seconds/turn',
                    'Sample representative early, mid, and late-game turns across multiple '
                    'matches.',
                    'Defines readability pressure and match flow.'),
                   ('CARD-M2',
                    'resource-curve',
                    'Turns to primary resource cap or decisive power turn',
                    'turns',
                    'Record when the game reaches full resource availability or a consistent '
                    'game-ending tempo point.',
                    'Maps pacing and comeback bandwidth.'),
                   ('CARD-M3',
                    'opening-consistency',
                    'Mulligan flexibility',
                    'cards-or-redraw-options',
                    'Document how many cards or choices the opening hand system allows the player '
                    'to smooth.',
                    'Directly affects non-games and opening variance.'),
                   ('CARD-M4',
                    'meta-health',
                    'Top archetype share',
                    'percent-of-sample',
                    'Estimate the share of observed matches or top lists occupied by the leading '
                    'archetype.',
                    'Provides a baseline for matchup diversity and meta concentration.'),
                   ('CARD-M5',
                    'onboarding',
                    'Starter deck performance gap',
                    'estimated-winrate-gap',
                    'Estimate the performance gap between onboarding decks and the live field or '
                    'intended baseline opponents.',
                    'Shows whether the collection loop supports or repels new players.')]}}

ARCHETYPE_METRIC_LINKS = {'mmo': [('MMO-M1',
          'EXP-02',
          'data/experiments/route-density-sample.csv',
          'duration_minutes',
          'numeric_band',
          'suggested',
          'Auto-roll route duration into daily route baseline when the sampled route is '
          'progression-representative.'),
         ('MMO-M2',
          '',
          '',
          '',
          'manual',
          'manual',
          'Requires interpretation from progression-band-map and source review.'),
         ('MMO-M3',
          'EXP-03',
          'data/experiments/economy-sampling.csv',
          'mandatory_sink;gross_input',
          'ratio_band',
          'suggested',
          'Compute mandatory sink pressure as mandatory_sink / gross_input.'),
         ('MMO-M4',
          '',
          '',
          '',
          'manual',
          'manual',
          'Requires trade and market observations beyond the default experiment templates.'),
         ('MMO-M5',
          '',
          '',
          '',
          'manual',
          'manual',
          'Usually sourced from service cadence and reset documentation.')],
 'arpg': [('ARPG-M1',
           'EXP-02',
           'data/experiments/route-density-sample.csv',
           'duration_minutes',
           'numeric_band',
           'suggested',
           'Auto-roll representative route duration into farming loop duration.'),
          ('ARPG-M2',
           'EXP-02',
           'data/experiments/route-density-sample.csv',
           'enemy_count;engagement_count',
           'ratio_band',
           'suggested',
           'Compute average pack density as enemy_count / engagement_count.'),
          ('ARPG-M3',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires progression-band or build-spike interpretation.'),
          ('ARPG-M4',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires item-upgrade relevance judgment, not just raw event counts.'),
          ('ARPG-M5',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires respec or build pivot cost sampling.')],
 'roguelike': [('ROGUE-M1',
                '',
                '',
                '',
                'manual',
                'manual',
                'Requires dedicated run-duration sampling.'),
               ('ROGUE-M2',
                '',
                '',
                '',
                'manual',
                'manual',
                'Requires decision-interval sampling from run logs.'),
               ('ROGUE-M3',
                '',
                '',
                '',
                'manual',
                'manual',
                'Requires recovery-node counting in progression or run-state logs.'),
               ('ROGUE-M4',
                '',
                '',
                '',
                'manual',
                'manual',
                'Requires anti-brick event counting before the first major gate.'),
               ('ROGUE-M5',
                'EXP-07',
                'data/experiments/failure-reentry.csv',
                'time_to_reentry_seconds',
                'numeric_band',
                'suggested',
                'Auto-roll failure-to-reentry timings into retry-speed baseline.')],
 'card': [('CARD-M1',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires turn-timing samples from state logs or match logs.'),
          ('CARD-M2',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires turn-curve sampling from match logs.'),
          ('CARD-M3',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires explicit mulligan-system sampling.'),
          ('CARD-M4',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires meta-share sampling from decklists or match populations.'),
          ('CARD-M5',
           '',
           '',
           '',
           'manual',
           'manual',
           'Requires onboarding deck performance measurement.')]}

EXPERIMENT_SPECS = [('EXP-01',
  'timing-capture',
  'Timing window capture',
  'mmo|arpg|roguelike',
  'frames-or-ms',
  '3-10 representative actions',
  'Count anticipation, active, recovery, interrupt, and cancel windows from representative clips.',
  'Turns vague feel into reproducible timing rules.'),
 ('EXP-02',
  'route-density-sample',
  'Route and density sample',
  'mmo|arpg',
  'minutes-and-enemies',
  '3 representative routes',
  'Measure route duration, enemy density, downtime, and reward completion on representative '
  'farming paths.',
  'Captures loop tempo, traversal burden, and content efficiency.'),
 ('EXP-03',
  'economy-sampling',
  'Faucet and sink sample',
  'all',
  'currency-plus-items',
  '10-30 observations',
  'Sample gross inputs, mandatory sinks, optional sinks, and recovery paths within a bounded '
  'progression band.',
  'Prevents fake economy models based on reward screenshots alone.'),
 ('EXP-04',
  'progression-band-map',
  'Progression band mapping',
  'all',
  'bands-or-stages',
  'full onboarding to endgame pass',
  'Map gate conditions, dominant loop, new unlocks, and obsolete loops per progression band.',
  'Preserves pacing, not just feature inventory.'),
 ('EXP-05',
  'onboarding-funnel',
  'Onboarding funnel observation',
  'all',
  'steps-and-minutes',
  'first 10-60 minutes',
  'Track first-session goals, blocking prompts, system reveals, friction points, and first strong '
  'payoff.',
  'Shows whether the remake can recreate the original first-session hook.'),
 ('EXP-06',
  'ui-flow-count',
  'UI flow step count',
  'all',
  'steps-per-task',
  '5-10 critical tasks',
  'Count entry points, clicks or inputs, confirmation states, and back-navigation behavior for '
  'core UI tasks.',
  'Converts interface quality into measurable friction.'),
 ('EXP-07',
  'failure-reentry',
  'Failure-to-reentry timing',
  'mmo|arpg|roguelike|card',
  'seconds-to-control',
  '3-5 representative failures',
  'Measure time from failure, loss, or wipe to restored player agency in a new attempt.',
  'Quantifies how punitive failure feels and how fast mastery loops restart.'),
 ('EXP-08',
  'state-log',
  'Encounter or match state log',
  'mmo|arpg|roguelike|card',
  'state-snapshots',
  '5-10 representative scenarios',
  'Record key state transitions, visible information, decision points, and resolution outcomes in '
  'a structured log.',
  'Supports exact reconstruction of rules, encounters, and readability loads.')]

EXPERIMENT_DETAIL_TEMPLATES = {'EXP-01': {'file': 'data/experiments/timing-capture.csv',
            'header': ['experiment_id',
                       'sample_id',
                       'source_id',
                       'action_name',
                       'clip_or_timestamp',
                       'anticipation_frames',
                       'active_frames',
                       'recovery_frames',
                       'interrupt_rule',
                       'cancel_rule',
                       'confidence',
                       'notes'],
            'sample': ['EXP-01', 'TIMING-001', '', '', '', '', '', '', '', '', '', '']},
 'EXP-02': {'file': 'data/experiments/route-density-sample.csv',
            'header': ['experiment_id',
                       'sample_id',
                       'source_id',
                       'route_name',
                       'context_band',
                       'duration_minutes',
                       'enemy_count',
                       'engagement_count',
                       'downtime_seconds',
                       'reward_summary',
                       'confidence',
                       'notes'],
            'sample': ['EXP-02', 'ROUTE-001', '', '', '', '', '', '', '', '', '', '']},
 'EXP-03': {'file': 'data/experiments/economy-sampling.csv',
            'header': ['experiment_id',
                       'sample_id',
                       'source_id',
                       'progression_band',
                       'input_type',
                       'gross_input',
                       'mandatory_sink',
                       'optional_sink',
                       'recovery_path',
                       'net_result',
                       'confidence',
                       'notes'],
            'sample': ['EXP-03', 'ECON-001', '', '', '', '', '', '', '', '', '', '']},
 'EXP-04': {'file': 'data/experiments/progression-band-map.csv',
            'header': ['experiment_id',
                       'band_id',
                       'source_id',
                       'entry_condition',
                       'dominant_loop',
                       'new_unlocks',
                       'obsolete_loops',
                       'exit_condition',
                       'confidence',
                       'notes'],
            'sample': ['EXP-04', 'BAND-001', '', '', '', '', '', '', '', '']},
 'EXP-05': {'file': 'data/experiments/onboarding-funnel.csv',
            'header': ['experiment_id',
                       'step_id',
                       'source_id',
                       'time_from_start_seconds',
                       'player_goal',
                       'system_reveal',
                       'friction_point',
                       'payoff',
                       'confidence',
                       'notes'],
            'sample': ['EXP-05', 'ONBOARD-001', '', '', '', '', '', '', '', '']},
 'EXP-06': {'file': 'data/experiments/ui-flow-count.csv',
            'header': ['experiment_id',
                       'task_id',
                       'source_id',
                       'entry_point',
                       'input_steps',
                       'confirmation_steps',
                       'backtrack_steps',
                       'blocking_prompts',
                       'completion_state',
                       'confidence',
                       'notes'],
            'sample': ['EXP-06', 'UIFLOW-001', '', '', '', '', '', '', '', '', '']},
 'EXP-07': {'file': 'data/experiments/failure-reentry.csv',
            'header': ['experiment_id',
                       'sample_id',
                       'source_id',
                       'failure_type',
                       'context_or_timestamp',
                       'time_to_reentry_seconds',
                       'retained_progress',
                       'penalty_summary',
                       'confidence',
                       'notes'],
            'sample': ['EXP-07', 'FAIL-001', '', '', '', '', '', '', '', '']},
 'EXP-08': {'file': 'data/experiments/state-log.csv',
            'header': ['experiment_id',
                       'sample_id',
                       'source_id',
                       'state_index',
                       'state_name',
                       'visible_information',
                       'decision_point',
                       'resolution_outcome',
                       'confidence',
                       'notes'],
            'sample': ['EXP-08', 'STATE-001', '', '', '', '', '', '', '', '']}}

ARCHETYPE_EXPERIMENT_PRIORITIES = {'mmo': {'EXP-01': 'medium',
         'EXP-02': 'high',
         'EXP-03': 'high',
         'EXP-04': 'high',
         'EXP-05': 'medium',
         'EXP-06': 'medium',
         'EXP-07': 'medium',
         'EXP-08': 'high'},
 'arpg': {'EXP-01': 'high',
          'EXP-02': 'high',
          'EXP-03': 'medium',
          'EXP-04': 'medium',
          'EXP-05': 'medium',
          'EXP-06': 'low',
          'EXP-07': 'medium',
          'EXP-08': 'high'},
 'roguelike': {'EXP-01': 'high',
               'EXP-02': 'low',
               'EXP-03': 'medium',
               'EXP-04': 'high',
               'EXP-05': 'medium',
               'EXP-06': 'low',
               'EXP-07': 'high',
               'EXP-08': 'high'},
 'card': {'EXP-01': 'low',
          'EXP-02': 'low',
          'EXP-03': 'medium',
          'EXP-04': 'medium',
          'EXP-05': 'high',
          'EXP-06': 'high',
          'EXP-07': 'medium',
          'EXP-08': 'high'}}



def evidence_section_block(language: str) -> str:
    _ = language
    return dedent(
        """\
        ## Evidence Tagging

        - Cite ledger IDs inline inside `Confirmed Facts` and `Inferred Model`, for example `S-id`.
        - Keep `Remake Decisions` separate from observed facts; add `EXP-id`, metric IDs, or supporting `S-id` when a decision depends on evidence.

        ## Confirmed Facts

        ## Inferred Model

        ## Remake Decisions

        ## Open Questions
        """
    )


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "game"


def render_csv(rows: list[list[str]]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue()


def format_version_scope(version_scope: str | None, language: str) -> str:
    _ = language
    if version_scope:
        return version_scope
    return "TBD version / region / platform / time slice"


def archetype_display(archetype: str | None, language: str) -> str:
    _ = language
    if not archetype:
        return "Not set"
    return ARCHETYPE_SPECS[archetype]["display"]


def archetype_scope_line(archetype: str | None, language: str) -> str:
    label = archetype_display(archetype, language)
    return f"- Archetype lens: `{label}`"


def build_documents(
    game: str, version_scope: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    return build_documents_en(game, version_scope, archetype)


def build_support_files(
    game: str, version_scope: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    return build_support_files_en(game, version_scope, archetype)


def build_single_file_template(
    game: str, version_scope: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    archetype_line = archetype_scope_line(archetype, "en")
    lines = [
        f"# {game} Remake Dossier",
        "",
        f"- Target game: `{game}`",
        f"- Baseline version: `{version_scope}`",
        f"{archetype_line}",
        "- Output shape: single document",
        "",
        "## Usage",
        "",
        "- Merge the multi-file research pack into this dossier in deliverable order.",
        "- Preserve `Confirmed Facts`, `Inferred Model`, `Remake Decisions`, and `Open Questions` in every major section.",
        "- Cite inline ledger anchors like `S-id` inside `Confirmed Facts` and `Inferred Model`.",
        "- If the research already exists as separate files, prefer `merge_remake_docs.py`.",
        "",
        "## Contents",
        "",
        "1. Overview and source ledger",
        "2. Product and player experience",
        "3. Systems and gameplay",
        "4. Economy and balance",
        "5. Content, art, audio, and narrative",
        "6. Client architecture and production",
        "7. Replica backlog and acceptance",
    ]
    if archetype:
        lines.extend(
            [
                "8. Archetype-specific template",
                "9. Archetype metric baselines",
                "10. Experiment design",
                "11. Experiment summary",
                "12. Research log",
            ]
        )
    else:
        lines.extend(
            [
                "8. Experiment design",
                "9. Experiment summary",
                "10. Research log",
            ]
        )
    return {DOSSIER_TEMPLATE_FILE_NAME: "\n".join(lines).rstrip() + "\n"}


def build_archetype_file(
    game: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    if not archetype:
        return {}

    spec = ARCHETYPE_SPECS[archetype]
    display = spec["display"]
    summary = spec["summary"]
    reference = spec["reference"]
    metrics_reference = ARCHETYPE_METRICS[archetype]["reference"]
    evidence_block = evidence_section_block("en")
    must_capture = "\n".join(f"- {item}" for item in spec["must_capture"])
    extra_outputs = "\n".join(f"- {item}" for item in spec["extra_outputs"])
    failure_modes = "\n".join(f"- {item}" for item in spec["failure_modes"])

    content = f"""\
# {game} {display} Archetype Template

## Lens

- Archetype: `{display}`
- Reference file: `references/{reference}`
- Metric reference: `references/{metrics_reference}`
- Focus summary: {summary}

## Must Answer

{must_capture}

## Additional Outputs

{extra_outputs}

## Common Failure Modes

{failure_modes}

{evidence_block}
"""
    return {ARCHETYPE_FILE_NAME: dedent(content)}


def build_archetype_checklist_csv(archetype: str, language: str) -> str:
    _ = language
    rows = ARCHETYPE_SPECS[archetype]["checklist_rows"]
    csv_rows = [["area", "focus_question", "priority", "status", "notes"]]
    for area, question in rows:
        csv_rows.append([area, question, "high", "not-started", ""])
    return render_csv(csv_rows)


def build_archetype_metric_file(
    game: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    if not archetype:
        return {}

    display = ARCHETYPE_SPECS[archetype]["display"]
    reference = ARCHETYPE_METRICS[archetype]["reference"]
    rows = ARCHETYPE_METRICS[archetype]["rows"]
    lines = [
        f"# {game} {display} Metric Baselines",
        "",
        "## Usage",
        "",
        f"- Archetype: `{display}`",
        f"- Metric reference file: `references/{reference}`",
        "- These metrics are observation baselines, not universal KPI targets.",
        "- Record the original game's observed band before proposing remake target bands.",
        "",
        "## Metric Table",
        "",
        "| ID | Category | Metric | Unit | How to sample | Why it matters |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for metric_id, category, metric_name, unit, method, why in rows:
        lines.append(
            f"| {metric_id} | {category} | {metric_name} | {unit} | {method} | {why} |"
        )

    lines.extend(["", evidence_section_block("en").rstrip()])
    return {ARCHETYPE_METRIC_FILE_NAME: "\n".join(lines).rstrip() + "\n"}


def build_archetype_metrics_csv(archetype: str, language: str) -> str:
    _ = language
    rows = ARCHETYPE_METRICS[archetype]["rows"]
    csv_rows = [[
        "metric_id",
        "category",
        "metric_name",
        "unit",
        "measurement_method",
        "why_it_matters",
        "observed_band",
        "target_band",
        "confidence",
        "source_ids",
        "notes",
    ]]
    for metric_id, category, metric_name, unit, method, why in rows:
        csv_rows.append(
            [metric_id, category, metric_name, unit, method, why, "", "", "Open", "", ""]
        )
    return render_csv(csv_rows)


def build_experiment_file(
    game: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    archetype_label = archetype_display(archetype, "en")
    rows = prioritized_experiment_rows("en", archetype)
    lines = [
        f"# {game} Cross-Archetype Experiment Design",
        "",
        "## Usage",
        "",
        "- Reference file: `references/experiment-design.md`",
        f"- Current primary lens: `{archetype_label}`",
        "- These experiments convert loose impressions into sampleable, comparable, reviewable evidence.",
        "- Record observed original-game bands before proposing remake target bands.",
        "",
        "## Recommended First Pass",
        "",
    ]
    if archetype:
        for experiment_id, _category, name, _applies_to, _unit, sample_size, _method, _why, priority in rows[:4]:
            lines.append(
                f"- `{experiment_id}` `{priority}`: {name}, recommended sample size `{sample_size}`."
            )
    else:
        lines.append(
            "- Without an archetype, start with `EXP-03`, `EXP-04`, and `EXP-05`."
        )
    lines.extend(
        [
            "",
            "## Experiment Catalog",
            "",
            "| ID | Category | Experiment | Applies to | Unit | Recommended sample size | Priority | Method | Value |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for experiment_id, category, name, applies_to, unit, sample_size, method, why, priority in rows:
        lines.append(
            f"| {experiment_id} | {category} | {name} | {applies_to} | {unit} | {sample_size} | {priority} | {method} | {why} |"
        )

    lines.extend(["", evidence_section_block("en").rstrip()])
    return {EXPERIMENT_FILE_NAME: "\n".join(lines).rstrip() + "\n"}


def build_experiment_summary_placeholder(
    game: str, language: str, archetype: str | None
) -> dict[str, str]:
    _ = language
    archetype_label = archetype_display(archetype, "en")
    content = f"""\
# {game} Experiment Summary

## Status

- Current primary lens: `{archetype_label}`
- This file is intended to be regenerated by `summarize_experiments.py`.

## Regeneration Command

```bash
python3 "${{GAME_REMAKE_RESEARCH:-{SKILL_ROOT}}}/scripts/summarize_experiments.py" \\
  --docs-dir . \\
  --mode full
```

## Notes

- Update `data/experiment-plan.csv`, `data/experiment-observations.csv`, and `data/experiments/*.csv` before regenerating.
- Run the command from the pack root.
- If the pack moves to another machine, set `GAME_REMAKE_RESEARCH` to the installed skill root before running the command.
- If metric rollup has already been run, the summary will also include a snapshot of `data/archetype-metrics.csv`.
- For final dossier use, also generate `10-experiment-summary-compact.md`:
  `summarize_experiments.py --mode compact --output 10-experiment-summary-compact.md`
"""
    return {EXPERIMENT_SUMMARY_FILE_NAME: dedent(content)}


def prioritized_experiment_rows(
    language: str, archetype: str | None
) -> list[tuple[str, str, str, str, str, str, str, str, str]]:
    _ = language
    rows = EXPERIMENT_SPECS
    prioritized = []
    for experiment_id, category, name, applies_to, unit, sample_size, method, why in rows:
        priority = resolve_experiment_priority(experiment_id, applies_to, archetype)
        prioritized.append(
            (
                experiment_id,
                category,
                name,
                applies_to,
                unit,
                sample_size,
                method,
                why,
                priority,
            )
        )
    prioritized.sort(key=lambda row: (PRIORITY_ORDER[row[8]], row[0]))
    return prioritized


def resolve_experiment_priority(
    experiment_id: str, applies_to: str, archetype: str | None
) -> str:
    if not archetype:
        return "medium"
    explicit = ARCHETYPE_EXPERIMENT_PRIORITIES.get(archetype, {}).get(experiment_id)
    if explicit:
        return explicit
    if applies_to == "all" or archetype in applies_to.split("|"):
        return "medium"
    return "low"


def build_experiment_plan_csv(language: str, archetype: str | None) -> str:
    rows = prioritized_experiment_rows(language, archetype)
    csv_rows = [[
        "experiment_id",
        "category",
        "experiment_name",
        "applies_to",
        "unit",
        "recommended_sample_size",
        "method",
        "status",
        "priority",
        "notes",
    ]]
    for experiment_id, category, name, applies_to, unit, sample_size, method, _why, priority in rows:
        csv_rows.append(
            [experiment_id, category, name, applies_to, unit, sample_size, method, "not-started", priority, ""]
        )
    return render_csv(csv_rows)


def build_experiment_observations_csv(language: str) -> str:
    _ = language
    rows = EXPERIMENT_SPECS
    csv_rows = [["experiment_id", "experiment_name", "detail_file", "last_updated", "status", "owner", "notes"]]
    for experiment_id, _category, name, _applies_to, _unit, _sample_size, _method, _why in rows:
        csv_rows.append(
            [experiment_id, name, EXPERIMENT_DETAIL_TEMPLATES[experiment_id]["file"], "", "not-started", "", ""]
        )
    return render_csv(csv_rows)


def build_experiment_detail_templates() -> dict[str, str]:
    files: dict[str, str] = {}
    for spec in EXPERIMENT_DETAIL_TEMPLATES.values():
        files[spec["file"]] = render_csv([spec["header"], spec["sample"]])
    return files


def build_archetype_metric_links_csv(archetype: str) -> str:
    csv_rows = [[
        "metric_id",
        "experiment_id",
        "detail_file",
        "value_columns",
        "aggregation",
        "status",
        "notes",
    ]]
    for metric_id, experiment_id, detail_file, value_columns, aggregation, status, notes in ARCHETYPE_METRIC_LINKS[archetype]:
        csv_rows.append(
            [metric_id, experiment_id, detail_file, value_columns, aggregation, status, notes]
        )
    return render_csv(csv_rows)
def build_documents_en(
    game: str, version_scope: str, archetype: str | None
) -> dict[str, str]:
    archetype_line = archetype_scope_line(archetype, "en")
    evidence_block = indent(evidence_section_block("en").rstrip(), "            ")
    return {
        "00-overview-and-source-ledger.md": dedent(
            f"""\
            # {game} Remake Research Overview

            ## Scope Lock

            - Target game: `{game}`
            - Baseline version: `{version_scope}`
            {archetype_line}
            - Research goal:
            - Target output: reference study / vertical slice / full remake
            - Platforms in scope:
            - Regions in scope:

            ## Research Questions

            - Which player fantasy and game pillars must survive the remake?
            - Which systems are historical constraints, monetization artifacts, or multiplayer-only dependencies?
            - Which parts require direct fidelity and which parts can be adapted?

            ## Source Ledger

            | ID | Type | Link or location | Version/date | Confidence | Notes |
            | --- | --- | --- | --- | --- | --- |
            |  | Official |  |  | Confirmed |  |
            |  | Gameplay footage |  |  | Confirmed |  |
            |  | Wiki / datamine |  |  | Inferred |  |

            ## Evidence Citation Rule

            - Use inline ledger anchors like `S-id` inside `Confirmed Facts` and `Inferred Model`.
            - Keep remake proposals separate from evidence-backed observations.

            ## Confidence Policy

            - Confirmed:
            - Inferred:
            - Open:

            ## Top Unknowns

            - Unknown:
            - Impact:
            - Validation plan:
            """
        ),
        "01-product-and-player-experience.md": dedent(
            f"""\
            # {game} Product And Player Experience

            ## Product Definition

            - Genre:
            - Audience:
            - Comparable titles:
            - Business model:
            - Session length:

            ## North Star Experience

            - Fantasy:
            - Pillars:
            - Must-preserve moments:
            - Must-adapt elements:

            ## Player Journey

            - Onboarding:
            - Midgame:
            - Endgame / mastery:
            - Long-term goals:

            ## Loop Design

            - Core loop:
            - Session loop:
            - Meta loop:
            - Retention hooks:

            ## Product Management Notes

            - Positioning:
            - Scope cuts:
            - KPI proxies:
            - Shipping risks:

{evidence_block}
            """
        ),
        "02-systems-and-gameplay.md": dedent(
            f"""\
            # {game} Systems And Gameplay

            ## Control Grammar

            - Inputs:
            - Context-sensitive actions:
            - Buffering / cancels:

            ## Movement And Combat

            - Movement verbs:
            - Combat verbs:
            - Hit timing:
            - Damage feedback:
            - Camera behavior:

            ## Challenge Structure

            - Enemy taxonomy:
            - Encounter grammar:
            - Map / mission flow:
            - Failure and recovery:

            ## Gameplay Feel Notes

            - Responsiveness drivers:
            - Readability rules:
            - Skill ceiling:

{evidence_block}
            """
        ),
        "03-economy-and-balance.md": dedent(
            f"""\
            # {game} Economy And Balance

            ## Resource Map

            - Primary currencies:
            - Secondary currencies:
            - Upgrade materials:
            - Energy / cooldown / capacity constraints:

            ## Faucets And Sinks

            - Sources:
            - Sinks:
            - Scarcity points:
            - Recovery paths:

            ## Stat And Progression Model

            - Core stats:
            - Progression bands:
            - Upgrade steps:
            - Build commitment points:

            ## Formula Capture

            - Damage formula:
            - Reward formula:
            - Upgrade success / failure logic:
            - TTK or difficulty targets:

            ## Tuning Risks

            - Dominant strategies:
            - Grind cliffs:
            - Economy inflation risks:

{evidence_block}
            """
        ),
        "04-content-art-audio-narrative.md": dedent(
            f"""\
            # {game} Content, Art, Audio, And Narrative

            ## Content Taxonomy

            - Modes / content types:
            - Level or map families:
            - Progression milestones:

            ## Art Direction

            - Shape language:
            - Color language:
            - Camera framing:
            - UI language:
            - Asset categories:

            ## Animation

            - Locomotion states:
            - Combat states:
            - Boss telegraphs:
            - Timing notes:

            ## Music And Audio

            - Cue map:
            - Dynamic rules:
            - SFX taxonomy:
            - Mix priorities:

            ## Copywriting And Narrative

            - Glossary:
            - UI tone:
            - Quest / mission writing pattern:
            - World pillars:
            - Story structure:

{evidence_block}
            """
        ),
        "05-client-architecture-and-production.md": dedent(
            f"""\
            # {game} Client Architecture And Production

            ## Product Targets

            - Platforms:
            - Performance budgets:
            - Input devices:
            - Online / offline assumptions:

            ## Runtime Architecture

            - Core modules:
            - System boundaries:
            - Data ownership:
            - Save model:
            - Content pipeline:

            ## Tools And Workflow

            - Editor tooling:
            - Debug tooling:
            - Data authoring flow:
            - Build pipeline:

            ## Production Plan

            - Vertical slice:
            - Milestones:
            - Staffing assumptions:
            - Outsourcing assumptions:

            ## Risk Register

            - Technical risks:
            - Content risks:
            - Schedule risks:

{evidence_block}
            """
        ),
        "06-replica-backlog-and-acceptance.md": dedent(
            f"""\
            # {game} Replica Backlog And Acceptance

            ## Prioritized Backlog

            | Priority | Area | Feature | Why it matters | Acceptance signal |
            | --- | --- | --- | --- | --- |
            | P0 | Core loop |  |  |  |
            | P1 | Progression |  |  |  |
            | P2 | Content |  |  |  |

            ## Vertical Slice Scope

            - Mandatory systems:
            - Mandatory content:
            - Mandatory polish:

            ## Full Production Scope

            - Content expansion plan:
            - Live-ops or post-launch assumptions:
            - Deliberate exclusions:

            ## Acceptance Criteria

            - Player feel:
            - Progression pacing:
            - Economy stability:
            - Art and animation readability:
            - Technical stability:

            ## Open Gaps And Validation

            - Gap:
            - Risk:
            - Validation task:
            """
        ),
        "99-research-log.md": dedent(
            f"""\
            # {game} Research Log

            ## Observation Entries

            | Date | Source ID | Topic | Observation | Confidence | Follow-up |
            | --- | --- | --- | --- | --- | --- |
            |  |  |  |  |  |  |

            ## Frame / Timing Notes

            - Clip:
            - Timestamp:
            - Observation:

            ## Contradictions To Resolve

            - Contradiction:
            - Sources:
            - Next step:
            """
        ),
    }


def build_support_files_en(
    game: str, version_scope: str, archetype: str | None
) -> dict[str, str]:
    slug = slugify(game)
    files = {
        "research-manifest.yaml": dedent(
            f"""\
            game: "{game}"
            slug: "{slug}"
            baseline_version: "{version_scope}"
            archetype: "{archetype or ''}"
            secondary_lenses: []
            research_goal: ""
            output_mode: "full remake pack"
            platforms: []
            regions: []
            languages: []
            historical_baseline: ""
            current_live_baseline: ""
            chosen_remake_baseline: ""
            constraints: []
            assumptions: []
            """
        ),
        "data/source-ledger.csv": dedent(
            """\
            source_id,source_type,title,url_or_location,platform,region,version_or_date,confidence,notes
            ,official,,,,,,Confirmed,
            ,gameplay-footage,,,,,,Confirmed,
            ,wiki-or-datamine,,,,,,Inferred,
            """
        ),
        "data/formula-catalog.csv": dedent(
            """\
            formula_id,system,name,expression,variables,units,version_scope,confidence,source_ids,notes
            F1,combat,,,,,,,,
            F2,economy,,,,,,,,
            """
        ),
        "data/asset-taxonomy.csv": dedent(
            """\
            asset_id,discipline,category,subtype,reusable_or_bespoke,priority,source_ids,notes
            A1,art,character,,,,,
            A2,animation,combat-state,,,,,
            A3,audio,sfx-class,,,,,
            """
        ),
        "data/risk-register.csv": dedent(
            """\
            risk_id,category,description,impact,likelihood,owner,mitigation,validation
            R1,design,,,,,,,
            R2,technical,,,,,,,
            """
        ),
        "data/role-coverage.csv": dedent(
            """\
            role,status,key_findings,missing_evidence,output_file
            product-manager,not-started,,,01-product-and-player-experience.md
            professional-game-designer,not-started,,,01-product-and-player-experience.md
            gameplay-designer,not-started,,,02-systems-and-gameplay.md
            balance-designer,not-started,,,03-economy-and-balance.md
            art,not-started,,,04-content-art-audio-narrative.md
            animation,not-started,,,04-content-art-audio-narrative.md
            music-audio,not-started,,,04-content-art-audio-narrative.md
            copywriting,not-started,,,04-content-art-audio-narrative.md
            narrative,not-started,,,04-content-art-audio-narrative.md
            game-client-architect,not-started,,,05-client-architecture-and-production.md
            lead-engineer,not-started,,,05-client-architecture-and-production.md
            """
        ),
        "data/experiment-plan.csv": build_experiment_plan_csv("en", archetype),
        "data/experiment-observations.csv": build_experiment_observations_csv("en"),
    }
    files.update(build_experiment_detail_templates())

    if archetype:
        files["data/archetype-checklist.csv"] = build_archetype_checklist_csv(
            archetype, "en"
        )
        files["data/archetype-metrics.csv"] = build_archetype_metrics_csv(
            archetype, "en"
        )
        files["data/archetype-metric-links.csv"] = build_archetype_metric_links_csv(
            archetype
        )
    return files


def write_files(out_dir: Path, files: dict[str, str], force: bool) -> list[Path]:
    created: list[Path] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        destination = out_dir / name
        if destination.exists() and not force:
            raise FileExistsError(
                f"{destination} already exists. Re-run with --force to overwrite."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content.rstrip() + "\n", encoding="utf-8")
        created.append(destination)
    return created




def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a remake-research document pack."
    )
    parser.add_argument("--game", required=True, help="Target game title.")
    parser.add_argument("--out", required=True, help="Output directory.")
    parser.add_argument(
        "--version-scope",
        help="Version, region, platform, or date scope to stamp into the docs.",
    )
    parser.add_argument(
        "--language",
        choices=("en",),
        default="en",
        help="Template language. Defaults to en.",
    )
    parser.add_argument(
        "--archetype",
        choices=ARCHETYPE_CHOICES,
        help="Optional genre lens: mmo, arpg, roguelike, or card.",
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help=f"Also create {DOSSIER_TEMPLATE_FILE_NAME} as a single-file dossier template.",
    )
    parser.add_argument(
        "--with-support-files",
        action="store_true",
        help="Also create manifest and CSV support templates under data/, plus 10-experiment-summary.md.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out).expanduser().resolve()
    language = args.language
    version_scope = format_version_scope(args.version_scope, language)

    files = build_documents(args.game, version_scope, language, args.archetype)
    files.update(build_archetype_file(args.game, language, args.archetype))
    files.update(build_archetype_metric_file(args.game, language, args.archetype))
    files.update(build_experiment_file(args.game, language, args.archetype))

    if args.single_file:
        files.update(
            build_single_file_template(
                args.game, version_scope, language, args.archetype
            )
        )

    if args.with_support_files:
        files.update(
            build_support_files(
                args.game, version_scope, language, args.archetype
            )
        )

    if args.with_support_files:
        files.update(
            build_experiment_summary_placeholder(args.game, language, args.archetype)
        )

    created = write_files(out_dir, files, args.force)
    for destination in created:
        print(f"Wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
