# Citation Style

Read this when writing the dossier itself, not just the supporting CSVs.

## Core Rule

- In `Confirmed Facts` and `Inferred Model`, cite ledger IDs inline with the claim.
- Use IDs that already exist in `data/source-ledger.csv`.
- Keep `Remake Decisions` separate from evidence-backed observations. If a decision depends on a source or experiment, cross-reference the relevant `S-id` and `EXP-id`.

## Acceptable Patterns

- `Party size cap is 4 in the observed dungeon flow. [S12]`
- `The reward bucket appears to swap after account level 30 rather than chapter clear. [S07, S14]`
- `Keep the 4-player cap, but shorten requeue friction; this depends on S12 and EXP-07.`

## Avoid

- Dumping sources only in `99-research-log.md` while leaving analysis sections uncited.
- Citing IDs that are not present in the ledger.
- Marking a speculative statement as `Confirmed`.
- Mixing remake proposals into `Confirmed Facts`.

## Audit Interaction

`audit_evidence_links.py` now checks Markdown docs for evidence sections that contain content but no inline ledger citations. Empty scaffold sections are ignored, but once you start writing analysis, add the `S-id` anchors in the section text.
