#!/usr/bin/env python3
"""Roll typed experiment data back into archetype metric baselines."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Roll typed experiment CSV observations into data/archetype-metrics.csv."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Research pack directory containing data/archetype-metrics.csv.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files.",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            extras = row.pop(None, None)
            if extras:
                existing_notes = row.get("notes", "")
                extra_text = " | ".join(value for value in extras if value)
                row["notes"] = f"{existing_notes} | {extra_text}".strip(" |")
            rows.append(row)
        return rows


def write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def try_float(value: str) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def unique_source_ids(rows: list[dict[str, str]]) -> str:
    values = sorted({row.get("source_id", "").strip() for row in rows if row.get("source_id", "").strip()})
    return ";".join(values)


def summarize_numeric_band(rows: list[dict[str, str]], columns: list[str]) -> str:
    parts: list[str] = []
    for column in columns:
        values = [value for row in rows if (value := try_float(row.get(column, ""))) is not None]
        if not values:
            continue
        minimum = min(values)
        average = sum(values) / len(values)
        maximum = max(values)
        parts.append(
            f"{column}[min={minimum:.2f} avg={average:.2f} max={maximum:.2f} n={len(values)}]"
        )
    return "; ".join(parts)


def summarize_ratio_band(rows: list[dict[str, str]], numerator: str, denominator: str) -> str:
    ratios: list[float] = []
    for row in rows:
        left = try_float(row.get(numerator, ""))
        right = try_float(row.get(denominator, ""))
        if left is None or right is None or right == 0:
            continue
        ratios.append(left / right)

    if not ratios:
        return ""

    minimum = min(ratios)
    average = sum(ratios) / len(ratios)
    maximum = max(ratios)
    return (
        f"{numerator}/{denominator}[min={minimum:.4f} avg={average:.4f} max={maximum:.4f} n={len(ratios)}]"
    )


def summarize_link(
    docs_dir: Path, link_row: dict[str, str]
) -> tuple[str, str, str]:
    detail_file = link_row.get("detail_file", "").strip()
    aggregation = link_row.get("aggregation", "").strip()
    value_columns = [value.strip() for value in link_row.get("value_columns", "").split(";") if value.strip()]

    if not detail_file or aggregation == "manual":
        return "", "", "manual"

    rows = read_csv_rows(docs_dir / detail_file)
    if not rows:
        return "", "", f"missing-or-empty:{detail_file}"

    if aggregation == "numeric_band":
        observed_band = summarize_numeric_band(rows, value_columns)
    elif aggregation == "ratio_band" and len(value_columns) == 2:
        observed_band = summarize_ratio_band(rows, value_columns[0], value_columns[1])
    else:
        observed_band = ""

    if not observed_band:
        return "", unique_source_ids(rows), f"no-usable-values:{detail_file}"

    return observed_band, unique_source_ids(rows), f"rollup:{aggregation}:{detail_file}"


def combine_notes(existing: str, new_note: str) -> str:
    existing = existing.strip()
    if not existing:
        return new_note
    if new_note in existing:
        return existing
    return f"{existing} | {new_note}"


def run_rollup(
    docs_dir: Path, dry_run: bool = False
) -> tuple[int, int, Path, list[dict[str, str]]]:
    data_dir = docs_dir / "data"
    metrics_path = data_dir / "archetype-metrics.csv"
    links_path = data_dir / "archetype-metric-links.csv"

    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics file: {metrics_path}")
    if not links_path.exists():
        raise FileNotFoundError(f"Missing metric links file: {links_path}")

    metric_rows = read_csv_rows(metrics_path)
    link_rows = read_csv_rows(links_path)
    metric_index = {row["metric_id"]: row for row in metric_rows}

    updated = 0
    skipped = 0

    for link_row in link_rows:
        metric_id = link_row.get("metric_id", "").strip()
        metric_row = metric_index.get(metric_id)
        if not metric_row:
            skipped += 1
            continue

        observed_band, source_ids, note = summarize_link(docs_dir, link_row)
        if not observed_band:
            if note and note != "manual":
                metric_row["notes"] = combine_notes(metric_row.get("notes", ""), note)
            skipped += 1
            continue

        metric_row["observed_band"] = observed_band
        metric_row["source_ids"] = source_ids
        if metric_row.get("confidence", "").strip() in ("", "Open"):
            metric_row["confidence"] = "Inferred"
        metric_row["notes"] = combine_notes(metric_row.get("notes", ""), note)
        updated += 1

    if dry_run:
        return updated, skipped, metrics_path, metric_rows

    fieldnames = list(metric_rows[0].keys()) if metric_rows else []
    write_csv_rows(metrics_path, metric_rows, fieldnames)
    return updated, skipped, metrics_path, metric_rows


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir).expanduser().resolve()
    updated, skipped, metrics_path, metric_rows = run_rollup(
        docs_dir, dry_run=args.dry_run
    )

    if args.dry_run:
        print(f"Would update {updated} metrics and skip {skipped}.")
        for row in metric_rows:
            print(
                f"- {row['metric_id']}: observed_band={row.get('observed_band', '')} source_ids={row.get('source_ids', '')}"
            )
        return 0

    print(f"Updated {updated} metrics and skipped {skipped} in {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
