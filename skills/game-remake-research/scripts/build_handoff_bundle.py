#!/usr/bin/env python3
"""Build a handoff bundle for a remake research pack."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from audit_evidence_links import build_markdown as build_evidence_markdown
from audit_evidence_links import (
    evidence_issue_counts,
    highest_evidence_priority,
    run_evidence_audit,
)
from audit_remake_pack import run_audit
from build_pack_status_report import (
    build_report,
    detect_language,
    recommend_actions,
    build_doc_rows,
    audit_status,
    generated_artifact_issue_counts,
    render_grouped_issues,
)
from merge_remake_docs import build_output, collect_markdown_files
from rollup_experiment_metrics import run_rollup
from summarize_experiments import (
    build_summary,
    parse_manifest_title,
    read_csv_rows,
)
from audit_remake_pack import detect_support_features, parse_manifest


DOSSIER_OUTPUTS = {
    "full": "handoff-full-dossier.md",
    "compact": "handoff-compact-dossier.md",
}

REPORT_OUTPUTS = {
    "full": "reports/pack-status.md",
    "compact": "reports/pack-status-compact.md",
}

SUMMARY_OUTPUTS = {
    "full": "10-experiment-summary.md",
    "compact": "10-experiment-summary-compact.md",
}

MANIFEST_OUTPUT = "reports/handoff-bundle.md"
EVIDENCE_OUTPUT = "reports/evidence-link-audit.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a handoff bundle for a remake research pack."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Research pack directory.",
    )
    parser.add_argument(
        "--dossier-mode",
        choices=("none", "full", "compact", "both"),
        default="compact",
        help="Which dossier variants to generate. Defaults to compact.",
    )
    parser.add_argument(
        "--report-mode",
        choices=("none", "full", "compact", "both"),
        default="both",
        help="Which status-report variants to generate. Defaults to both.",
    )
    parser.add_argument(
        "--include-log",
        action="store_true",
        help="Include 99-research-log.md in generated dossiers.",
    )
    parser.add_argument(
        "--rollup-metrics",
        action="store_true",
        help="Run metric rollup before summaries when archetype metric files exist.",
    )
    parser.add_argument(
        "--strict-audit",
        action="store_true",
        help="Return non-zero when warnings remain after bundle generation.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "en"),
        default="auto",
        help="Output language for generated reports. Defaults to auto, which currently resolves to en.",
    )
    parser.add_argument(
        "--manifest-output",
        default=MANIFEST_OUTPUT,
        help="Manifest markdown path. Relative paths are resolved inside docs-dir.",
    )
    return parser.parse_args()


def resolve_modes(mode: str) -> list[str]:
    if mode == "both":
        return ["full", "compact"]
    if mode == "none":
        return []
    return [mode]


def resolve_output_path(docs_dir: Path, target: str) -> Path:
    path = Path(target)
    if not path.is_absolute():
        path = docs_dir / path
    return path


def summarize_locations(locations: list[str], language: str, limit: int = 2) -> str:
    if len(locations) <= limit:
        return "; ".join(locations)
    shown = "; ".join(locations[:limit])
    remainder = len(locations) - limit
    return f"{shown}; +{remainder} more"


def render_priority(priority: str, label: dict[str, str]) -> str:
    return label.get(f"priority_{priority}", priority)


def write_experiment_summary(docs_dir: Path, mode: str, language: str) -> Path | None:
    data_dir = docs_dir / "data"
    plan_rows = read_csv_rows(data_dir / "experiment-plan.csv")
    if not plan_rows:
        return None
    registry_rows = read_csv_rows(data_dir / "experiment-observations.csv")
    metric_rows = read_csv_rows(data_dir / "archetype-metrics.csv")
    title = parse_manifest_title(docs_dir, language)
    output = build_summary(
        title, plan_rows, registry_rows, metric_rows, docs_dir, mode, language
    )
    output_path = docs_dir / SUMMARY_OUTPUTS[mode]
    output_path.write_text(output, encoding="utf-8")
    return output_path


def write_dossier(
    docs_dir: Path, mode: str, include_log: bool, game: str, language: str
) -> Path:
    output_name = DOSSIER_OUTPUTS[mode]
    files = collect_markdown_files(docs_dir, output_name, include_log, mode)
    title = f"{game} Handoff Dossier ({mode})"
    output = build_output(title, files)
    output_path = docs_dir / output_name
    output_path.write_text(output, encoding="utf-8")
    return output_path


def write_status_report(
    docs_dir: Path,
    mode: str,
    language: str,
    evidence_result=None,
    ignored_generated_paths: set[str] | None = None,
) -> Path:
    output_path = resolve_output_path(docs_dir, REPORT_OUTPUTS[mode])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(
        docs_dir,
        mode,
        language,
        evidence_result,
        ignored_generated_paths,
    )
    output_path.write_text(report, encoding="utf-8")
    return output_path


def build_manifest(
    docs_dir: Path,
    manifest_output: Path,
    game: str,
    language: str,
    generated_paths: list[Path],
    rollup_result: tuple[int, int, Path, list[dict[str, str]]] | None,
    issues: list,
    evidence_result,
    strict_audit: bool,
) -> str:
    has_errors = any(issue.severity == "error" for issue in issues)
    has_warnings = any(issue.severity == "warning" for issue in issues)
    combined_status = audit_status(issues, evidence_result)
    generated_artifact_counts = generated_artifact_issue_counts(issues)
    label = {
        "en": {
            "title": f"{game} Handoff Bundle",
            "snapshot": "Snapshot",
            "artifacts": "Generated Artifacts",
            "audit": "Audit",
            "actions": "Recommended Next Actions",
            "errors": "Errors",
            "warnings": "Warnings",
            "none": "None.",
            "strict": "Strict audit",
            "rollup": "Metric rollup",
            "skipped": "skipped",
            "updated": "updated",
            "generated_at": "Generated at",
            "evidence_priority": "Highest evidence priority",
            "duplicate_sources": "Duplicate source IDs",
            "unknown_sources": "Unknown source IDs",
            "blank_source_refs": "Rows missing source refs",
            "unused_sources": "Unused ledger IDs",
            "doc_citation_gaps": "Docs missing inline citations",
            "stale_experiment_summaries": "Stale experiment summaries",
            "stale_evidence_audits": "Stale evidence audits",
            "stale_status_reports": "Stale status reports",
            "stale_handoff_dossiers": "Stale handoff dossiers",
            "stale_handoff_manifests": "Stale handoff manifests",
            "yes": "yes",
            "no": "no",
            "skip_count": "skipped",
            "evidence_audit": "Evidence link audit",
            "evidence_findings": "Evidence findings",
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
            "evidence_duplicate_detail": "Duplicate source example",
            "evidence_unknown_detail": "Unknown source example",
            "evidence_blank_detail": "Blank source-ref example",
            "evidence_unused_detail": "Unused ledger example",
            "evidence_doc_detail": "Citation-gap example",
        },
    }[language]

    pack_manifest = parse_manifest(docs_dir / "research-manifest.yaml")
    has_support, has_archetype, has_experiments = detect_support_features(
        docs_dir, pack_manifest
    )
    doc_rows = build_doc_rows(docs_dir, {"status_ok": "", "status_review": "", "status_missing": ""})
    action_label = {
        "en": {
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
            "priority_blocker": "blocker",
            "priority_high": "high",
            "priority_medium": "medium",
            "priority_low": "low",
            "names_more": "+{count} more",
            "none": "None.",
            "no_actions": "No immediate actions.",
        },
    }[language]
    actions = recommend_actions(
        issues,
        doc_rows,
        has_support,
        has_archetype,
        has_experiments,
        action_label,
        language,
        docs_dir,
        evidence_result,
    )

    lines = [f"# {label['title']}", ""]
    lines.extend(
        [
            f"## {label['snapshot']}",
            "",
            f"- {label['generated_at']}: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
            f"- {label['audit']}: `{combined_status}`",
            f"- {label['errors']}: `{sum(1 for issue in issues if issue.severity == 'error')}`",
            f"- {label['warnings']}: `{sum(1 for issue in issues if issue.severity == 'warning')}`",
            f"- {label['strict']}: `{label['yes'] if strict_audit else label['no']}`",
        ]
    )
    if evidence_result is not None:
        evidence_priority = render_priority(
            highest_evidence_priority(evidence_result), label
        )
        lines.append(f"- {label['evidence_audit']}: `{evidence_result.status}`")
        lines.append(f"- {label['evidence_priority']}: `{evidence_priority}`")
        lines.append(
            f"- {label['duplicate_sources']}: `{len(evidence_result.duplicate_ids)}`"
        )
        lines.append(
            f"- {label['unknown_sources']}: `{len(evidence_result.unknown_ids)}`"
        )
        lines.append(
            f"- {label['blank_source_refs']}: `{len(evidence_result.blank_references)}`"
        )
        lines.append(
            f"- {label['doc_citation_gaps']}: `{len(evidence_result.docs_without_citations)}`"
        )
    lines.append(
        f"- {label['stale_experiment_summaries']}: `{generated_artifact_counts['stale_experiment_summaries']}`"
    )
    lines.append(
        f"- {label['stale_evidence_audits']}: `{generated_artifact_counts['stale_evidence_audits']}`"
    )
    lines.append(
        f"- {label['stale_status_reports']}: `{generated_artifact_counts['stale_status_reports']}`"
    )
    lines.append(
        f"- {label['stale_handoff_dossiers']}: `{generated_artifact_counts['stale_handoff_dossiers']}`"
    )
    lines.append(
        f"- {label['stale_handoff_manifests']}: `{generated_artifact_counts['stale_handoff_manifests']}`"
    )

    if rollup_result is None:
        lines.append(f"- {label['rollup']}: `{label['skipped']}`")
    else:
        updated, skipped, metrics_path, _rows = rollup_result
        lines.append(
            f"- {label['rollup']}: `{label['updated']}={updated}` `{label['skip_count']}={skipped}` `{metrics_path.relative_to(docs_dir)}`"
        )

    lines.extend(["", f"## {label['artifacts']}", ""])
    for path in generated_paths:
        lines.append(f"- `{path.relative_to(docs_dir)}`")
    if not generated_paths:
        lines.append(f"- {label['none']}")

    error_issues = [issue for issue in issues if issue.severity == "error"]
    warning_issues = [issue for issue in issues if issue.severity == "warning"]
    lines.extend(["", f"## {label['audit']}", "", f"### {label['errors']}", ""])
    if error_issues:
        lines.extend(render_grouped_issues(error_issues, label, language))
    else:
        lines.append(f"- {label['none']}")

    lines.extend(["", f"### {label['warnings']}", ""])
    if warning_issues:
        lines.extend(
            render_grouped_issues(warning_issues, label, language, per_group_limit=2)
        )
    else:
        lines.append(f"- {label['none']}")

    if evidence_result is not None:
        lines.extend(["", f"### {label['evidence_findings']}", ""])
        evidence_items: list[str] = []
        finding_labels = {
            "duplicate_ids": label["duplicate_sources"],
            "unknown_ids": label["unknown_sources"],
            "blank_references": label["blank_source_refs"],
            "docs_without_citations": label["doc_citation_gaps"],
            "unused_ids": label["unused_sources"],
        }
        for priority, key, count in evidence_issue_counts(evidence_result):
            evidence_items.append(
                f"{render_priority(priority, label)} | {finding_labels[key]}: {count}"
            )
        if evidence_result.duplicate_ids:
            source_id, count = next(iter(sorted(evidence_result.duplicate_ids.items())))
            evidence_items.append(
                f"{label['evidence_duplicate_detail']}: `{source_id}` x{count}"
            )
        if evidence_result.unknown_ids:
            source_id, locations = next(iter(sorted(evidence_result.unknown_ids.items())))
            evidence_items.append(
                f"{label['evidence_unknown_detail']}: `{source_id}` -> {summarize_locations(locations, language)}"
            )
        if evidence_result.blank_references:
            item = evidence_result.blank_references[0]
            evidence_items.append(
                f"{label['evidence_blank_detail']}: `{item.location}` / `{item.row}` / `{item.field}`"
            )
        if evidence_result.unused_ids:
            source_id = evidence_result.unused_ids[0]
            evidence_items.append(
                f"{label['evidence_unused_detail']}: `{source_id}`"
            )
        if evidence_result.docs_without_citations:
            filename, sections = evidence_result.docs_without_citations[0]
            evidence_items.append(
                f"{label['evidence_doc_detail']}: `{filename}` -> {sections}"
            )
        if evidence_items:
            for item in evidence_items:
                lines.append(f"- {item}")
        else:
            lines.append(f"- {label['none']}")

    lines.extend(["", f"## {label['actions']}", ""])
    for action in actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def relative_output_path(path: Path, docs_dir: Path) -> str:
    return str(path.relative_to(docs_dir)).replace("\\", "/")


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        raise NotADirectoryError(f"{docs_dir} is not a directory.")

    language = detect_language(docs_dir) if args.language == "auto" else args.language
    manifest = parse_manifest(docs_dir / "research-manifest.yaml")
    game = manifest.get("game") or docs_dir.name
    has_support, _has_archetype, has_experiments = detect_support_features(
        docs_dir, manifest
    )

    generated_paths: list[Path] = []
    rollup_result = None
    evidence_result = None

    if args.rollup_metrics and has_support:
        metrics_path = docs_dir / "data" / "archetype-metrics.csv"
        links_path = docs_dir / "data" / "archetype-metric-links.csv"
        if metrics_path.exists() and links_path.exists():
            rollup_result = run_rollup(docs_dir)

    if has_experiments:
        summary_modes = set()
        dossier_modes = resolve_modes(args.dossier_mode)
        existing_summary_modes = {
            mode
            for mode, relative_path in SUMMARY_OUTPUTS.items()
            if (docs_dir / relative_path).exists()
        }
        summary_modes.update(existing_summary_modes)
        if "full" in dossier_modes:
            summary_modes.add("full")
        if "compact" in dossier_modes:
            summary_modes.add("compact")
        if not summary_modes:
            summary_modes.add("full")
        for mode in sorted(summary_modes):
            path = write_experiment_summary(docs_dir, mode, language)
            if path:
                generated_paths.append(path)

    if has_support and (docs_dir / "data" / "source-ledger.csv").exists():
        evidence_result = run_evidence_audit(docs_dir, language)
        evidence_path = resolve_output_path(docs_dir, EVIDENCE_OUTPUT)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            build_evidence_markdown(evidence_result, docs_dir), encoding="utf-8"
        )
        generated_paths.append(evidence_path)

    report_modes = resolve_modes(args.report_mode)
    dossier_modes = resolve_modes(args.dossier_mode)
    report_ignored_generated_paths = {
        relative_output_path(resolve_output_path(docs_dir, REPORT_OUTPUTS[mode]), docs_dir)
        for mode in report_modes
    }
    report_ignored_generated_paths.update(
        relative_output_path(resolve_output_path(docs_dir, DOSSIER_OUTPUTS[mode]), docs_dir)
        for mode in dossier_modes
    )
    report_ignored_generated_paths.add(
        relative_output_path(resolve_output_path(docs_dir, args.manifest_output), docs_dir)
    )
    for mode in report_modes:
        generated_paths.append(
            write_status_report(
                docs_dir,
                mode,
                language,
                evidence_result,
                report_ignored_generated_paths,
            )
        )

    for mode in dossier_modes:
        generated_paths.append(
            write_dossier(docs_dir, mode, args.include_log, game, language)
        )

    manifest_path = resolve_output_path(docs_dir, args.manifest_output)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ignored_generated_paths = {str(manifest_path.relative_to(docs_dir)).replace("\\", "/")}
    issues = run_audit(docs_dir, ignored_generated_paths)
    manifest_output = build_manifest(
        docs_dir,
        manifest_path,
        game,
        language,
        generated_paths,
        rollup_result,
        issues,
        evidence_result,
        args.strict_audit,
    )
    manifest_path.write_text(manifest_output, encoding="utf-8")
    generated_paths.append(manifest_path)

    print(f"Wrote handoff bundle manifest to {manifest_path}")
    for path in generated_paths:
        print(f"- {path}")

    has_errors = any(issue.severity == "error" for issue in issues)
    has_warnings = any(issue.severity == "warning" for issue in issues)
    evidence_fail = evidence_result is not None and evidence_result.status == "FAIL"
    evidence_warn = evidence_result is not None and evidence_result.status == "WARN"
    if has_errors or evidence_fail or (args.strict_audit and (has_warnings or evidence_warn)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
