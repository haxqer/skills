#!/usr/bin/env python3
"""Build a markdown status report for a remake research pack."""

from __future__ import annotations

import argparse
import shlex
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from audit_evidence_links import (
    EvidenceAuditResult,
    evidence_issue_counts,
    highest_evidence_priority,
    run_evidence_audit,
)
from audit_remake_pack import (
    CORE_DOC_REQUIREMENTS,
    STATUS_INCOMPLETE,
    Issue,
    collect_h2_headings,
    count_blank_placeholders,
    count_meaningful_rows,
    detect_support_features,
    detect_language,
    handoff_dossier_includes_log,
    is_meaningful,
    is_meaningful_detail_row,
    parse_manifest,
    render_issue,
    read_csv_rows,
    read_text,
    run_audit,
)


SKILL_ROOT = Path(__file__).resolve().parent.parent


LANG = {
    "en": {
        "title": "{game} Pack Status Report",
        "snapshot": "Snapshot",
        "audit_result": "Audit result",
        "error_count": "Errors",
        "warning_count": "Warnings",
        "baseline": "Baseline version",
        "archetype": "Archetype lens",
        "support": "Support files",
        "experiments": "Experiment support",
        "evidence": "Evidence traceability",
        "evidence_status": "Evidence audit",
        "evidence_priority": "Highest evidence priority",
        "unknown_sources": "Unknown source IDs",
        "duplicate_sources": "Duplicate source IDs",
        "blank_source_refs": "Rows missing source refs",
        "unused_sources": "Unused ledger IDs",
        "doc_citation_gaps": "Docs missing inline citations",
        "stale_experiment_summaries": "Stale experiment summaries",
        "stale_evidence_audits": "Stale evidence audits",
        "stale_status_reports": "Stale status reports",
        "stale_handoff_dossiers": "Stale handoff dossiers",
        "stale_handoff_manifests": "Stale handoff manifests",
        "duplicate_source_rows": "Duplicate source IDs",
        "unknown_source_refs": "Unknown source references",
        "blank_ref_rows": "Blank source reference rows",
        "unused_source_rows": "Unused ledger source rows",
        "doc_citation_rows": "Docs missing inline citations",
        "documents": "Core Document Snapshot",
        "placeholder_hotspots": "Placeholder Hotspots",
        "folded_docs": "... {count} more docs folded in compact view.",
        "file": "File",
        "status": "Status",
        "missing_sections": "Missing sections",
        "blank_placeholders": "Blank placeholders",
        "support_data": "Support Data Snapshot",
        "sources_with_evidence": "Sources with evidence",
        "formulas_captured": "Formulas captured",
        "assets_detailed": "Asset rows with production detail",
        "risks_populated": "Risks populated",
        "role_coverage": "Role Coverage",
        "roles_summary": "Roles by status",
        "role": "Role",
        "key_findings": "Key findings",
        "missing_evidence": "Missing evidence",
        "archetype_snapshot": "Archetype Snapshot",
        "checklist_progress": "Checklist progress",
        "metric_progress": "Observed metrics",
        "experiments_snapshot": "Experiment Snapshot",
        "plan_status": "Plan statuses",
        "registry_status": "Registry statuses",
        "raw_samples": "Raw captured samples",
        "detail_file": "Detail file",
        "samples": "Samples",
        "findings": "Audit Findings",
        "errors": "Errors",
        "warnings": "Warnings",
        "no_errors": "No errors.",
        "no_warnings": "No warnings.",
        "none": "None.",
        "source_id": "Source ID",
        "references": "References",
        "location": "Location",
        "row": "Row",
        "field": "Field",
        "count": "Count",
        "source_type": "Source type",
        "title_col": "Title",
        "document": "Document",
        "sections": "Sections",
        "more_locations": "+{count} more",
        "priority": "Priority",
        "priority_blocker": "blocker",
        "priority_high": "high",
        "priority_medium": "medium",
        "priority_low": "low",
        "priority_none": "none",
        "group_scope": "Scope And Structure",
        "group_placeholders": "Template Placeholders",
        "group_support_data": "Support Data",
        "group_generated_artifacts": "Generated Artifacts",
        "group_progress": "Progress Signals",
        "group_other": "Other",
        "omitted_group_items": "... {count} more in this group.",
        "folded_docs": "... {count} more docs folded in compact view.",
        "names_more": "+{count} more",
        "support_missing_sources": "Source ledger still lacks dated evidence rows.",
        "support_missing_formulas": "Formula catalog still has no captured formulas.",
        "support_missing_assets": "Asset taxonomy still has no production-detail rows.",
        "support_missing_risks": "Risk register still has no populated risks.",
        "support_ok": "Tracked support tables all have at least one populated row.",
        "roles_blocked": "Roles still not-started: `{count}` ({roles})",
        "roles_active": "Role coverage summary: {summary}",
        "roles_ok": "Role coverage has no blocked entries.",
        "archetype_checklist_gap": "Checklist items still not progressed: `{remaining}` / `{total}`",
        "archetype_metric_gap": "Observed metric bands still missing: `{remaining}` / `{total}`",
        "archetype_ok": "Archetype checklist and metric baselines both show progress.",
        "experiments_raw_gap": "Experiments still missing raw samples: `{count}` ({experiments})",
        "experiments_plan_gap": "Experiment plan still not-started: `{count}` ({experiments})",
        "experiments_registry_gap": "Experiment registry still not-started: `{count}` ({experiments})",
        "experiments_ok": "Experiment tracking shows active progress.",
        "next_actions": "Recommended Next Actions",
        "no_actions": "No immediate actions.",
        "status_ok": "ok",
        "status_review": "review",
        "status_missing": "missing",
        "action_restore_docs": "Restore the missing core docs: {value}",
        "action_replace_placeholders": "Replace scaffold placeholders in {value}.",
        "action_lock_baseline": "Lock the baseline version, region, platform, and time slice.",
        "action_populate_sources": "Populate `data/source-ledger.csv` with dated official and gameplay sources.",
        "action_advance_roles": "Advance `data/role-coverage.csv` so each role reflects actual progress and missing evidence.",
        "action_progress_checklist": "Progress at least the highest-priority archetype checklist items.",
        "action_populate_metrics": "Populate observed metric bands or run metric rollup after sampling.",
        "action_mark_plan": "Mark experiment plan status realistically instead of leaving the whole plan at `not-started`.",
        "action_mark_plan_specific": "Update experiment-plan statuses for {value} so the plan reflects real progress.",
        "action_update_registry": "Update `data/experiment-observations.csv` so the registry reflects actual capture progress.",
        "action_update_registry_specific": "Update `data/experiment-observations.csv` for {value} so the registry matches the actual capture state.",
        "action_capture_samples": "Capture at least one typed experiment sheet so the pack has raw evidence, not only intentions.",
        "action_capture_samples_specific": "Capture typed raw samples first for {value}.",
        "action_fix_unknown_sources": "Reconcile duplicate or unknown `S-id` references so every cited source resolves cleanly in `data/source-ledger.csv`.",
        "action_fix_blank_source_refs": "Fill missing `source_id` / `source_ids` on populated support rows.",
        "action_fix_doc_citations": "Add inline `S-id` anchors inside populated `Confirmed Facts` / `Inferred Model` sections.",
        "action_review_unused_sources": "Review unused ledger IDs and prune or cite the stale source entries.",
        "action_refresh_generated_bundle": "Run {command} to refresh stale derived artifacts in one pass: {targets}.",
        "action_refresh_experiment_summary": "Run {command} to regenerate stale experiment summaries: {value}.",
        "action_refresh_evidence_audit": "Run {command} to refresh stale evidence-audit outputs: {value}.",
        "action_refresh_status_report": "Run {command} to refresh stale status reports: {value}.",
        "action_refresh_handoff_dossier": "Run {command} to refresh stale handoff dossiers: {value}.",
        "action_refresh_handoff_bundle": "Run {command} to refresh stale handoff manifests: {value}.",
        "yes": "yes",
        "no": "no",
        "not_available": "not available",
    },
}

DEFAULT_OUTPUTS = {
    "full": "reports/pack-status.md",
    "compact": "reports/pack-status-compact.md",
}

ACTION_PRIORITY_RANK = {
    "blocker": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

GENERATED_ARTIFACT_ISSUE_CODES = {
    "stale_experiment_summary": "stale_experiment_summaries",
    "stale_evidence_link_audit": "stale_evidence_audits",
    "stale_status_report": "stale_status_reports",
    "stale_handoff_dossier": "stale_handoff_dossiers",
    "stale_handoff_bundle": "stale_handoff_manifests",
}

ISSUE_GROUP_ORDER = (
    "scope",
    "placeholders",
    "support_data",
    "generated_artifacts",
    "progress",
    "other",
)
ISSUE_GROUP_BY_CODE = {
    "missing_required_document": "scope",
    "missing_section_heading": "scope",
    "missing_manifest_baseline_version": "scope",
    "default_baseline_placeholder": "scope",
    "missing_manifest_file": "scope",
    "missing_support_file": "scope",
    "missing_archetype_doc": "scope",
    "missing_archetype_support_file": "scope",
    "missing_experiment_support_path": "scope",
    "missing_experiment_summary": "scope",
    "blank_scaffold_placeholders": "placeholders",
    "empty_source_ledger": "support_data",
    "empty_formula_catalog": "support_data",
    "empty_risk_register": "support_data",
    "empty_role_coverage": "support_data",
    "missing_role_coverage_roles": "support_data",
    "stale_experiment_summary": "generated_artifacts",
    "stale_evidence_link_audit": "generated_artifacts",
    "stale_status_report": "generated_artifacts",
    "stale_handoff_dossier": "generated_artifacts",
    "stale_handoff_bundle": "generated_artifacts",
    "incomplete_role_coverage": "progress",
    "no_archetype_checklist_progress": "progress",
    "no_archetype_metric_bands": "progress",
    "no_experiment_plan_progress": "progress",
    "no_experiment_registry_progress": "progress",
    "empty_experiment_detail_sheets": "progress",
    "no_experiment_raw_samples": "progress",
}

PLACEHOLDER_PRIORITY_BY_FILE = {
    "00-overview-and-source-ledger.md": "high",
    "01-product-and-player-experience.md": "medium",
    "02-systems-and-gameplay.md": "medium",
    "03-economy-and-balance.md": "medium",
    "04-content-art-audio-narrative.md": "medium",
    "05-client-architecture-and-production.md": "medium",
    "06-replica-backlog-and-acceptance.md": "low",
    "99-research-log.md": "low",
}

DOC_FOCUS_LIMIT = 4
ROLE_NAME_LIMIT = 3
ROLE_TERMINAL_STATUSES = {"complete", "completed", "done", "verified"}
EXPERIMENT_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
EXPERIMENT_STATUS_ORDER = {"in-progress": 0, "not-started": 1, "not started": 1, "completed": 2}
ACTION_OUTPUT_LIMIT = 10


@dataclass
class ActionItem:
    priority: str
    text: str
    order: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a markdown status report for a remake research pack."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Research pack directory to summarize.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path. Relative paths are resolved inside docs-dir. Only valid when --mode is full or compact.",
    )
    parser.add_argument(
        "--mode",
        choices=("full", "compact", "both"),
        default="full",
        help="Report mode. `compact` keeps only the headline tables and blockers; `both` writes both default outputs.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "en"),
        default="auto",
        help="Report language. Defaults to auto, which currently resolves to en.",
    )
    return parser.parse_args()
def format_status_counts(rows: list[dict[str, str]], field: str = "status") -> str:
    if not rows:
        return "`none`=0"
    counts = Counter((row.get(field, "").strip() or "unknown") for row in rows)
    return ", ".join(f"`{key}`={counts[key]}" for key in sorted(counts))


def normalize_status(value: str) -> str:
    return value.strip().lower()


def normalize_priority(value: str) -> str:
    return value.strip().lower()


def classify_doc_status(exists: bool, missing_count: int, blank_count: int, label: dict[str, str]) -> str:
    if not exists or missing_count:
        return label["status_missing"]
    if blank_count:
        return label["status_review"]
    return label["status_ok"]


def build_doc_rows(docs_dir: Path, label: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for filename, expected_groups in CORE_DOC_REQUIREMENTS.items():
        path = docs_dir / filename
        exists = path.exists()
        missing: list[str] = []
        blank_count = 0
        if exists:
            headings = collect_h2_headings(read_text(path))
            for group in expected_groups:
                if not any(candidate in headings for candidate in group):
                    missing.append(" / ".join(group))
            blank_count, _samples = count_blank_placeholders(read_text(path))
        rows.append(
            {
                "file": filename,
                "exists": exists,
                "missing": missing,
                "blank_count": blank_count,
                "status": classify_doc_status(exists, len(missing), blank_count, label),
            }
        )
    return rows


def placeholder_priority_for_file(filename: str) -> str:
    return PLACEHOLDER_PRIORITY_BY_FILE.get(filename, "low")


def summarize_placeholder_hotspots(
    doc_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    hotspots = [
        {
            "file": row["file"],
            "blank_count": int(row["blank_count"]),
            "priority": placeholder_priority_for_file(str(row["file"])),
        }
        for row in doc_rows
        if row["exists"] and int(row["blank_count"])
    ]
    hotspots.sort(
        key=lambda row: (
            ACTION_PRIORITY_RANK[row["priority"]],
            -int(row["blank_count"]),
            str(row["file"]),
        )
    )
    return hotspots


def doc_focus_priority(row: dict[str, object]) -> str:
    if not row["exists"] or row["missing"]:
        return "blocker"
    return placeholder_priority_for_file(str(row["file"]))


def summarize_compact_doc_rows(
    doc_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], int]:
    ranked = sorted(
        doc_rows,
        key=lambda row: (
            ACTION_PRIORITY_RANK[doc_focus_priority(row)],
            -int(row["blank_count"]),
            str(row["file"]),
        ),
    )
    selected = ranked[:DOC_FOCUS_LIMIT]
    omitted = max(0, len(ranked) - len(selected))
    return selected, omitted


def summarize_support_data(docs_dir: Path) -> dict[str, int]:
    data_dir = docs_dir / "data"
    ledger_rows = read_csv_rows(data_dir / "source-ledger.csv")
    formula_rows = read_csv_rows(data_dir / "formula-catalog.csv")
    asset_rows = read_csv_rows(data_dir / "asset-taxonomy.csv")
    risk_rows = read_csv_rows(data_dir / "risk-register.csv")
    return {
        "sources": count_meaningful_rows(
            ledger_rows, ["title", "url_or_location", "version_or_date", "notes"]
        ),
        "formulas": count_meaningful_rows(
            formula_rows, ["name", "expression", "variables", "version_scope", "source_ids"]
        ),
        "assets": count_meaningful_rows(
            asset_rows, ["subtype", "reusable_or_bespoke", "priority", "source_ids", "notes"]
        ),
        "risks": count_meaningful_rows(
            risk_rows, ["description", "impact", "likelihood", "mitigation", "validation"]
        ),
    }


def summarize_role_coverage(docs_dir: Path) -> tuple[list[dict[str, str]], str]:
    rows = read_csv_rows(docs_dir / "data" / "role-coverage.csv")
    return rows, format_status_counts(rows)


def summarize_archetype(docs_dir: Path) -> dict[str, int]:
    data_dir = docs_dir / "data"
    checklist_rows = read_csv_rows(data_dir / "archetype-checklist.csv")
    metric_rows = read_csv_rows(data_dir / "archetype-metrics.csv")
    progressed = sum(
        1 for row in checklist_rows if row.get("status", "").strip().lower() not in STATUS_INCOMPLETE
    )
    populated_metrics = sum(
        1 for row in metric_rows if is_meaningful(row.get("observed_band", ""))
    )
    return {
        "checklist_total": len(checklist_rows),
        "checklist_progressed": progressed,
        "metric_total": len(metric_rows),
        "metric_populated": populated_metrics,
    }


def summarize_experiments(docs_dir: Path) -> dict[str, object]:
    data_dir = docs_dir / "data"
    experiment_dir = data_dir / "experiments"
    plan_rows = read_csv_rows(data_dir / "experiment-plan.csv")
    registry_rows = read_csv_rows(data_dir / "experiment-observations.csv")
    detail_counts: list[tuple[str, int]] = []
    detail_count_map: dict[str, int] = {}
    raw_samples = 0
    for path in sorted(experiment_dir.glob("*.csv")):
        rows = read_csv_rows(path)
        count = sum(1 for row in rows if is_meaningful_detail_row(row))
        detail_counts.append((path.name, count))
        detail_count_map[path.name] = count
        detail_count_map[str(path.relative_to(docs_dir)).replace("\\", "/")] = count
        raw_samples += count
    registry_index = {row.get("experiment_id", "").strip(): row for row in registry_rows}
    records: list[dict[str, object]] = []
    for row in plan_rows:
        experiment_id = row.get("experiment_id", "").strip()
        registry_row = registry_index.get(experiment_id, {})
        detail_file = (
            registry_row.get("detail_file", "").strip()
            or row.get("detail_file", "").strip()
        )
        samples = detail_count_map.get(
            detail_file,
            detail_count_map.get(Path(detail_file).name, 0),
        )
        records.append(
            {
                "experiment_id": experiment_id,
                "experiment_name": row.get("experiment_name", "").strip(),
                "priority": row.get("priority", "").strip(),
                "status": registry_row.get("status", "").strip()
                or row.get("status", "").strip(),
                "detail_file": detail_file,
                "samples": samples,
            }
        )
    return {
        "plan_rows": plan_rows,
        "registry_rows": registry_rows,
        "plan_summary": format_status_counts(plan_rows),
        "registry_summary": format_status_counts(registry_rows),
        "raw_samples": raw_samples,
        "detail_counts": detail_counts,
        "records": records,
    }


def summarize_evidence(
    docs_dir: Path, language: str, evidence_result: EvidenceAuditResult | None = None
) -> EvidenceAuditResult | None:
    ledger_path = docs_dir / "data" / "source-ledger.csv"
    if not ledger_path.exists():
        return None
    return evidence_result or run_evidence_audit(docs_dir, language)


def summarize_locations(
    locations: list[str], label: dict[str, str], limit: int = 3
) -> str:
    if len(locations) <= limit:
        return "; ".join(locations)
    shown = "; ".join(locations[:limit])
    remainder = len(locations) - limit
    return f"{shown}; {label['more_locations'].format(count=remainder)}"


def render_priority(priority: str, label: dict[str, str]) -> str:
    return label.get(f"priority_{priority}", priority)


def summarize_names(names: list[str], label: dict[str, str], limit: int = ROLE_NAME_LIMIT) -> str:
    formatted = [f"`{name}`" for name in names if name]
    if len(formatted) <= limit:
        return ", ".join(formatted)
    shown = ", ".join(formatted[:limit])
    remainder = len(formatted) - limit
    return f"{shown}, {label['names_more'].format(count=remainder)}"


def format_experiment_target(row: dict[str, object]) -> str:
    experiment_id = str(row.get("experiment_id", "")).strip()
    experiment_name = str(row.get("experiment_name", "")).strip()
    if experiment_id and experiment_name:
        return f"`{experiment_id}` {experiment_name}"
    if experiment_id:
        return f"`{experiment_id}`"
    return experiment_name


def sort_experiment_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            EXPERIMENT_PRIORITY_ORDER.get(
                normalize_priority(str(row.get("priority", ""))),
                99,
            ),
            0 if int(row.get("samples", 0) or 0) <= 0 else 1,
            EXPERIMENT_STATUS_ORDER.get(
                normalize_status(str(row.get("status", ""))),
                99,
            ),
            str(row.get("experiment_id", "")),
        ),
    )


def summarize_experiment_targets(
    rows: list[dict[str, object]],
    label: dict[str, str],
    limit: int = 3,
) -> str:
    ordered = sort_experiment_rows(rows)
    formatted = [target for target in (format_experiment_target(row) for row in ordered) if target]
    if not formatted:
        return label["none"]
    if len(formatted) <= limit:
        return ", ".join(formatted)
    shown = ", ".join(formatted[:limit])
    remainder = len(formatted) - limit
    return f"{shown}, {label['names_more'].format(count=remainder)}"


def summarize_display_values(
    values: list[str],
    label: dict[str, str],
    limit: int = 3,
) -> str:
    formatted = [f"`{value}`" for value in values if value]
    if not formatted:
        return label["none"]
    if len(formatted) <= limit:
        return ", ".join(formatted)
    shown = ", ".join(formatted[:limit])
    remainder = len(formatted) - limit
    return f"{shown}, {label['names_more'].format(count=remainder)}"


def shell_command(script_name: str, arguments: list[str]) -> str:
    script_path = f'"${{GAME_REMAKE_RESEARCH:-{SKILL_ROOT}}}/scripts/{script_name}"'
    args = shlex.join(arguments)
    suffix = f" {args}" if args else ""
    return f"`python3 {script_path}{suffix}`"


def language_args(language: str) -> list[str]:
    return ["--language", language] if language == "en" else []


def include_log_args(include_log: bool) -> list[str]:
    return ["--include-log"] if include_log else []


def rollup_metrics_args(enabled: bool) -> list[str]:
    return ["--rollup-metrics"] if enabled else []


def has_metric_rollup_support(docs_dir: Path | None) -> bool:
    if docs_dir is None:
        return False
    data_dir = docs_dir / "data"
    return (data_dir / "archetype-metrics.csv").exists() and (
        data_dir / "archetype-metric-links.csv"
    ).exists()


def format_command_sequence(commands: list[str]) -> str:
    rendered = [command for command in commands if command]
    if not rendered:
        return ""
    if len(rendered) == 1:
        return rendered[0]
    return f"{rendered[0]} then {rendered[1]}"


def stale_issue_paths(issues: list[Issue], code: str) -> list[str]:
    return [
        path
        for issue in issues
        if issue.code == code
        for path in [issue.data.get("path", "")]
        if path
    ]


def infer_generated_mode(paths: list[str], full_path: str, compact_path: str) -> str:
    has_full = full_path in paths
    has_compact = compact_path in paths
    if has_full and has_compact:
        return "both"
    if has_full:
        return "full"
    if has_compact:
        return "compact"
    return "none"


def infer_handoff_include_log(paths: list[str], docs_dir: Path | None) -> bool:
    if docs_dir is None:
        return False
    observed: list[bool] = []
    for relative in paths:
        artifact = docs_dir / relative
        if not artifact.exists():
            continue
        observed.append(handoff_dossier_includes_log(artifact, docs_dir))
    if not observed:
        return False
    return all(observed)


def build_experiment_summary_command(
    paths: list[str], language: str, docs_dir: Path | None
) -> str | None:
    mode = infer_generated_mode(paths, "10-experiment-summary.md", "10-experiment-summary-compact.md")
    if mode == "none":
        return None
    commands: list[str] = []
    if has_metric_rollup_support(docs_dir):
        commands.append(
            shell_command("rollup_experiment_metrics.py", ["--docs-dir", "."])
        )
    commands.append(
        shell_command(
            "summarize_experiments.py",
            ["--docs-dir", ".", "--mode", mode, *language_args(language)],
        )
    )
    return format_command_sequence(commands)


def build_evidence_audit_command(paths: list[str], language: str) -> str | None:
    if not paths:
        return None
    return shell_command(
        "audit_evidence_links.py",
        ["--docs-dir", ".", "--output", "reports/evidence-link-audit.md", *language_args(language)],
    )


def build_status_report_command(paths: list[str], language: str) -> str | None:
    mode = infer_generated_mode(paths, "reports/pack-status.md", "reports/pack-status-compact.md")
    if mode == "none":
        return None
    return shell_command(
        "build_pack_status_report.py",
        ["--docs-dir", ".", "--mode", mode, *language_args(language)],
    )


def build_handoff_dossier_command(
    paths: list[str], language: str, docs_dir: Path | None
) -> str | None:
    mode = infer_generated_mode(paths, "handoff-full-dossier.md", "handoff-compact-dossier.md")
    if mode == "none":
        return None
    include_log = infer_handoff_include_log(paths, docs_dir)
    return shell_command(
        "build_handoff_bundle.py",
        [
            "--docs-dir",
            ".",
            "--dossier-mode",
            mode,
            "--report-mode",
            "none",
            *include_log_args(include_log),
            *language_args(language),
        ],
    )


def build_handoff_manifest_command(paths: list[str], language: str) -> str | None:
    if not paths:
        return None
    return shell_command(
        "build_handoff_bundle.py",
        [
            "--docs-dir",
            ".",
            "--dossier-mode",
            "none",
            "--report-mode",
            "none",
            *language_args(language),
        ],
    )


def build_generated_bundle_action(
    issues: list[Issue],
    label: dict[str, str],
    language: str,
    docs_dir: Path | None,
) -> tuple[str, str] | None:
    stale_paths = {
        "stale_experiment_summary": stale_issue_paths(issues, "stale_experiment_summary"),
        "stale_evidence_link_audit": stale_issue_paths(issues, "stale_evidence_link_audit"),
        "stale_status_report": stale_issue_paths(issues, "stale_status_report"),
        "stale_handoff_dossier": stale_issue_paths(issues, "stale_handoff_dossier"),
        "stale_handoff_bundle": stale_issue_paths(issues, "stale_handoff_bundle"),
    }
    active = {code: paths for code, paths in stale_paths.items() if paths}
    if len(active) < 2:
        return None

    dossier_mode = infer_generated_mode(
        stale_paths["stale_handoff_dossier"],
        "handoff-full-dossier.md",
        "handoff-compact-dossier.md",
    )
    include_log = infer_handoff_include_log(
        stale_paths["stale_handoff_dossier"],
        docs_dir,
    )
    run_rollup = bool(stale_paths["stale_experiment_summary"]) and has_metric_rollup_support(
        docs_dir
    )
    report_mode = infer_generated_mode(
        stale_paths["stale_status_report"],
        "reports/pack-status.md",
        "reports/pack-status-compact.md",
    )
    command = shell_command(
        "build_handoff_bundle.py",
        [
            "--docs-dir",
            ".",
            "--dossier-mode",
            dossier_mode,
            "--report-mode",
            report_mode,
            *rollup_metrics_args(run_rollup),
            *include_log_args(include_log),
            *language_args(language),
        ],
    )
    targets = summarize_display_values(
        [path for paths in active.values() for path in paths],
        label,
    )
    return (
        "medium",
        label["action_refresh_generated_bundle"].format(
            command=command,
            targets=targets,
        ),
    )


def build_compact_support_lines(
    support: dict[str, int],
    label: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    if support["sources"] <= 0:
        lines.append(label["support_missing_sources"])
    if support["formulas"] <= 0:
        lines.append(label["support_missing_formulas"])
    if support["assets"] <= 0:
        lines.append(label["support_missing_assets"])
    if support["risks"] <= 0:
        lines.append(label["support_missing_risks"])
    return lines or [label["support_ok"]]


def build_compact_role_lines(
    role_rows: list[dict[str, str]],
    role_summary: str,
    label: dict[str, str],
) -> list[str]:
    blocked_roles = sorted(
        row.get("role", "").strip()
        for row in role_rows
        if normalize_status(row.get("status", "")) in STATUS_INCOMPLETE
    )
    blocked_roles = [role for role in blocked_roles if role]
    if blocked_roles:
        return [
            label["roles_blocked"].format(
                count=len(blocked_roles),
                roles=summarize_names(blocked_roles, label),
            )
        ]

    normalized_statuses = {
        normalize_status(row.get("status", ""))
        for row in role_rows
        if normalize_status(row.get("status", ""))
    }
    if normalized_statuses and normalized_statuses.issubset(ROLE_TERMINAL_STATUSES):
        return [label["roles_ok"]]
    return [label["roles_active"].format(summary=role_summary)]


def build_compact_archetype_lines(
    archetype_summary: dict[str, int],
    label: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    checklist_remaining = (
        archetype_summary["checklist_total"] - archetype_summary["checklist_progressed"]
    )
    metric_remaining = (
        archetype_summary["metric_total"] - archetype_summary["metric_populated"]
    )
    if checklist_remaining > 0 or archetype_summary["checklist_total"] == 0:
        lines.append(
            label["archetype_checklist_gap"].format(
                remaining=checklist_remaining,
                total=archetype_summary["checklist_total"],
            )
        )
    if metric_remaining > 0 or archetype_summary["metric_total"] == 0:
        lines.append(
            label["archetype_metric_gap"].format(
                remaining=metric_remaining,
                total=archetype_summary["metric_total"],
            )
        )
    return lines or [label["archetype_ok"]]


def count_incomplete_rows(rows: list[dict[str, str]], field: str = "status") -> int:
    return sum(1 for row in rows if normalize_status(row.get(field, "")) in STATUS_INCOMPLETE)


def build_compact_experiment_lines(
    experiment_summary: dict[str, object],
    label: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    records = experiment_summary.get("records")
    plan_rows = experiment_summary.get("plan_rows")
    registry_rows = experiment_summary.get("registry_rows")
    record_list = records if isinstance(records, list) else []
    plan_list = plan_rows if isinstance(plan_rows, list) else []
    registry_list = registry_rows if isinstance(registry_rows, list) else []

    sample_gaps = [
        row
        for row in record_list
        if normalize_status(str(row.get("status", ""))) != "completed"
        and int(row.get("samples", 0) or 0) <= 0
    ]
    if sample_gaps:
        lines.append(
            label["experiments_raw_gap"].format(
                count=len(sample_gaps),
                experiments=summarize_experiment_targets(sample_gaps, label),
            )
        )

    plan_not_started = count_incomplete_rows(plan_list)
    if plan_not_started:
        lines.append(
            label["experiments_plan_gap"].format(
                count=plan_not_started,
                experiments=summarize_experiment_targets(plan_list, label),
            )
        )
    registry_not_started = count_incomplete_rows(registry_list)
    if registry_not_started:
        lines.append(
            label["experiments_registry_gap"].format(
                count=registry_not_started,
                experiments=summarize_experiment_targets(registry_list, label),
            )
        )
    return lines or [label["experiments_ok"]]


def format_action_item(item: ActionItem, label: dict[str, str]) -> str:
    return f"{render_priority(item.priority, label)} | {item.text}"


def issue_group(issue: Issue) -> str:
    return ISSUE_GROUP_BY_CODE.get(issue.code, "other")


def generated_artifact_issue_counts(issues: list[Issue]) -> dict[str, int]:
    counts = {label_key: 0 for label_key in GENERATED_ARTIFACT_ISSUE_CODES.values()}
    for issue in issues:
        label_key = GENERATED_ARTIFACT_ISSUE_CODES.get(issue.code)
        if label_key is None:
            continue
        counts[label_key] += 1
    return counts


def render_grouped_issues(
    issues: list[Issue],
    label: dict[str, str],
    language: str,
    max_items: int | None = None,
    per_group_limit: int | None = None,
) -> list[str]:
    lines: list[str] = []
    remaining = max_items
    for group in ISSUE_GROUP_ORDER:
        grouped = [issue for issue in issues if issue_group(issue) == group]
        if not grouped:
            continue
        if remaining is not None and remaining <= 0:
            break
        lines.extend(["", f"#### {label[f'group_{group}']}", ""])
        group_remaining = len(grouped)
        displayed = 0
        for issue in grouped:
            if remaining is not None and remaining <= 0:
                break
            if per_group_limit is not None and displayed >= per_group_limit:
                break
            lines.append(f"- {render_issue(issue, language)}")
            displayed += 1
            group_remaining -= 1
            if remaining is not None:
                remaining -= 1
        if group_remaining > 0:
            lines.append(f"- {label['omitted_group_items'].format(count=group_remaining)}")
    return lines


def append_evidence_detail_sections(
    lines: list[str],
    evidence_summary: EvidenceAuditResult,
    label: dict[str, str],
) -> None:
    lines.extend(["", f"### {label['duplicate_source_rows']}", ""])
    if evidence_summary.duplicate_ids:
        lines.extend(
            [
                f"| {label['source_id']} | {label['count']} |",
                "| --- | --- |",
            ]
        )
        for source_id, count in sorted(evidence_summary.duplicate_ids.items()):
            lines.append(f"| {source_id} | {count} |")
    else:
        lines.append(f"- {label['none']}")

    lines.extend(["", f"### {label['unknown_source_refs']}", ""])
    if evidence_summary.unknown_ids:
        lines.extend(
            [
                f"| {label['source_id']} | {label['references']} |",
                "| --- | --- |",
            ]
        )
        for source_id, locations in sorted(evidence_summary.unknown_ids.items()):
            lines.append(
                f"| {source_id} | {summarize_locations(locations, label)} |"
            )
    else:
        lines.append(f"- {label['none']}")

    lines.extend(["", f"### {label['blank_ref_rows']}", ""])
    if evidence_summary.blank_references:
        lines.extend(
            [
                f"| {label['location']} | {label['row']} | {label['field']} |",
                "| --- | --- | --- |",
            ]
        )
        for item in evidence_summary.blank_references:
            lines.append(f"| {item.location} | {item.row} | {item.field} |")
    else:
        lines.append(f"- {label['none']}")

    lines.extend(["", f"### {label['doc_citation_rows']}", ""])
    if evidence_summary.docs_without_citations:
        lines.extend(
            [
                f"| {label['document']} | {label['sections']} |",
                "| --- | --- |",
            ]
        )
        for filename, sections in evidence_summary.docs_without_citations:
            lines.append(f"| {filename} | {sections} |")
    else:
        lines.append(f"- {label['none']}")

    lines.extend(["", f"### {label['unused_source_rows']}", ""])
    if evidence_summary.unused_ids:
        lines.extend(
            [
                f"| {label['source_id']} | {label['source_type']} | {label['title_col']} |",
                "| --- | --- | --- |",
            ]
        )
        for source_id in evidence_summary.unused_ids:
            row = evidence_summary.ledger_ids.get(source_id, {})
            lines.append(
                f"| {source_id} | {row.get('source_type','')} | {row.get('title','')} |"
            )
    else:
        lines.append(f"- {label['none']}")


def audit_status(
    issues: list[Issue], evidence_result: EvidenceAuditResult | None = None
) -> str:
    if evidence_result is not None and evidence_result.status == "FAIL":
        return "FAIL"
    if any(issue.severity == "error" for issue in issues):
        return "FAIL"
    if evidence_result is not None and evidence_result.status == "WARN":
        return "WARN"
    if any(issue.severity == "warning" for issue in issues):
        return "WARN"
    return "PASS"


def recommend_actions(
    issues: list[Issue],
    doc_rows: list[dict[str, object]],
    has_support: bool,
    has_archetype: bool,
    has_experiments: bool,
    label: dict[str, str],
    language: str,
    docs_dir: Path | None = None,
    evidence_result: EvidenceAuditResult | None = None,
) -> list[str]:
    actions: list[ActionItem] = []
    sequence = 0
    experiment_summary = (
        summarize_experiments(docs_dir)
        if has_experiments and docs_dir is not None
        else None
    )

    def add_action(priority: str, text: str) -> None:
        nonlocal sequence
        actions.append(ActionItem(priority=priority, text=text, order=sequence))
        sequence += 1

    missing_docs = [row["file"] for row in doc_rows if not row["exists"]]
    if missing_docs:
        add_action(
            "blocker",
            label["action_restore_docs"].format(value=", ".join(missing_docs[:3])),
        )

    placeholder_hotspots = summarize_placeholder_hotspots(doc_rows)
    for priority in ("high", "medium", "low"):
        bucket = [row for row in placeholder_hotspots if row["priority"] == priority]
        if not bucket:
            continue
        limit = 1 if priority == "high" else 2
        selected = bucket[:limit]
        add_action(
            priority,
            label["action_replace_placeholders"].format(
                value=", ".join(
                    f"`{row['file']}` ({row['blank_count']})" for row in selected
                )
            ),
        )

    codes = {issue.code for issue in issues}

    if "default_baseline_placeholder" in codes:
        add_action("blocker", label["action_lock_baseline"])

    if has_support and "empty_source_ledger" in codes:
        add_action("high", label["action_populate_sources"])
    if evidence_result is not None:
        if evidence_result.duplicate_ids or evidence_result.unknown_ids:
            add_action("blocker", label["action_fix_unknown_sources"])
        if evidence_result.blank_references:
            add_action("high", label["action_fix_blank_source_refs"])
        if evidence_result.docs_without_citations:
            add_action("medium", label["action_fix_doc_citations"])
        if evidence_result.unused_ids:
            add_action("low", label["action_review_unused_sources"])

    bundle_refresh_action = build_generated_bundle_action(
        issues, label, language, docs_dir
    )
    if bundle_refresh_action is not None:
        priority, text = bundle_refresh_action
        add_action(priority, text)
    else:
        stale_experiment_summaries = stale_issue_paths(issues, "stale_experiment_summary")
        if stale_experiment_summaries:
            command = build_experiment_summary_command(
                stale_experiment_summaries, language, docs_dir
            )
            add_action(
                "medium",
                label["action_refresh_experiment_summary"].format(
                    command=command or label["none"],
                    value=summarize_display_values(stale_experiment_summaries, label),
                ),
            )

        stale_evidence_outputs = stale_issue_paths(issues, "stale_evidence_link_audit")
        if stale_evidence_outputs:
            command = build_evidence_audit_command(stale_evidence_outputs, language)
            add_action(
                "medium",
                label["action_refresh_evidence_audit"].format(
                    command=command or label["none"],
                    value=summarize_display_values(stale_evidence_outputs, label),
                ),
            )

        stale_status_reports = stale_issue_paths(issues, "stale_status_report")
        if stale_status_reports:
            command = build_status_report_command(stale_status_reports, language)
            add_action(
                "medium",
                label["action_refresh_status_report"].format(
                    command=command or label["none"],
                    value=summarize_display_values(stale_status_reports, label),
                ),
            )

        stale_handoff_dossiers = stale_issue_paths(issues, "stale_handoff_dossier")
        if stale_handoff_dossiers:
            command = build_handoff_dossier_command(
                stale_handoff_dossiers, language, docs_dir
            )
            add_action(
                "medium",
                label["action_refresh_handoff_dossier"].format(
                    command=command or label["none"],
                    value=summarize_display_values(stale_handoff_dossiers, label),
                ),
            )

        stale_handoff_manifests = stale_issue_paths(issues, "stale_handoff_bundle")
        if stale_handoff_manifests:
            command = build_handoff_manifest_command(stale_handoff_manifests, language)
            add_action(
                "medium",
                label["action_refresh_handoff_bundle"].format(
                    command=command or label["none"],
                    value=summarize_display_values(stale_handoff_manifests, label),
                ),
            )
    if has_support and (
        "empty_role_coverage" in codes
        or "missing_role_coverage_roles" in codes
        or "incomplete_role_coverage" in codes
    ):
        add_action("medium", label["action_advance_roles"])
    if has_experiments and "no_experiment_plan_progress" in codes:
        plan_rows = (
            experiment_summary.get("plan_rows", [])
            if isinstance(experiment_summary, dict)
            else []
        )
        if isinstance(plan_rows, list) and plan_rows:
            add_action(
                "medium",
                label["action_mark_plan_specific"].format(
                    value=summarize_experiment_targets(plan_rows, label)
                ),
            )
        else:
            add_action("medium", label["action_mark_plan"])
    if has_experiments and "no_experiment_registry_progress" in codes:
        registry_rows = (
            experiment_summary.get("registry_rows", [])
            if isinstance(experiment_summary, dict)
            else []
        )
        if isinstance(registry_rows, list) and registry_rows:
            add_action(
                "medium",
                label["action_update_registry_specific"].format(
                    value=summarize_experiment_targets(registry_rows, label)
                ),
            )
        else:
            add_action("medium", label["action_update_registry"])
    if has_experiments and "no_experiment_raw_samples" in codes:
        records = (
            experiment_summary.get("records", [])
            if isinstance(experiment_summary, dict)
            else []
        )
        if isinstance(records, list):
            sample_gaps = [
                row
                for row in records
                if normalize_status(str(row.get("status", ""))) != "completed"
                and int(row.get("samples", 0) or 0) <= 0
            ]
        else:
            sample_gaps = []
        if sample_gaps:
            add_action(
                "medium",
                label["action_capture_samples_specific"].format(
                    value=summarize_experiment_targets(sample_gaps, label)
                ),
            )
        else:
            add_action("medium", label["action_capture_samples"])
    if has_archetype and "no_archetype_checklist_progress" in codes:
        add_action("medium", label["action_progress_checklist"])
    if has_archetype and "no_archetype_metric_bands" in codes:
        add_action("medium", label["action_populate_metrics"])

    if not actions:
        return [label["no_actions"]]

    deduped: dict[str, ActionItem] = {}
    for action in actions:
        existing = deduped.get(action.text)
        if existing is None:
            deduped[action.text] = action
            continue
        current_rank = ACTION_PRIORITY_RANK[action.priority]
        existing_rank = ACTION_PRIORITY_RANK[existing.priority]
        if current_rank < existing_rank:
            deduped[action.text] = ActionItem(
                priority=action.priority,
                text=action.text,
                order=existing.order,
            )

    ordered = sorted(
        deduped.values(),
        key=lambda item: (ACTION_PRIORITY_RANK[item.priority], item.order),
    )
    return [format_action_item(item, label) for item in ordered[:ACTION_OUTPUT_LIMIT]]


def build_report(
    docs_dir: Path,
    mode: str,
    language: str,
    evidence_result: EvidenceAuditResult | None = None,
    ignored_generated_paths: set[str] | None = None,
) -> str:
    label = LANG[language]
    manifest = parse_manifest(docs_dir / "research-manifest.yaml")
    issues = run_audit(docs_dir, ignored_generated_paths)
    has_support, has_archetype, has_experiments = detect_support_features(docs_dir, manifest)
    game = manifest.get("game") or docs_dir.name
    baseline = manifest.get("baseline_version") or label["not_available"]
    archetype = manifest.get("archetype") or label["not_available"]
    doc_rows = build_doc_rows(docs_dir, label)
    evidence_summary = summarize_evidence(docs_dir, language, evidence_result)
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    generated_artifact_counts = generated_artifact_issue_counts(issues)
    status = audit_status(issues, evidence_summary)
    actions = recommend_actions(
        issues,
        doc_rows,
        has_support,
        has_archetype,
        has_experiments,
        label,
        language,
        docs_dir,
        evidence_summary,
    )

    lines = [f"# {label['title'].format(game=game)}", ""]
    lines.extend(
        [
            f"## {label['snapshot']}",
            "",
            f"- {label['audit_result']}: `{status}`",
            f"- {label['error_count']}: `{len(errors)}`",
            f"- {label['warning_count']}: `{len(warnings)}`",
            f"- {label['baseline']}: `{baseline}`",
            f"- {label['archetype']}: `{archetype}`",
            f"- {label['support']}: `{label['yes'] if has_support else label['no']}`",
            f"- {label['experiments']}: `{label['yes'] if has_experiments else label['no']}`",
        ]
    )
    if evidence_summary is not None:
        evidence_priority = render_priority(
            highest_evidence_priority(evidence_summary), label
        )
        lines.extend(
            [
                f"- {label['evidence_status']}: `{evidence_summary.status}`",
                f"- {label['evidence_priority']}: `{evidence_priority}`",
                f"- {label['duplicate_sources']}: `{len(evidence_summary.duplicate_ids)}`",
                f"- {label['unknown_sources']}: `{len(evidence_summary.unknown_ids)}`",
                f"- {label['blank_source_refs']}: `{len(evidence_summary.blank_references)}`",
                f"- {label['doc_citation_gaps']}: `{len(evidence_summary.docs_without_citations)}`",
                f"- {label['stale_experiment_summaries']}: `{generated_artifact_counts['stale_experiment_summaries']}`",
                f"- {label['stale_evidence_audits']}: `{generated_artifact_counts['stale_evidence_audits']}`",
                f"- {label['stale_status_reports']}: `{generated_artifact_counts['stale_status_reports']}`",
                f"- {label['stale_handoff_dossiers']}: `{generated_artifact_counts['stale_handoff_dossiers']}`",
                f"- {label['stale_handoff_manifests']}: `{generated_artifact_counts['stale_handoff_manifests']}`",
            ]
        )
    else:
        lines.extend(
            [
                f"- {label['stale_experiment_summaries']}: `{generated_artifact_counts['stale_experiment_summaries']}`",
                f"- {label['stale_evidence_audits']}: `{generated_artifact_counts['stale_evidence_audits']}`",
                f"- {label['stale_status_reports']}: `{generated_artifact_counts['stale_status_reports']}`",
                f"- {label['stale_handoff_dossiers']}: `{generated_artifact_counts['stale_handoff_dossiers']}`",
                f"- {label['stale_handoff_manifests']}: `{generated_artifact_counts['stale_handoff_manifests']}`",
            ]
        )

    lines.extend(
        [
            "",
            f"## {label['documents']}",
            "",
            f"| {label['file']} | {label['status']} | {label['missing_sections']} | {label['blank_placeholders']} |",
            "| --- | --- | --- | --- |",
        ]
    )
    compact_doc_rows, omitted_docs = summarize_compact_doc_rows(doc_rows)
    document_rows = doc_rows if mode == "full" else compact_doc_rows
    for row in document_rows:
        missing_text = ", ".join(row["missing"]) if row["missing"] else "-"
        blank_value = str(row["blank_count"]) if row["exists"] else "-"
        lines.append(
            f"| {row['file']} | {row['status']} | {missing_text} | {blank_value} |"
        )
    if mode != "full" and omitted_docs:
        lines.extend(["", f"- {label['folded_docs'].format(count=omitted_docs)}"])
    if mode == "full":
        placeholder_hotspots = summarize_placeholder_hotspots(doc_rows)
        lines.extend(["", f"### {label['placeholder_hotspots']}", ""])
        if placeholder_hotspots:
            lines.extend(
                [
                    f"| {label['priority']} | {label['file']} | {label['blank_placeholders']} |",
                    "| --- | --- | --- |",
                ]
            )
            for row in placeholder_hotspots:
                lines.append(
                    f"| {render_priority(str(row['priority']), label)} | {row['file']} | {row['blank_count']} |"
                )
        else:
            lines.append(f"- {label['none']}")

    if has_support:
        support = summarize_support_data(docs_dir)
        role_rows, role_summary = summarize_role_coverage(docs_dir)
        lines.extend(["", f"## {label['support_data']}", ""])
        if mode == "full":
            lines.extend(
                [
                    f"- {label['sources_with_evidence']}: `{support['sources']}`",
                    f"- {label['formulas_captured']}: `{support['formulas']}`",
                    f"- {label['assets_detailed']}: `{support['assets']}`",
                    f"- {label['risks_populated']}: `{support['risks']}`",
                    "",
                    f"## {label['role_coverage']}",
                    "",
                    f"- {label['roles_summary']}: {role_summary}",
                ]
            )
            lines.extend(
                [
                    "",
                    f"| {label['role']} | {label['status']} | {label['key_findings']} | {label['missing_evidence']} |",
                    "| --- | --- | --- | --- |",
                ]
            )
            for row in role_rows:
                lines.append(
                    f"| {row.get('role','')} | {row.get('status','')} | {row.get('key_findings','')} | {row.get('missing_evidence','')} |"
                )
        else:
            for item in build_compact_support_lines(support, label):
                lines.append(f"- {item}")
            lines.extend(["", f"## {label['role_coverage']}", ""])
            for item in build_compact_role_lines(role_rows, role_summary, label):
                lines.append(f"- {item}")

    if evidence_summary is not None:
        evidence_priority = render_priority(
            highest_evidence_priority(evidence_summary), label
        )
        lines.extend(
            [
                "",
                f"## {label['evidence']}",
                "",
                f"- {label['evidence_status']}: `{evidence_summary.status}`",
                f"- {label['evidence_priority']}: `{evidence_priority}`",
                f"- {label['duplicate_sources']}: `{len(evidence_summary.duplicate_ids)}`",
                f"- {label['unknown_sources']}: `{len(evidence_summary.unknown_ids)}`",
                f"- {label['blank_source_refs']}: `{len(evidence_summary.blank_references)}`",
                f"- {label['unused_sources']}: `{len(evidence_summary.unused_ids)}`",
                f"- {label['doc_citation_gaps']}: `{len(evidence_summary.docs_without_citations)}`",
            ]
        )
        evidence_findings = evidence_issue_counts(evidence_summary)
        if evidence_findings:
            lines.extend(["", f"| {label['priority']} | {label['findings']} |", "| --- | --- |"])
            finding_labels = {
                "duplicate_ids": label["duplicate_sources"],
                "unknown_ids": label["unknown_sources"],
                "blank_references": label["blank_source_refs"],
                "docs_without_citations": label["doc_citation_gaps"],
                "unused_ids": label["unused_sources"],
            }
            for priority, key, count in evidence_findings:
                lines.append(
                    f"| {render_priority(priority, label)} | {finding_labels[key]}: {count} |"
                )
        if mode == "full":
            append_evidence_detail_sections(lines, evidence_summary, label)

    if has_archetype:
        archetype_summary = summarize_archetype(docs_dir)
        lines.extend(["", f"## {label['archetype_snapshot']}", ""])
        if mode == "full":
            lines.extend(
                [
                    f"- {label['checklist_progress']}: `{archetype_summary['checklist_progressed']}` / `{archetype_summary['checklist_total']}`",
                    f"- {label['metric_progress']}: `{archetype_summary['metric_populated']}` / `{archetype_summary['metric_total']}`",
                ]
            )
        else:
            for item in build_compact_archetype_lines(archetype_summary, label):
                lines.append(f"- {item}")

    if has_experiments:
        experiment_summary = summarize_experiments(docs_dir)
        lines.extend(["", f"## {label['experiments_snapshot']}", ""])
        if mode == "full":
            lines.extend(
                [
                    f"- {label['plan_status']}: {experiment_summary['plan_summary']}",
                    f"- {label['registry_status']}: {experiment_summary['registry_summary']}",
                    f"- {label['raw_samples']}: `{experiment_summary['raw_samples']}`",
                ]
            )
        else:
            for item in build_compact_experiment_lines(experiment_summary, label):
                lines.append(f"- {item}")
        if mode == "full" and experiment_summary["detail_counts"]:
            lines.extend(
                [
                    "",
                    f"| {label['detail_file']} | {label['samples']} |",
                    "| --- | --- |",
                ]
            )
            for filename, count in experiment_summary["detail_counts"]:
                lines.append(f"| {filename} | {count} |")

    lines.extend(["", f"## {label['findings']}", ""])
    lines.append(f"### {label['errors']}")
    lines.append("")
    if errors:
        lines.extend(render_grouped_issues(errors, label, language))
    else:
        lines.append(f"- {label['no_errors']}")

    lines.extend(["", f"### {label['warnings']}", ""])
    if warnings:
        if mode == "full":
            lines.extend(render_grouped_issues(warnings, label, language))
        else:
            lines.extend(
                render_grouped_issues(
                    warnings, label, language, per_group_limit=2
                )
            )
    else:
        lines.append(f"- {label['no_warnings']}")

    lines.extend(["", f"## {label['next_actions']}", ""])
    for action in actions:
        lines.append(f"- {action}")

    return "\n".join(lines).rstrip() + "\n"


def resolve_output_path(docs_dir: Path, output: str | None, mode: str) -> Path:
    target = output or DEFAULT_OUTPUTS[mode]
    path = Path(target)
    if not path.is_absolute():
        path = docs_dir / path
    return path


def resolve_modes(mode: str) -> list[str]:
    if mode == "both":
        return ["full", "compact"]
    return [mode]


def relative_output_path(path: Path, docs_dir: Path) -> str:
    return str(path.relative_to(docs_dir)).replace("\\", "/")


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        raise NotADirectoryError(f"{docs_dir} is not a directory.")

    language = detect_language(docs_dir) if args.language == "auto" else args.language
    if args.mode == "both" and args.output:
        raise ValueError("--output cannot be used together with --mode both.")

    modes = resolve_modes(args.mode)
    planned_output_paths = [resolve_output_path(docs_dir, args.output, mode) for mode in modes]
    ignored_generated_paths = {
        relative_output_path(path, docs_dir) for path in planned_output_paths
    }

    for mode, output_path in zip(modes, planned_output_paths):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = build_report(
            docs_dir,
            mode,
            language,
            ignored_generated_paths=ignored_generated_paths,
        )
        output_path.write_text(report, encoding="utf-8")
        print(f"Wrote pack status report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
