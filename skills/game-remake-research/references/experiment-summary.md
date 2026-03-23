# Experiment Summary

Use this reference when raw experiment CSV data needs to be turned into a compact markdown brief for the remake pack.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Purpose

`10-experiment-summary.md` should answer:

- Which experiments are in progress?
- Which high-priority experiments are still missing?
- Which typed sheets already contain usable samples?
- Which archetype metrics have already been populated by rollup?

`10-experiment-summary-compact.md` is the dossier-friendly variant. It should answer the same questions with less registry detail.
The generated summary now also includes:

- total raw typed sample count across all experiment sheets
- how many experiments already have at least one usable raw sample
- a priority-ranked next-pass list with experiment IDs, statuses, and current sample counts
- a raw-sample coverage section that highlights both sampled sheets and still-empty high-priority sheets

## Workflow

1. Update `data/experiment-plan.csv`.
2. Update `data/experiment-observations.csv`.
3. Fill the relevant `data/experiments/*.csv` typed sheets.
4. Optionally run metric rollup if archetype metrics should be refreshed.
5. Run:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/summarize_experiments.py" \
  --docs-dir ./docs/remake-maplestory \
  --mode full
```

Use `--language en` when you want to pin the output explicitly. `--language auto` currently resolves to `en`.
If the pack also uses `data/archetype-metric-links.csv`, stale-summary repair commands now pair summary regeneration with `rollup_experiment_metrics.py` first so metric snapshots stay aligned.

When the final merge should stay concise, also run:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/summarize_experiments.py" \
  --docs-dir ./docs/remake-maplestory \
  --mode compact \
  --output 10-experiment-summary-compact.md
```

When both default variants need a refresh, use:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/summarize_experiments.py" \
  --docs-dir ./docs/remake-maplestory \
  --mode both \
  --language en
```

`merge_remake_docs.py --docs-dir ./docs/remake-maplestory --mode compact` will prefer `10-experiment-summary-compact.md` when it exists.

## Expectations

- This file is a status and evidence summary, not a replacement for raw sheets.
- Regenerate it whenever experiment status or rollup results change.
- Keep it concise enough that it can be merged into the final dossier without becoming a data dump.
- The compact variant should omit noisy registry detail rather than invent a second interpretation layer.
- If a compact summary still hides where evidence is missing, the next-pass and raw-sample coverage sections should be tightened before handoff.
