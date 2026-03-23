# Evidence Link Audit

Use this reference when a remake research pack has a source ledger and you need to verify that every structured `source_id` or `source_ids` reference still resolves cleanly.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Purpose

`audit_evidence_links.py` checks:

- duplicate IDs inside `data/source-ledger.csv`
- references to unknown source IDs
- ledger IDs that were never cited anywhere
- structured rows that contain research payload but no source reference
- markdown evidence sections that contain analysis text but no inline `S-id` citations
- evidence links inside:
  - `data/formula-catalog.csv`
  - `data/asset-taxonomy.csv`
  - `data/archetype-metrics.csv`
  - `data/experiments/*.csv`
  - `01-*.md` to `09-*.md` dossier sections with `Confirmed Facts` / `Inferred Model`
  - `99-research-log.md`

This script is about evidence traceability, not content quality or balance correctness.

## Workflow

1. Update `data/source-ledger.csv`.
2. Update support CSVs and typed experiment sheets.
3. Run:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/audit_evidence_links.py" \
  --docs-dir ./docs/remake-maplestory \
  --output reports/evidence-link-audit.md
```

4. Fix unknown source IDs first.
5. Then fix dossier sections that already contain analysis but still lack inline `S-id` anchors.
6. Finally decide whether unused ledger IDs or blank source refs are acceptable.

Use `--strict` when warnings should also fail the check.
Use [citation-style.md](citation-style.md) if the audit is warning about missing inline citations in Markdown sections.

## Output Semantics

- `PASS`: no dangling or suspicious evidence links were found
- `WARN`: no hard link failures, but stale or incomplete evidence references still exist
- `FAIL`: duplicate ledger IDs or unknown source IDs were found

Markdown citation warnings are content-aware: blank scaffold sections are ignored, but once `Confirmed Facts` or `Inferred Model` has real text, that section is expected to cite ledger IDs inline.
Downstream status and handoff artifacts rank evidence problems by severity: duplicate or unknown source IDs first, then blank source refs, then uncited evidence sections, then unused ledger cleanup.

For handoff generation, `build_handoff_bundle.py` can emit this report automatically.
