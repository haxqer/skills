---
name: "game-remake-research"
description: "Source-backed analysis / 拆解 of an existing game into a remake / 复刻 teardown, benchmark / 对标, competitor study / 竞品分析, dossier, spec, formula set, experiment plan, handoff bundle, or vertical-slice research pack / 调研包. Use when the deliverable must separate original-game facts, inferences, and remake decisions. Do not use for generic brainstorming, casual recommendations, implementation-only work, or one-off mechanic explanations."
---

# Game Remake Research

Turn an existing game into source-backed remake documentation. Use this skill for remake teardowns, benchmarks, competitor studies, or vertical-slice research packs, not for generic brainstorming or casual comparisons.

## Start

- Lock the target game, edition or era, platform set, region, and time slice before writing conclusions.
- If the target is live-service and the user says `latest`, `current`, `live`, `today`, or similar, browse first and cite exact dates or build windows.
- Treat repo-local GDDs, spreadsheets, and technical docs as target-state inputs, not evidence about the original game.
- Pick one primary archetype lens. Read `references/template-selection.md` first, then load only one explicit pair unless a secondary lens is clearly required: `mmo -> template-mmo.md + metrics-mmo.md`, `arpg -> template-arpg.md + metrics-arpg.md`, `roguelike -> template-roguelike.md + metrics-roguelike.md`, `card -> template-card.md + metrics-card.md`.
- Scaffold the output pack before deep research. For packs that will be audited or handed off, pass a concrete `--version-scope` and usually add `--with-support-files`.
- Scaffold templates currently support only `--language en`. Keep the working research pack in English if you still need `audit_remake_pack.py`, `audit_evidence_links.py`, `build_pack_status_report.py`, or `build_handoff_bundle.py`. If the final deliverable must ship in another language, translate a derived dossier or handoff artifact after the English pack is complete.

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/scaffold_remake_docs.py" \
  --game "MapleStory" \
  --out ./docs/remake-maplestory \
  --archetype mmo \
  --version-scope "KMS baseline as observed on 2026-03-01" \
  --language en \
  --with-support-files
```

Example assumes `$GAME_REMAKE_RESEARCH` points at the skill root. If that variable is unset, run the same script from this skill's local `scripts/` directory.
Add `--with-support-files` when the pack should later regenerate experiment summaries or run evidence, status, and handoff tooling against structured support data.
Add `--single-file` only when you also want `remake-dossier-template.md` as a manual one-file writing template.

## Workflow

1. Read `references/research-workflow.md` and lock scope before collecting sources.
2. Use `references/role-matrix.md` to cover every analysis lens in one coherent pack.
3. Use `references/deliverables.md` to keep the pack structure and section outputs aligned.
4. End every major section with open questions and the minimum validation step needed to close them.

## Load These References As Needed

- Planning and structure: `references/template-selection.md`, `references/research-workflow.md`, `references/role-matrix.md`, `references/deliverables.md`
- Archetype lenses: `references/template-mmo.md`, `references/metrics-mmo.md`, `references/template-arpg.md`, `references/metrics-arpg.md`, `references/template-roguelike.md`, `references/metrics-roguelike.md`, `references/template-card.md`, `references/metrics-card.md`
- Evidence and capture: `references/evidence-rubric.md`, `references/citation-style.md`, `references/capture-methods.md`
- Experiments and metrics: `references/experiment-design.md`, `references/metric-rollup.md`, `references/experiment-summary.md`, `references/evidence-link-audit.md`
- Finish and handoff: `references/pack-audit.md`, `references/status-report.md`, `references/handoff-bundle.md`

## Evidence Rules

- Prefer sources in this order: official sites, manuals, patch notes, developer talks, direct gameplay footage, reputable wikis or datamines, then secondary commentary.
- Stamp important claims as `Confirmed`, `Inferred`, or `Open`.
- In `Confirmed Facts` and `Inferred Model`, cite ledger IDs inline with the claim, for example `S12` or `S12, S18`.
- Attach exact dates, versions, regions, and platforms to balance values, drop rules, UI flows, monetization details, and feature availability.
- If internals are unknowable, infer from repeated observation and explain the inference path instead of pretending certainty.
- Keep original-game facts separate from remake decisions.

## Scripts

- Core pack flow: `scaffold_remake_docs.py`, `merge_remake_docs.py`
- Experiment flow: `rollup_experiment_metrics.py`, `summarize_experiments.py`
- Audit flow: `audit_evidence_links.py`, `audit_remake_pack.py`
- Review and handoff: `build_pack_status_report.py`, `build_handoff_bundle.py`

If the user wants one final document, merge the pack in the order defined by `references/deliverables.md`.

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/merge_remake_docs.py" \
  --docs-dir ./docs/remake-maplestory \
  --mode full
```

## Common Failure Modes

- Mixing regions, eras, or platforms without labeling them.
- Loading all four archetype templates when one primary lens would do.
- Writing strong conclusions without an experiment plan for the highest-risk unknowns.
- Confusing inferred formulas with confirmed formulas.
- Writing opinions without backlog, risk, or acceptance criteria.
- Describing art direction without asset categories and reuse strategy.
- Describing feel without timing, state, cancel, or camera rules.
- Producing architecture prose without boundaries, hot paths, or tool implications.

## Check Before You Finish

- Confirm the user can see which version or build the research refers to.
- Confirm each role's output is reflected in the final pack rather than left as raw notes.
- Confirm formulas include units, variables, and assumptions.
- Confirm asset and animation sections describe production-ready categories, not just adjectives.
- Confirm architecture and engineering sections define boundaries, sequencing, and risks.
- Confirm unresolved gaps include a validation plan.
