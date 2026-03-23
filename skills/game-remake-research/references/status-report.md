# Status Report

Use this reference when a remake research pack needs a one-file progress snapshot for handoff, takeover, producer review, or milestone check-ins.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Purpose

`build_pack_status_report.py` generates a markdown report that combines:

- current audit result
- evidence-traceability snapshot from `audit_evidence_links.py`
- core-doc structural readiness
- support-data population snapshot
- role-coverage progress
- archetype checklist and metric progress
- experiment status and raw-sample counts
- recommended next actions

The report is meant to answer "How complete is this pack right now?" without forcing the reader to inspect every file.

## Workflow

1. Update the research pack.
2. Run audit first if the structure may be broken.
3. Generate the report:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/build_pack_status_report.py" \
  --docs-dir ./docs/remake-maplestory \
  --mode full
```

Use `--mode both` to regenerate `reports/pack-status.md` and `reports/pack-status-compact.md` together.
When both variants are generated in one run, the two outputs now ignore each other during freshness audit so they do not self-report sibling stale warnings.

Default output:

- `reports/pack-status.md` for `--mode full`
- `reports/pack-status-compact.md` for `--mode compact`

Use `--language en` when you want to pin the output explicitly. `--language auto` currently resolves to `en`.

`--mode full` now expands the evidence section into actionable detail tables:

- unknown source IDs with sample reference locations
- duplicate source IDs
- populated support rows that still lack source refs
- unused ledger IDs
- docs whose populated `Confirmed Facts` / `Inferred Model` sections still lack inline `S-id` anchors

These evidence findings are ordered by severity so blocker-class ID integrity problems surface before lower-priority citation or cleanup work.
The generated `Recommended Next Actions` list uses the same severity order and prefixes each item with its priority.
`--mode full` also surfaces placeholder hotspots by document role, so overview/source-ledger cleanup is separated from main analysis docs and low-priority tail docs such as backlog/log files.
Audit findings are grouped into scope/structure, template placeholders, support data, and progress signals so takeover readers can scan by problem class instead of reading one long warning list.
Generated-artifact freshness now appears as its own issue group when inherited packs contain stale experiment summaries, evidence-link audits, status reports, handoff dossiers, or handoff manifests.
The snapshot header also surfaces those stale-artifact counts directly, so takeover readers can see freshness debt for reports and dossiers before they read the grouped warnings.
In `--mode compact`, each group shows the first two findings and then an omitted-count line if more items remain in that group.
The compact core-document table also keeps only the highest-risk docs in view and reports how many remaining docs were folded.
Compact support, role, archetype, and experiment sections are anomaly-first: they call out missing source/formula/asset/risk population, blocked `not-started` roles, remaining checklist or metric gaps, and raw-sample / registry debt before they fall back to healthy progress summaries.
When experiment support is stalled, the compact experiment snapshot and next-action list now cite the leading experiment IDs directly so takeover readers know which typed sheets to update first.
When generated artifacts are stale, the next-action list also points to the exact summaries, reports, or dossiers that should be regenerated first.
If freshness debt spans multiple artifact classes, those next actions now collapse into one inferred `build_handoff_bundle.py` command instead of listing four separate refresh bullets.
If only one artifact class is stale, the next-action line now includes the direct repair command for that class.
Those command snippets assume the current shell is already in the research-pack root, so they use `--docs-dir .`.
If the current generated artifact was explicitly generated with `--language en`, the stale-repair commands now preserve that same language flag, including experiment-summary refresh commands.
If the stale artifact is a handoff dossier that was originally generated with `--include-log`, the repair command now preserves that flag too.
If stale experiment summaries depend on archetype metric rollup support, the repair command now includes `rollup_experiment_metrics.py` before summary regeneration.

## Expectations

- This report is a management and handoff artifact, not a replacement for the pack itself.
- Keep it outside the root merge set so it does not get folded into the final dossier accidentally.
- Regenerate it after major progress updates, especially after audit fixes, evidence-link fixes, role-coverage changes, metric rollups, or experiment updates.
