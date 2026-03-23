# Metric Rollup

Use this reference when typed experiment data should flow back into `data/archetype-metrics.csv`.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Files

- `data/archetype-metrics.csv`
  The baseline metric table used in the final remake pack.
- `data/archetype-metric-links.csv`
  A per-metric mapping file that declares which experiment detail sheet should feed which metric.
- `data/experiments/*.csv`
  Typed raw-observation sheets.

## Supported Rollups

- `numeric_band`
  Summarizes one or more numeric columns as `min`, `avg`, `max`, and `n`.
- `ratio_band`
  Summarizes a numerator and denominator pair as `min`, `avg`, `max`, and `n` for the ratio.
- `manual`
  Leaves the metric untouched. Use when interpretation still requires human judgment.

## Workflow

1. Fill the typed experiment sheets under `data/experiments/`.
2. Adjust `data/archetype-metric-links.csv` if the default link or aggregation is wrong.
3. Run:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/rollup_experiment_metrics.py" \
  --docs-dir ./docs/remake-maplestory
```

4. Review the updated `data/archetype-metrics.csv`.
5. Keep any metric on `manual` when the data still needs interpretation.

## Expectations

- The helper only automates obvious numeric summaries.
- It should not pretend to infer design meaning where the data is ambiguous.
- `manual` rows are expected, especially for metrics that depend on contextual interpretation.
