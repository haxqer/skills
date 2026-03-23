#!/usr/bin/env python3
"""Audit a remake research pack for structural and completion issues."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from merge_remake_docs import collect_markdown_files


CORE_DOC_REQUIREMENTS = {
    "00-overview-and-source-ledger.md": [
        ("Scope Lock",),
        ("Source Ledger",),
        ("Confidence Policy",),
        ("Top Unknowns",),
    ],
    "01-product-and-player-experience.md": [
        ("Product Definition",),
        ("North Star Experience",),
        ("Player Journey",),
        ("Loop Design",),
        ("Product Management Notes",),
        ("Confirmed Facts",),
        ("Inferred Model",),
        ("Remake Decisions",),
        ("Open Questions",),
    ],
    "02-systems-and-gameplay.md": [
        ("Control Grammar",),
        ("Movement And Combat",),
        ("Challenge Structure",),
        ("Gameplay Feel Notes",),
        ("Confirmed Facts",),
        ("Inferred Model",),
        ("Remake Decisions",),
        ("Open Questions",),
    ],
    "03-economy-and-balance.md": [
        ("Resource Map",),
        ("Faucets And Sinks",),
        ("Stat And Progression Model",),
        ("Formula Capture",),
        ("Tuning Risks",),
        ("Confirmed Facts",),
        ("Inferred Model",),
        ("Remake Decisions",),
        ("Open Questions",),
    ],
    "04-content-art-audio-narrative.md": [
        ("Content Taxonomy",),
        ("Art Direction",),
        ("Animation",),
        ("Music And Audio",),
        ("Copywriting And Narrative",),
        ("Confirmed Facts",),
        ("Inferred Model",),
        ("Remake Decisions",),
        ("Open Questions",),
    ],
    "05-client-architecture-and-production.md": [
        ("Product Targets",),
        ("Runtime Architecture",),
        ("Tools And Workflow",),
        ("Production Plan",),
        ("Risk Register",),
        ("Confirmed Facts",),
        ("Inferred Model",),
        ("Remake Decisions",),
        ("Open Questions",),
    ],
    "06-replica-backlog-and-acceptance.md": [
        ("Prioritized Backlog",),
        ("Vertical Slice Scope",),
        ("Full Production Scope",),
        ("Acceptance Criteria",),
        ("Open Gaps And Validation",),
    ],
    "99-research-log.md": [
        ("Observation Entries",),
        ("Frame / Timing Notes",),
        ("Contradictions To Resolve",),
    ],
}

ROLE_SET = {
    "product-manager",
    "professional-game-designer",
    "gameplay-designer",
    "balance-designer",
    "art",
    "animation",
    "music-audio",
    "copywriting",
    "narrative",
    "game-client-architect",
    "lead-engineer",
}

PLACEHOLDER_VALUES = {
    "",
    "[]",
    '""',
    "TBD version / region / platform / time slice",
}
STATUS_INCOMPLETE = {"", "not-started", "not started"}
SOURCE_MARKDOWN_EXCLUDES = {
    "10-experiment-summary.md",
    "10-experiment-summary-compact.md",
}

AUDIT_LABELS = {
    "en": {
        "audit_result": "Audit result",
        "errors": "Errors",
        "warnings": "Warnings",
        "none": "None.",
    },
}

ISSUE_TEMPLATES = {
    "missing_required_document": {
        "en": "Missing required document: {filename}",
    },
    "missing_section_heading": {
        "en": "{filename} is missing section heading: {heading}",
    },
    "blank_scaffold_placeholders": {
        "en": "{filename} still contains {count} blank scaffold placeholders. Sample: {sample}",
    },
    "missing_manifest_baseline_version": {
        "en": "research-manifest.yaml is missing a concrete baseline_version.",
    },
    "default_baseline_placeholder": {
        "en": "00-overview-and-source-ledger.md still uses the default baseline-version placeholder.",
    },
    "missing_manifest_file": {
        "en": "Support files are present but research-manifest.yaml is missing.",
    },
    "missing_support_file": {
        "en": "Support file missing: {path}",
    },
    "empty_source_ledger": {
        "en": "data/source-ledger.csv exists but still looks scaffold-empty.",
    },
    "empty_formula_catalog": {
        "en": "data/formula-catalog.csv has no captured formulas yet.",
    },
    "empty_risk_register": {
        "en": "data/risk-register.csv has no populated risk entries yet.",
    },
    "empty_role_coverage": {
        "en": "data/role-coverage.csv is missing or empty.",
    },
    "missing_role_coverage_roles": {
        "en": "data/role-coverage.csv is missing roles: {roles}",
    },
    "incomplete_role_coverage": {
        "en": "{count} role-coverage entries are still not-started.",
    },
    "missing_archetype_doc": {
        "en": "Archetype pack is missing {filename}.",
    },
    "missing_archetype_support_file": {
        "en": "Archetype support file missing: {path}",
    },
    "no_archetype_checklist_progress": {
        "en": "data/archetype-checklist.csv has no progressed checklist items yet.",
    },
    "no_archetype_metric_bands": {
        "en": "data/archetype-metrics.csv has no observed bands populated yet.",
    },
    "missing_experiment_support_path": {
        "en": "Experiment support is incomplete: missing {path}",
    },
    "missing_experiment_summary": {
        "en": "Experiment support is incomplete: missing 10-experiment-summary.md or 10-experiment-summary-compact.md.",
    },
    "no_experiment_plan_progress": {
        "en": "data/experiment-plan.csv has no experiments beyond not-started.",
    },
    "no_experiment_registry_progress": {
        "en": "data/experiment-observations.csv has no registry entries beyond not-started.",
    },
    "empty_experiment_detail_sheets": {
        "en": "data/experiments/ exists but contains no typed detail sheets.",
    },
    "no_experiment_raw_samples": {
        "en": "data/experiments/*.csv contains no captured raw samples yet.",
    },
    "stale_experiment_summary": {
        "en": "{path} is older than {count} research inputs. Newer inputs include: {sample}",
    },
    "stale_evidence_link_audit": {
        "en": "{path} is older than {count} evidence inputs. Newer inputs include: {sample}",
    },
    "stale_status_report": {
        "en": "{path} is older than {count} pack inputs. Newer inputs include: {sample}",
    },
    "stale_handoff_bundle": {
        "en": "{path} is older than {count} handoff inputs. Newer inputs include: {sample}",
    },
    "stale_handoff_dossier": {
        "en": "{path} is older than {count} dossier inputs. Newer inputs include: {sample}",
    },
}


@dataclass
class Issue:
    severity: str
    code: str
    data: dict[str, str] = field(default_factory=dict)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a remake research pack for missing sections and incomplete scaffolding."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Research pack directory to audit.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when warnings are present.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "en"),
        default="auto",
        help="Output language. Defaults to auto, which currently resolves to en.",
    )
    return parser.parse_args()


def detect_language(docs_dir: Path) -> str:
    return "en"


def make_issue(severity: str, code: str, **data: str) -> Issue:
    normalized = {key: str(value) for key, value in data.items()}
    return Issue(severity=severity, code=code, data=normalized)


def render_issue(issue: Issue, language: str) -> str:
    template = ISSUE_TEMPLATES[issue.code][language]
    return template.format(**issue.data)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
            rows.append({key: (value or "").strip() for key, value in row.items()})
        return rows


def parse_manifest(path: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    if not path.exists():
        return manifest
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line.startswith("#") or raw_line[0].isspace():
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        manifest[key.strip()] = unquote(value.strip())
    return manifest


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def is_meaningful(value: str) -> bool:
    return value.strip() not in PLACEHOLDER_VALUES


def collect_h2_headings(text: str) -> set[str]:
    headings: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            headings.add(stripped[3:].strip())
    return headings


def count_blank_placeholders(text: str) -> tuple[int, list[str]]:
    count = 0
    samples: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^- .+:\s*$", stripped):
            count += 1
            if len(samples) < 3:
                samples.append(stripped)
            continue
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]*", cell) for cell in cells):
            continue
        empty_cells = sum(1 for cell in cells if not cell)
        if empty_cells >= 2:
            count += 1
            if len(samples) < 3:
                samples.append(stripped)
    return count, samples


def count_meaningful_rows(rows: list[dict[str, str]], fields: list[str]) -> int:
    total = 0
    for row in rows:
        if any(is_meaningful(row.get(field, "")) for field in fields):
            total += 1
    return total


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
        if is_meaningful(value):
            return True
    return False


def relative_display(path: Path, docs_dir: Path) -> str:
    return str(path.relative_to(docs_dir)).replace("\\", "/")


def source_markdown_paths(docs_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(docs_dir.glob("*.md")):
        if path.name in SOURCE_MARKDOWN_EXCLUDES:
            continue
        if path.name.endswith("-dossier.md"):
            continue
        if path.name.endswith("-dossier-template.md"):
            continue
        if path.name.startswith("handoff-"):
            continue
        paths.append(path)
    return paths


def support_csv_paths(docs_dir: Path) -> list[Path]:
    data_dir = docs_dir / "data"
    paths = sorted(data_dir.glob("*.csv"))
    experiment_dir = data_dir / "experiments"
    if experiment_dir.exists():
        paths.extend(sorted(experiment_dir.glob("*.csv")))
    return paths


def experiment_summary_dependencies(docs_dir: Path) -> list[Path]:
    data_dir = docs_dir / "data"
    dependencies = [
        docs_dir / "research-manifest.yaml",
        data_dir / "experiment-plan.csv",
        data_dir / "experiment-observations.csv",
        data_dir / "archetype-metrics.csv",
    ]
    experiment_dir = data_dir / "experiments"
    if experiment_dir.exists():
        dependencies.extend(sorted(experiment_dir.glob("*.csv")))
    return [path for path in dependencies if path.exists()]


def evidence_audit_dependencies(docs_dir: Path) -> list[Path]:
    data_dir = docs_dir / "data"
    dependencies = source_markdown_paths(docs_dir)
    dependencies.extend(
        path
        for path in (
            data_dir / "source-ledger.csv",
            data_dir / "formula-catalog.csv",
            data_dir / "asset-taxonomy.csv",
            data_dir / "archetype-metrics.csv",
        )
        if path.exists()
    )
    experiment_dir = data_dir / "experiments"
    if experiment_dir.exists():
        dependencies.extend(sorted(experiment_dir.glob("*.csv")))
    return dependencies


def pack_input_dependencies(docs_dir: Path) -> list[Path]:
    dependencies = source_markdown_paths(docs_dir)
    manifest = docs_dir / "research-manifest.yaml"
    if manifest.exists():
        dependencies.append(manifest)
    dependencies.extend(support_csv_paths(docs_dir))
    return dependencies


def handoff_bundle_dependencies(docs_dir: Path) -> list[Path]:
    dependencies = pack_input_dependencies(docs_dir)
    dependencies.extend(
        path
        for path in (
            docs_dir / "10-experiment-summary.md",
            docs_dir / "10-experiment-summary-compact.md",
            docs_dir / "reports" / "evidence-link-audit.md",
            docs_dir / "reports" / "pack-status.md",
            docs_dir / "reports" / "pack-status-compact.md",
            docs_dir / "handoff-full-dossier.md",
            docs_dir / "handoff-compact-dossier.md",
        )
        if path.exists()
    )
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in dependencies:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def markdown_title(path: Path) -> str:
    for line in read_text(path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def handoff_dossier_includes_log(artifact: Path, docs_dir: Path) -> bool:
    log_path = docs_dir / "99-research-log.md"
    if not artifact.exists() or not log_path.exists():
        return False
    title = markdown_title(log_path)
    if not title:
        return False
    return f"# {title}" in read_text(artifact)


def handoff_dossier_dependencies(docs_dir: Path, artifact: Path) -> list[Path]:
    mode = "compact" if "compact" in artifact.name else "full"
    dependencies = collect_markdown_files(
        docs_dir,
        artifact.name,
        handoff_dossier_includes_log(artifact, docs_dir),
        mode,
    )
    manifest = docs_dir / "research-manifest.yaml"
    if manifest.exists():
        dependencies.append(manifest)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in dependencies:
        if not path.exists() or path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def newer_dependencies(artifact: Path, dependencies: list[Path]) -> list[Path]:
    if not artifact.exists():
        return []
    artifact_mtime = artifact.stat().st_mtime
    newer = [path for path in dependencies if path.exists() and path.stat().st_mtime > artifact_mtime]
    newer.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return newer


def summarize_dependency_sample(paths: list[Path], docs_dir: Path, limit: int = 3) -> str:
    return ", ".join(relative_display(path, docs_dir) for path in paths[:limit])


def is_ignored_generated_path(
    path: Path, docs_dir: Path, ignored_generated_paths: set[str] | None
) -> bool:
    if not ignored_generated_paths:
        return False
    return relative_display(path, docs_dir) in ignored_generated_paths


def detect_support_features(docs_dir: Path, manifest: dict[str, str]) -> tuple[bool, bool, bool]:
    data_dir = docs_dir / "data"
    has_support = (docs_dir / "research-manifest.yaml").exists() or data_dir.exists()
    has_archetype = bool(manifest.get("archetype")) or any(
        (docs_dir / name).exists()
        for name in (
            "07-archetype-specific-template.md",
            "08-archetype-metric-baselines.md",
        )
    )
    has_experiments = any(
        path.exists()
        for path in (
            data_dir / "experiment-plan.csv",
            data_dir / "experiment-observations.csv",
            data_dir / "experiments",
        )
    ) or has_support
    return has_support, has_archetype, has_experiments


def audit_core_docs(docs_dir: Path, issues: list[Issue]) -> None:
    for filename, expected_groups in CORE_DOC_REQUIREMENTS.items():
        path = docs_dir / filename
        if not path.exists():
            issues.append(make_issue("error", "missing_required_document", filename=filename))
            continue
        text = read_text(path)
        headings = collect_h2_headings(text)
        for group in expected_groups:
            if not any(candidate in headings for candidate in group):
                issues.append(
                    make_issue(
                        "error",
                        "missing_section_heading",
                        filename=filename,
                        heading=" / ".join(group),
                    )
                )
        blank_count, samples = count_blank_placeholders(text)
        if blank_count:
            sample_text = "; ".join(samples)
            issues.append(
                make_issue(
                    "warning",
                    "blank_scaffold_placeholders",
                    filename=filename,
                    count=str(blank_count),
                    sample=sample_text,
                )
            )


def audit_baseline(docs_dir: Path, manifest: dict[str, str], issues: list[Issue]) -> None:
    manifest_baseline = manifest.get("baseline_version", "")
    if manifest and not is_meaningful(manifest_baseline):
        issues.append(make_issue("error", "missing_manifest_baseline_version"))

    overview_path = docs_dir / "00-overview-and-source-ledger.md"
    if not overview_path.exists():
        return
    overview_text = read_text(overview_path)
    if any(value in overview_text for value in PLACEHOLDER_VALUES if value):
        if "TBD version / region / platform / time slice" in overview_text:
            issues.append(make_issue("error", "default_baseline_placeholder"))


def audit_support_files(docs_dir: Path, has_support: bool, issues: list[Issue]) -> None:
    if not has_support:
        return

    manifest_path = docs_dir / "research-manifest.yaml"
    if not manifest_path.exists():
        issues.append(make_issue("error", "missing_manifest_file"))

    data_dir = docs_dir / "data"
    required_support = [
        "source-ledger.csv",
        "formula-catalog.csv",
        "asset-taxonomy.csv",
        "risk-register.csv",
        "role-coverage.csv",
    ]
    for filename in required_support:
        path = data_dir / filename
        if not path.exists():
            issues.append(
                make_issue(
                    "error", "missing_support_file", path=f"data/{filename}"
                )
            )

    ledger_rows = read_csv_rows(data_dir / "source-ledger.csv")
    if ledger_rows and not count_meaningful_rows(
        ledger_rows, ["title", "url_or_location", "version_or_date", "notes"]
    ):
        issues.append(make_issue("warning", "empty_source_ledger"))

    formula_rows = read_csv_rows(data_dir / "formula-catalog.csv")
    if formula_rows and not count_meaningful_rows(
        formula_rows, ["name", "expression", "variables", "version_scope", "source_ids"]
    ):
        issues.append(make_issue("warning", "empty_formula_catalog"))

    risk_rows = read_csv_rows(data_dir / "risk-register.csv")
    if risk_rows and not count_meaningful_rows(
        risk_rows, ["description", "impact", "likelihood", "mitigation", "validation"]
    ):
        issues.append(make_issue("warning", "empty_risk_register"))


def audit_role_coverage(docs_dir: Path, has_support: bool, issues: list[Issue]) -> None:
    if not has_support:
        return
    rows = read_csv_rows(docs_dir / "data" / "role-coverage.csv")
    if not rows:
        issues.append(make_issue("error", "empty_role_coverage"))
        return

    roles = {row.get("role", "") for row in rows}
    missing_roles = sorted(ROLE_SET - roles)
    if missing_roles:
        issues.append(
            make_issue(
                "error",
                "missing_role_coverage_roles",
                roles=", ".join(missing_roles),
            )
        )

    incomplete_roles = [
        row.get("role", "")
        for row in rows
        if row.get("role", "") in ROLE_SET
        and row.get("status", "").strip().lower() in STATUS_INCOMPLETE
    ]
    if incomplete_roles:
        issues.append(
            make_issue(
                "warning",
                "incomplete_role_coverage",
                count=str(len(incomplete_roles)),
            )
        )


def audit_archetype(
    docs_dir: Path, has_support: bool, has_archetype: bool, issues: list[Issue]
) -> None:
    if not has_archetype:
        return

    for filename in (
        "07-archetype-specific-template.md",
        "08-archetype-metric-baselines.md",
    ):
        if not (docs_dir / filename).exists():
            issues.append(
                make_issue("error", "missing_archetype_doc", filename=filename)
            )

    if not has_support:
        return

    data_dir = docs_dir / "data"
    for filename in (
        "archetype-checklist.csv",
        "archetype-metrics.csv",
        "archetype-metric-links.csv",
    ):
        if not (data_dir / filename).exists():
            issues.append(
                make_issue(
                    "error",
                    "missing_archetype_support_file",
                    path=f"data/{filename}",
                )
            )

    checklist_rows = read_csv_rows(data_dir / "archetype-checklist.csv")
    progressed_checklist = [
        row for row in checklist_rows if row.get("status", "").lower() not in STATUS_INCOMPLETE
    ]
    if checklist_rows and not progressed_checklist:
        issues.append(make_issue("warning", "no_archetype_checklist_progress"))

    metric_rows = read_csv_rows(data_dir / "archetype-metrics.csv")
    populated_metrics = [row for row in metric_rows if is_meaningful(row.get("observed_band", ""))]
    if metric_rows and not populated_metrics:
        issues.append(make_issue("warning", "no_archetype_metric_bands"))


def audit_experiments(
    docs_dir: Path, has_experiments: bool, issues: list[Issue]
) -> None:
    if not has_experiments:
        return

    data_dir = docs_dir / "data"
    experiment_dir = data_dir / "experiments"
    required_paths = [
        docs_dir / "09-experiment-design.md",
        data_dir / "experiment-plan.csv",
        data_dir / "experiment-observations.csv",
    ]
    for path in required_paths:
        if not path.exists():
            relative = path.relative_to(docs_dir)
            issues.append(
                make_issue(
                    "error", "missing_experiment_support_path", path=str(relative)
                )
            )

    summary_candidates = [
        docs_dir / "10-experiment-summary.md",
        docs_dir / "10-experiment-summary-compact.md",
    ]
    if not any(path.exists() for path in summary_candidates):
        issues.append(make_issue("error", "missing_experiment_summary"))

    if not experiment_dir.exists():
        issues.append(
            make_issue(
                "error", "missing_experiment_support_path", path="data/experiments/"
            )
        )
        return

    plan_rows = read_csv_rows(data_dir / "experiment-plan.csv")
    if plan_rows and not [
        row for row in plan_rows if row.get("status", "").strip().lower() not in STATUS_INCOMPLETE
    ]:
        issues.append(make_issue("warning", "no_experiment_plan_progress"))

    registry_rows = read_csv_rows(data_dir / "experiment-observations.csv")
    if registry_rows and not [
        row for row in registry_rows if row.get("status", "").strip().lower() not in STATUS_INCOMPLETE
    ]:
        issues.append(make_issue("warning", "no_experiment_registry_progress"))

    detail_files = sorted(experiment_dir.glob("*.csv"))
    if not detail_files:
        issues.append(make_issue("warning", "empty_experiment_detail_sheets"))
        return

    meaningful_rows = 0
    for path in detail_files:
        rows = read_csv_rows(path)
        meaningful_rows += sum(1 for row in rows if is_meaningful_detail_row(row))
    if meaningful_rows == 0:
        issues.append(make_issue("warning", "no_experiment_raw_samples"))


def audit_generated_artifacts(
    docs_dir: Path,
    has_experiments: bool,
    issues: list[Issue],
    ignored_generated_paths: set[str] | None = None,
) -> None:
    if has_experiments:
        for artifact in (
            docs_dir / "10-experiment-summary.md",
            docs_dir / "10-experiment-summary-compact.md",
        ):
            if not artifact.exists():
                continue
            if is_ignored_generated_path(artifact, docs_dir, ignored_generated_paths):
                continue
            newer = newer_dependencies(artifact, experiment_summary_dependencies(docs_dir))
            if newer:
                issues.append(
                    make_issue(
                        "warning",
                        "stale_experiment_summary",
                        path=relative_display(artifact, docs_dir),
                        count=str(len(newer)),
                        sample=summarize_dependency_sample(newer, docs_dir),
                    )
                )

    evidence_report = docs_dir / "reports" / "evidence-link-audit.md"
    if evidence_report.exists() and not is_ignored_generated_path(
        evidence_report, docs_dir, ignored_generated_paths
    ):
        newer = newer_dependencies(evidence_report, evidence_audit_dependencies(docs_dir))
        if newer:
            issues.append(
                make_issue(
                    "warning",
                    "stale_evidence_link_audit",
                    path=relative_display(evidence_report, docs_dir),
                    count=str(len(newer)),
                    sample=summarize_dependency_sample(newer, docs_dir),
                )
            )

    for artifact in (
        docs_dir / "reports" / "pack-status.md",
        docs_dir / "reports" / "pack-status-compact.md",
    ):
        if not artifact.exists():
            continue
        if is_ignored_generated_path(artifact, docs_dir, ignored_generated_paths):
            continue
        newer = newer_dependencies(artifact, pack_input_dependencies(docs_dir))
        if newer:
            issues.append(
                make_issue(
                    "warning",
                    "stale_status_report",
                    path=relative_display(artifact, docs_dir),
                    count=str(len(newer)),
                    sample=summarize_dependency_sample(newer, docs_dir),
                )
            )

    for artifact in (
        docs_dir / "handoff-full-dossier.md",
        docs_dir / "handoff-compact-dossier.md",
    ):
        if not artifact.exists():
            continue
        if is_ignored_generated_path(artifact, docs_dir, ignored_generated_paths):
            continue
        newer = newer_dependencies(artifact, handoff_dossier_dependencies(docs_dir, artifact))
        if newer:
            issues.append(
                make_issue(
                    "warning",
                    "stale_handoff_dossier",
                    path=relative_display(artifact, docs_dir),
                    count=str(len(newer)),
                    sample=summarize_dependency_sample(newer, docs_dir),
                )
            )

    handoff_manifest = docs_dir / "reports" / "handoff-bundle.md"
    if handoff_manifest.exists() and not is_ignored_generated_path(
        handoff_manifest, docs_dir, ignored_generated_paths
    ):
        newer = newer_dependencies(handoff_manifest, handoff_bundle_dependencies(docs_dir))
        if newer:
            issues.append(
                make_issue(
                    "warning",
                    "stale_handoff_bundle",
                    path=relative_display(handoff_manifest, docs_dir),
                    count=str(len(newer)),
                    sample=summarize_dependency_sample(newer, docs_dir),
                )
            )


def summarize_issues(issues: list[Issue], language: str) -> str:
    labels = AUDIT_LABELS[language]
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    lines = [f"{labels['audit_result']}: {status}", ""]
    lines.append(f"- {labels['errors']}: {len(errors)}")
    lines.append(f"- {labels['warnings']}: {len(warnings)}")

    if errors:
        lines.extend(["", f"{labels['errors']}:"])
        for issue in errors:
            lines.append(f"- {render_issue(issue, language)}")
    else:
        lines.extend(["", f"{labels['errors']}:"])
        lines.append(f"- {labels['none']}")

    if warnings:
        lines.extend(["", f"{labels['warnings']}:"])
        for issue in warnings:
            lines.append(f"- {render_issue(issue, language)}")
    else:
        lines.extend(["", f"{labels['warnings']}:"])
        lines.append(f"- {labels['none']}")

    return "\n".join(lines)


def run_audit(
    docs_dir: Path, ignored_generated_paths: set[str] | None = None
) -> list[Issue]:
    issues: list[Issue] = []
    manifest = parse_manifest(docs_dir / "research-manifest.yaml")
    has_support, has_archetype, has_experiments = detect_support_features(
        docs_dir, manifest
    )

    audit_core_docs(docs_dir, issues)
    audit_baseline(docs_dir, manifest, issues)
    audit_support_files(docs_dir, has_support, issues)
    audit_role_coverage(docs_dir, has_support, issues)
    audit_archetype(docs_dir, has_support, has_archetype, issues)
    audit_experiments(docs_dir, has_experiments, issues)
    audit_generated_artifacts(
        docs_dir, has_experiments, issues, ignored_generated_paths
    )
    return issues


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        raise NotADirectoryError(f"{docs_dir} is not a directory.")

    language = detect_language(docs_dir) if args.language == "auto" else args.language
    issues = run_audit(docs_dir)

    print(summarize_issues(issues, language))

    errors = any(issue.severity == "error" for issue in issues)
    warnings = any(issue.severity == "warning" for issue in issues)
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
