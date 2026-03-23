#!/usr/bin/env python3
"""Generate a markdown experiment summary from experiment CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_FILE = "10-experiment-summary.md"
COMPACT_OUTPUT_FILE = "10-experiment-summary-compact.md"
NEXT_STATUS_ORDER = {"in-progress": 0, "not-started": 1, "completed": 2}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
LABELS = {
    "en": {
        "snapshot": "Snapshot",
        "total_experiments": "Total experiments",
        "status_counts": "Status counts",
        "priority_counts": "Priority counts",
        "raw_samples": "Raw typed samples",
        "sampled_experiments": "Experiments with raw samples",
        "high_priority_open": "High-priority unfinished",
        "recommended": "Recommended Next Experiments",
        "no_unfinished": "No unfinished experiments remain.",
        "sample_count_short": "samples={count}",
        "sample_coverage": "Raw Sample Coverage",
        "no_sample_coverage": "No typed sample rows captured yet.",
        "missing_sample_coverage": "Still missing raw samples",
        "registry": "Registry",
        "registry_headers": ("Experiment", "Detail file", "Status", "Samples", "Owner", "Notes"),
        "metrics": "Metric Rollup Snapshot",
        "pending_metrics": "Pending Metrics",
        "no_metrics": "No archetype metrics file found.",
        "populated_metrics": "Populated metrics",
        "notes": "Notes",
        "regenerate_note": "Regenerate this file after updating experiment sheets or running metric rollup.",
        "truth_note": "Treat populated metric bands as summaries of current sampled evidence, not final design truth.",
        "mode_note": "Summary mode",
        "experiment_summary": "Experiment Summary",
    },
}
DEFAULT_OUTPUTS = {
    "full": OUTPUT_FILE,
    "compact": COMPACT_OUTPUT_FILE,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a markdown experiment summary from research-pack CSV files."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Research pack directory containing data/experiment-plan.csv.",
    )
    parser.add_argument(
        "--output",
        help="Optional output markdown file name inside docs-dir. Only valid when --mode is full or compact.",
    )
    parser.add_argument(
        "--mode",
        choices=("full", "compact", "both"),
        default="full",
        help="Summary mode. `full` includes registry details; `compact` is dossier-friendly; `both` writes both default outputs.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "en"),
        default="auto",
        help="Output language for generated summaries. Defaults to auto, which currently resolves to en.",
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
                existing = row.get("notes", "")
                extra_text = " | ".join(value for value in extras if value)
                row["notes"] = f"{existing} | {extra_text}".strip(" |")
            rows.append(row)
        return rows


def detect_language(docs_dir: Path) -> str:
    return "en"


def parse_manifest_title(docs_dir: Path, language: str) -> str:
    manifest = docs_dir / "research-manifest.yaml"
    if not manifest.exists():
        suffix = LABELS[language]["experiment_summary"]
        return f"{docs_dir.name} {suffix}"
    game = ""
    archetype = ""
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("game:"):
            game = raw_line.split(":", 1)[1].strip().strip('"')
        elif raw_line.startswith("archetype:"):
            archetype = raw_line.split(":", 1)[1].strip().strip('"')
    suffix = LABELS[language]["experiment_summary"]
    if game and archetype:
        return f"{game} {suffix} ({archetype})"
    if game:
        return f"{game} {suffix}"
    return f"{docs_dir.name} {suffix}"


def normalize_status(value: str) -> str:
    return value.strip().lower()


def normalize_priority(value: str) -> str:
    return value.strip().lower()


def count_detail_rows(path: Path) -> int:
    rows = read_csv_rows(path)
    return sum(1 for row in rows if is_meaningful_detail_row(row))


def is_meaningful_detail_row(row: dict[str, str]) -> bool:
    ignorable_keys = {
        "experiment_id",
        "sample_id",
        "task_id",
        "band_id",
        "step_id",
        "state_index",
        "source_id",
        "confidence",
        "notes",
    }
    for key, value in row.items():
        if key in ignorable_keys:
            continue
        if (value or "").strip():
            return True
    return False


def build_detail_count_map(docs_dir: Path) -> dict[str, int]:
    detail_dir = docs_dir / "data" / "experiments"
    counts: dict[str, int] = {}
    if not detail_dir.exists():
        return counts
    for path in sorted(detail_dir.glob("*.csv")):
        count = count_detail_rows(path)
        counts[path.name] = count
        counts[str(path.relative_to(docs_dir)).replace("\\", "/")] = count
    return counts


def build_experiment_records(
    docs_dir: Path,
    plan_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
) -> list[dict[str, str | int]]:
    detail_counts = build_detail_count_map(docs_dir)
    registry_index = {row.get("experiment_id", "").strip(): row for row in registry_rows}
    records: list[dict[str, str | int]] = []
    for row in plan_rows:
        experiment_id = row.get("experiment_id", "").strip()
        registry_row = registry_index.get(experiment_id, {})
        detail_file = (
            registry_row.get("detail_file", "").strip() or row.get("detail_file", "").strip()
        )
        samples = detail_counts.get(detail_file, detail_counts.get(Path(detail_file).name, 0))
        status = registry_row.get("status", "").strip() or row.get("status", "").strip()
        notes = registry_row.get("notes", "").strip() or row.get("notes", "").strip()
        records.append(
            {
                "experiment_id": experiment_id,
                "experiment_name": row.get("experiment_name", "").strip(),
                "priority": row.get("priority", "").strip(),
                "status": status,
                "detail_file": detail_file,
                "samples": samples,
                "owner": registry_row.get("owner", "").strip(),
                "notes": notes,
            }
        )
    return records


def format_sample_count(count: int, language: str) -> str:
    return LABELS[language]["sample_count_short"].format(count=count)


def format_experiment_ref(record: dict[str, str | int]) -> str:
    experiment_id = str(record.get("experiment_id", "")).strip()
    experiment_name = str(record.get("experiment_name", "")).strip()
    if experiment_id and experiment_name:
        return f"`{experiment_id}` {experiment_name}"
    if experiment_id:
        return f"`{experiment_id}`"
    return experiment_name


def sort_experiment_records(
    records: list[dict[str, str | int]],
) -> list[dict[str, str | int]]:
    return sorted(
        records,
        key=lambda row: (
            PRIORITY_ORDER.get(normalize_priority(str(row.get("priority", ""))), 99),
            0 if int(row.get("samples", 0)) <= 0 else 1,
            NEXT_STATUS_ORDER.get(normalize_status(str(row.get("status", ""))), 99),
            str(row.get("experiment_id", "")),
        ),
    )


def summarize_snapshot(
    records: list[dict[str, str | int]], language: str
) -> list[str]:
    label = LABELS[language]
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    total_samples = 0
    sampled_experiments = 0
    high_priority_open = 0
    for row in records:
        status = str(row.get("status", "")).strip() or "unknown"
        priority = str(row.get("priority", "")).strip() or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        samples = int(row.get("samples", 0))
        total_samples += samples
        if samples > 0:
            sampled_experiments += 1
        if normalize_priority(priority) == "high" and normalize_status(status) != "completed":
            high_priority_open += 1

    lines = [f"## {label['snapshot']}", ""]
    lines.append(f"- {label['total_experiments']}: `{len(records)}`")
    lines.append(
        f"- {label['status_counts']}: "
        + ", ".join(f"`{key}`={status_counts[key]}" for key in sorted(status_counts))
    )
    lines.append(
        f"- {label['priority_counts']}: "
        + ", ".join(f"`{key}`={priority_counts[key]}" for key in sorted(priority_counts))
    )
    lines.append(f"- {label['raw_samples']}: `{total_samples}`")
    lines.append(f"- {label['sampled_experiments']}: `{sampled_experiments}` / `{len(records)}`")
    lines.append(f"- {label['high_priority_open']}: `{high_priority_open}`")
    return lines


def summarize_first_pass(
    records: list[dict[str, str | int]], language: str
) -> list[str]:
    label = LABELS[language]
    actionable = [
        row for row in records if normalize_status(str(row.get("status", ""))) != "completed"
    ]
    ordered = sort_experiment_records(actionable)
    lines = [f"## {label['recommended']}", ""]
    if not ordered:
        lines.append(f"- {label['no_unfinished']}")
        return lines
    for row in ordered[:5]:
        lines.append(
            f"- {format_experiment_ref(row)} `{row.get('priority','')}` `{row.get('status','')}` `{format_sample_count(int(row.get('samples', 0)), language)}`"
        )
    return lines


def summarize_registry(
    docs_dir: Path, registry_rows: list[dict[str, str]], language: str
) -> list[str]:
    label = LABELS[language]
    headers = label["registry_headers"]
    lines = [
        f"## {label['registry']}",
        "",
        f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} | {headers[5]} |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in registry_rows:
        detail_file = row.get("detail_file", "")
        samples = count_detail_rows(docs_dir / detail_file) if detail_file else 0
        lines.append(
            f"| {row.get('experiment_id','')} | {detail_file} | {row.get('status','')} | {samples} | {row.get('owner','')} | {row.get('notes','')} |"
        )
    return lines


def summarize_sample_coverage(
    records: list[dict[str, str | int]], language: str
) -> list[str]:
    label = LABELS[language]
    sampled = sorted(
        [row for row in records if int(row.get("samples", 0)) > 0],
        key=lambda row: (-int(row.get("samples", 0)), str(row.get("experiment_id", ""))),
    )
    missing = sort_experiment_records(
        [row for row in records if int(row.get("samples", 0)) <= 0]
    )

    lines = [f"## {label['sample_coverage']}", ""]
    if not sampled:
        lines.append(f"- {label['no_sample_coverage']}")
    else:
        for row in sampled[:5]:
            lines.append(
                f"- {format_experiment_ref(row)} `{format_sample_count(int(row.get('samples', 0)), language)}`"
            )
    if missing:
        lines.append(
            f"- {label['missing_sample_coverage']}: "
            + ", ".join(format_experiment_ref(row) for row in missing[:3])
            + (f", +{len(missing) - 3} more" if len(missing) > 3 else "")
        )
    return lines


def summarize_metrics(metric_rows: list[dict[str, str]], language: str) -> list[str]:
    label = LABELS[language]
    populated = [row for row in metric_rows if row.get("observed_band", "").strip()]
    pending = [row for row in metric_rows if not row.get("observed_band", "").strip()]

    lines = [f"## {label['metrics']}", ""]
    if not metric_rows:
        lines.append(f"- {label['no_metrics']}")
        return lines

    lines.append(f"- {label['populated_metrics']}: `{len(populated)}` / `{len(metric_rows)}`")
    if populated:
        lines.extend(["", "| Metric | Observed band | Confidence | Source IDs |", "| --- | --- | --- | --- |"])
        for row in populated:
            lines.append(
                f"| {row.get('metric_id','')} | {row.get('observed_band','')} | {row.get('confidence','')} | {row.get('source_ids','')} |"
            )

    if pending:
        lines.extend(["", f"### {label['pending_metrics']}", ""])
        for row in pending:
            lines.append(f"- `{row.get('metric_id','')}`: {row.get('metric_name','')}")
    return lines


def summarize_metrics_compact(metric_rows: list[dict[str, str]], language: str) -> list[str]:
    label = LABELS[language]
    populated = [row for row in metric_rows if row.get("observed_band", "").strip()]
    pending = [row for row in metric_rows if not row.get("observed_band", "").strip()]

    lines = [f"## {label['metrics']}", ""]
    if not metric_rows:
        lines.append(f"- {label['no_metrics']}")
        return lines

    lines.append(f"- {label['populated_metrics']}: `{len(populated)}` / `{len(metric_rows)}`")
    for row in populated[:5]:
        lines.append(
            f"- `{row.get('metric_id','')}` `{row.get('confidence','')}`: {row.get('observed_band','')}"
        )
    if pending:
        lines.append(
            f"- {label['pending_metrics']}: "
            + ", ".join(f"`{row.get('metric_id','')}`" for row in pending)
        )
    return lines


def build_summary(
    title: str,
    plan_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
    metric_rows: list[dict[str, str]],
    docs_dir: Path,
    mode: str,
    language: str,
) -> str:
    label = LABELS[language]
    effective_records = build_experiment_records(docs_dir, plan_rows, registry_rows)
    sections: list[str] = [f"# {title}", ""]
    sections.extend(summarize_snapshot(effective_records, language))
    sections.extend([""])
    sections.extend(summarize_first_pass(effective_records, language))
    sections.extend([""])
    sections.extend(summarize_sample_coverage(effective_records, language))
    if mode == "full":
        sections.extend([""])
        sections.extend(summarize_registry(docs_dir, registry_rows, language))
        sections.extend([""])
        sections.extend(summarize_metrics(metric_rows, language))
    else:
        sections.extend([""])
        sections.extend(summarize_metrics_compact(metric_rows, language))
    sections.extend(
        [
            "",
            f"## {label['notes']}",
            "",
            f"- {label['regenerate_note']}",
            f"- {label['truth_note']}",
            f"- {label['mode_note']}: `{mode}`.",
            "",
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def resolve_modes(mode: str) -> list[str]:
    if mode == "both":
        return ["full", "compact"]
    return [mode]


def resolve_output_path(docs_dir: Path, output: str | None, mode: str) -> Path:
    target = output or DEFAULT_OUTPUTS[mode]
    path = Path(target)
    if not path.is_absolute():
        path = docs_dir / path
    return path


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir).expanduser().resolve()
    data_dir = docs_dir / "data"
    language = detect_language(docs_dir) if args.language == "auto" else args.language

    plan_rows = read_csv_rows(data_dir / "experiment-plan.csv")
    registry_rows = read_csv_rows(data_dir / "experiment-observations.csv")
    metric_rows = read_csv_rows(data_dir / "archetype-metrics.csv")

    if not plan_rows:
        raise FileNotFoundError(
            "Missing or empty experiment plan: "
            f"{data_dir / 'experiment-plan.csv'}. "
            "Scaffold with --with-support-files or add experiment support CSVs before regenerating summaries."
        )

    title = parse_manifest_title(docs_dir, language)
    if args.mode == "both" and args.output:
        raise ValueError("--output cannot be used together with --mode both.")

    for mode in resolve_modes(args.mode):
        output = build_summary(
            title, plan_rows, registry_rows, metric_rows, docs_dir, mode, language
        )
        output_path = resolve_output_path(docs_dir, args.output, mode)
        output_path.write_text(output, encoding="utf-8")
        print(f"Wrote experiment summary to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
