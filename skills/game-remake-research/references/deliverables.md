# Deliverables

## Contents

- `Default Structure`
- `Required Content Per File`
- `Cross-Document Standards`
- `Done Criteria`

Use the scaffold script to create the pack. The default structure is:

1. `00-overview-and-source-ledger.md`
2. `01-product-and-player-experience.md`
3. `02-systems-and-gameplay.md`
4. `03-economy-and-balance.md`
5. `04-content-art-audio-narrative.md`
6. `05-client-architecture-and-production.md`
7. `06-replica-backlog-and-acceptance.md`
8. `09-experiment-design.md`
9. `99-research-log.md`

If the user wants one long document, merge the same sections in that order.

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/merge_remake_docs.py" \
  --docs-dir ./docs/remake-maplestory \
  --mode full
```

- `merge_remake_docs.py --mode full` keeps the full pack structure and writes `remake-dossier.md` by default.
- `merge_remake_docs.py --mode compact` omits `09-experiment-design.md` and prefers `10-experiment-summary-compact.md`, falling back to `10-experiment-summary.md`.

When `--archetype` is set, also create:

10. `07-archetype-specific-template.md`
11. `08-archetype-metric-baselines.md`

Insert those archetype docs before `09-experiment-design.md` when merging in numeric file order.

When `--with-support-files` is set, also scaffold:

- `10-experiment-summary.md` as the summary placeholder that `summarize_experiments.py` later regenerates from CSV support data
- `research-manifest.yaml`
- `data/source-ledger.csv`
- `data/formula-catalog.csv`
- `data/asset-taxonomy.csv`
- `data/risk-register.csv`
- `data/role-coverage.csv`
- `data/experiment-plan.csv`
- `data/experiment-observations.csv`
- `data/experiments/*.csv` typed raw-observation templates
- `data/archetype-checklist.csv` when `--archetype` is set
- `data/archetype-metrics.csv` when `--archetype` is set
- `data/archetype-metric-links.csv` when `--archetype` is set

Optional generated derivative for compact dossier merges:

12. `10-experiment-summary-compact.md`

Optional manual single-file template created by `scaffold_remake_docs.py --single-file`:

13. `remake-dossier-template.md`

Optional generated derivatives created by follow-up scripts:

- `reports/evidence-link-audit.md` optional evidence-link integrity report
- `reports/pack-status.md` optional generated status report
- `reports/pack-status-compact.md` optional compact status report
- `reports/handoff-bundle.md` optional generated handoff manifest
- `handoff-full-dossier.md` optional generated full handoff dossier
- `handoff-compact-dossier.md` optional generated compact handoff dossier

If the user wants a merged dossier after writing the pack, use `merge_remake_docs.py --docs-dir ./docs/remake-maplestory`.
Keep the working pack in English until audit, evidence, status, and handoff scripts are done; translate only a derived dossier or handoff artifact afterward.
Generate `10-experiment-summary-compact.md` first when the goal is an external-facing or shorter dossier.
Run `audit_remake_pack.py` before final handoff so missing sections, empty scaffolds, and incomplete support files are caught explicitly.
Run `audit_evidence_links.py` when the pack uses source ledgers and support CSVs so dangling or stale source IDs are caught before handoff.
Generate `reports/pack-status.md` when reviewers need a quick production-style progress snapshot without reading every file.
Use `build_handoff_bundle.py` when reviewers want the compact dossier, status report, and audit manifest generated in one pass.
If generated derivatives already exist, keep them fresh: stale experiment summaries, evidence-link audits, status reports, handoff dossiers, and handoff manifests now show up as audit warnings.

## Required Content Per File

### 00 Overview And Source Ledger

- scope lock
- version and platform baseline
- research goals
- source ledger with dates
- confidence policy
- top unknowns

### 01 Product And Player Experience

- genre and audience
- market positioning
- fantasy and pillars
- macro loop and session loop
- onboarding, midgame, endgame journey
- retention or progression hooks
- preserve vs adapt decisions

### 02 Systems And Gameplay

- control grammar
- movement and combat rules
- camera and feedback stack
- enemy or challenge taxonomy
- map or mission structure
- failure and recovery states
- gameplay-specific source evidence

### 03 Economy And Balance

- currencies and materials
- faucets and sinks
- stat model
- progression bands
- upgrade formulas
- drop logic or reward cadence
- target metrics and tuning risks

### 04 Content, Art, Audio, Narrative

- content taxonomy
- art pillars and UI language
- animation inventory and timing notes
- music cue map and SFX taxonomy
- copy tone and terminology
- narrative structure and quest or mission writing patterns

### 05 Client Architecture And Production

- platform targets
- runtime architecture
- scene or screen flow
- data boundaries
- save model
- toolchain and content pipeline
- performance budgets
- milestone plan and risk register

### 06 Replica Backlog And Acceptance

- prioritized backlog
- vertical-slice scope
- full-production scope
- acceptance criteria
- unresolved gaps and validation tasks
- IP-sensitive items to reskin if the output is intended for public shipping

### 99 Research Log

- raw observations
- clip or source references
- frame or timing notes
- unresolved contradictions
- follow-up tasks

## Cross-Document Standards

Every major section should contain:

- `Confirmed facts`
- `Inferred model`
- `Remake decisions`
- `Open questions`

Every formula should contain:

- variable definitions
- units
- assumptions
- version scope

Every production-facing section should contain:

- what is reusable
- what is bespoke
- what is high risk

## Done Criteria

The pack is not done until:

- each core role is represented
- the baseline version is explicit
- the source ledger exists
- speculative points are labeled
- architecture and engineering sections are actionable
- backlog items are prioritized
- acceptance criteria are testable
- `audit_remake_pack.py` reports no errors
