# Handoff Bundle

Use this reference when a remake research pack should be packaged for review, takeover, or milestone handoff in one command.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Purpose

`build_handoff_bundle.py` orchestrates the derived artifacts that usually get regenerated together:

- optional archetype metric rollup
- experiment summaries
- status reports
- evidence-link audit report
- handoff dossiers
- final audit manifest

This is the fastest path when the user wants "give me the current handoff pack" rather than asking for each derived artifact one by one.

## Workflow

1. Update the research pack and support CSVs.
2. If experiment data changed, decide whether metric rollup should run first.
3. Run:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/build_handoff_bundle.py" \
  --docs-dir ./docs/remake-maplestory \
  --dossier-mode compact \
  --report-mode both \
  --rollup-metrics
```

Default generated outputs:

- `10-experiment-summary.md`
- `10-experiment-summary-compact.md` when compact dossier output is requested
- `reports/evidence-link-audit.md` when the pack has a source ledger
- `reports/pack-status.md`
- `reports/pack-status-compact.md`
- `handoff-compact-dossier.md`
- `reports/handoff-bundle.md`

Use `--dossier-mode both` when reviewers need both full and compact dossiers.

## Expectations

- This script packages the current state; it does not replace research judgment.
- Keep `reports/` outputs outside the main dossier merge path.
- Use `--strict-audit` when the handoff should fail on warnings, not only on errors.
- The bundle manifest now surfaces evidence-link counts directly, so reviewers can see citation gaps and source-ID integrity issues without opening the full audit report first.
- It also includes a first example for each evidence problem class, so the handoff page itself points to the first broken `S-id`, blank source-ref row, unused ledger entry, or uncited doc section.
- Evidence findings are severity-ranked, so duplicate or unknown source IDs show up before blank refs, citation gaps, and unused-ledger cleanup.
- The bundle's recommended next actions follow the same priority order and prefix each action with its severity.
- Placeholder cleanup recommendations are also role-aware, so overview/source-ledger work appears before lower-priority backlog or log cleanup.
- The bundle audit section groups structural findings into scope/structure, template placeholders, support data, and progress signals for faster handoff scanning.
- Generated-artifact freshness is also grouped separately, so inherited stale summaries, handoff dossiers, or audit exports do not get buried under generic progress debt.
- The snapshot header also reports stale-artifact counts directly, so reviewers can tell immediately whether any derivative reports or dossiers still lag behind newer pack inputs.
- In compact handoff output, each warning group is capped to the first two items and then shows an omitted-count line for the remainder.
- Compact status artifacts inside the bundle also fold lower-priority core-doc rows, keeping the highest-risk files visible first.
- Those compact status artifacts also flip support/role/archetype/experiment sections into anomaly-first summaries, so takeover readers see blocked roles, missing support rows, and experiment debt before generic healthy counts.
- The bundle's next-action list now names the first blocked experiment IDs directly when plan statuses, registry statuses, or typed raw samples still lag behind.
- When inherited handoff dossiers are stale, the same next-action list also names the exact dossier files that should be rebuilt.
- When stale summaries, reports, dossiers, and manifests pile up together, that same next-action list now collapses them into one inferred bundle-regeneration command.
- When only one stale artifact class remains, the next-action list now emits the direct script command for that class instead of a generic reminder.
- Those generated command snippets assume the shell is already inside the pack root, so they use `--docs-dir .`.
- If the current generated artifact was explicitly generated with `--language en`, those stale-repair commands now preserve that same language flag.
- If a stale handoff dossier was originally generated with `--include-log`, the repair command also preserves that flag.
- If stale experiment summaries depend on archetype metric rollup support, the generated bundle-refresh command now preserves `--rollup-metrics` too.
- When the bundle regenerates both status-report variants in one pass, those reports also ignore each other during freshness audit so the pair does not self-report stale sibling warnings.
- Because the bundle regenerates summaries, evidence audits, and requested status variants before its final audit pass, it also clears most stale-artifact warnings automatically during packaging.
- Existing experiment-summary variants are also refreshed during bundling, so a stale `10-experiment-summary.md` does not linger just because the handoff request only asked for a compact dossier.
