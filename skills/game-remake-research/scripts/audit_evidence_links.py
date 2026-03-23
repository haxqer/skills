#!/usr/bin/env python3
"""Audit source-ledger link integrity across remake research support files."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from audit_remake_pack import (
    detect_language,
    is_meaningful,
    read_csv_rows,
)


SPLIT_PATTERN = re.compile(r"[;,|]")
CITATION_PATTERN = re.compile(r"\bS(?:-\d+|\d+)\b")
SECTION_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
PLACEHOLDER_BULLET_PATTERN = re.compile(r"^[-*+]\s+[^:]+:\s*$")
PLACEHOLDER_NUMBERED_PATTERN = re.compile(r"^\d+\.\s+[^:]+:\s*$")
TABLE_DIVIDER_PATTERN = re.compile(r"^\|?[-: ]+\|(?:[-: ]+\|)+$")
EVIDENCE_SECTION_NAMES = {
    "confirmed facts": "Confirmed Facts",
    "inferred model": "Inferred Model",
}
LABELS = {
    "en": {
        "title": "{game} Evidence Link Audit",
        "status": "Audit status",
        "snapshot": "Snapshot",
        "ledger_ids": "Ledger IDs",
        "referenced_ids": "Referenced IDs",
        "unknown_ids": "Unknown IDs",
        "unused_ids": "Unused ledger IDs",
        "blank_refs": "Rows missing source refs",
        "duplicates": "Duplicate ledger IDs",
        "missing_files": "Missing structured files",
        "markdown_docs": "Markdown docs scanned",
        "docs_without_citations": "Docs with uncited evidence sections",
        "findings": "Findings",
        "unknown_section": "Unknown Source IDs",
        "unused_section": "Unused Ledger IDs",
        "blank_section": "Blank Source References",
        "duplicate_section": "Duplicate Ledger IDs",
        "missing_section": "Missing Files",
        "doc_section": "Evidence Sections Missing Inline Citations",
        "no_items": "None.",
        "headers_unknown": ("Source ID", "References"),
        "headers_unused": ("Source ID", "Source type", "Title"),
        "headers_blank": ("Location", "Row", "Field"),
        "headers_missing": ("Path",),
        "headers_duplicate": ("Source ID", "Count"),
        "headers_docs": ("Document", "Sections missing citations"),
        "fail_unknown": "Unknown source IDs must be added to data/source-ledger.csv or removed from references.",
        "warn_unused": "Unused ledger IDs usually indicate stale ledger entries or sources that were never cited.",
        "warn_blank": "Blank source references mean the row contains research data without a traceable source.",
        "warn_docs": "These docs contain evidence-section content, but the section text has no inline ledger citations.",
        "summary": "Evidence audit result: {status} | ledger={ledger} referenced={referenced} unknown={unknown} unused={unused} blank={blank} duplicates={duplicates} doc_gaps={doc_gaps}",
    },
}


@dataclass
class BlankReference:
    location: str
    row: str
    field: str


@dataclass
class EvidenceAuditResult:
    status: str
    ledger_ids: dict[str, dict[str, str]]
    duplicate_ids: dict[str, int]
    references: dict[str, list[str]]
    unknown_ids: dict[str, list[str]]
    unused_ids: list[str]
    blank_references: list[BlankReference]
    docs_without_citations: list[tuple[str, str]]
    markdown_docs_scanned: int
    missing_files: list[str]
    language: str


EVIDENCE_PRIORITY_ORDER = (
    ("blocker", "duplicate_ids"),
    ("blocker", "unknown_ids"),
    ("high", "blank_references"),
    ("medium", "docs_without_citations"),
    ("low", "unused_ids"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit source-ledger link integrity across research-pack files."
    )
    parser.add_argument("--docs-dir", required=True, help="Research pack directory.")
    parser.add_argument(
        "--output",
        help="Optional markdown output path. Relative paths are resolved inside docs-dir.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "en"),
        default="auto",
        help="Output language. Defaults to auto, which currently resolves to en.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when warnings are present.",
    )
    return parser.parse_args()


def evidence_issue_counts(result: EvidenceAuditResult) -> list[tuple[str, str, int]]:
    counts = {
        "duplicate_ids": len(result.duplicate_ids),
        "unknown_ids": len(result.unknown_ids),
        "blank_references": len(result.blank_references),
        "docs_without_citations": len(result.docs_without_citations),
        "unused_ids": len(result.unused_ids),
    }
    findings: list[tuple[str, str, int]] = []
    for priority, key in EVIDENCE_PRIORITY_ORDER:
        count = counts[key]
        if count:
            findings.append((priority, key, count))
    return findings


def highest_evidence_priority(result: EvidenceAuditResult) -> str:
    findings = evidence_issue_counts(result)
    if not findings:
        return "none"
    return findings[0][0]


def split_source_ids(value: str) -> list[str]:
    if not value:
        return []
    parts = [part.strip() for part in SPLIT_PATTERN.split(value) if part.strip()]
    return parts


def row_has_payload(row: dict[str, str], ignore_fields: set[str]) -> bool:
    for key, value in row.items():
        if key in ignore_fields:
            continue
        if is_meaningful(value):
            return True
    return False


def row_has_payload_in_fields(row: dict[str, str], fields: list[str]) -> bool:
    return any(is_meaningful(row.get(field, "")) for field in fields)


def row_label(row: dict[str, str], fallback_index: int) -> str:
    for key in (
        "sample_id",
        "task_id",
        "band_id",
        "step_id",
        "formula_id",
        "asset_id",
        "metric_id",
        "risk_id",
        "experiment_id",
        "role",
    ):
        value = row.get(key, "").strip()
        if value:
            return value
    return f"row-{fallback_index}"


def add_multi_source_refs(
    rows: list[dict[str, str]],
    field: str,
    location: str,
    payload_fields: list[str],
    references: dict[str, list[str]],
    blank_refs: list[BlankReference],
) -> None:
    for index, row in enumerate(rows, start=2):
        label = row_label(row, index)
        values = split_source_ids(row.get(field, ""))
        if values:
            for source_id in values:
                references[source_id].append(f"{location}:{label}")
        elif row_has_payload_in_fields(row, payload_fields):
            blank_refs.append(BlankReference(location, label, field))


def add_single_source_refs(
    rows: list[dict[str, str]],
    field: str,
    location: str,
    references: dict[str, list[str]],
    blank_refs: list[BlankReference],
) -> None:
    ignored_fields = {
        field,
        "notes",
        "confidence",
        "experiment_id",
        "sample_id",
        "task_id",
        "band_id",
        "step_id",
        "state_index",
    }
    for index, row in enumerate(rows, start=2):
        label = row_label(row, index)
        source_id = row.get(field, "").strip()
        if source_id:
            references[source_id].append(f"{location}:{label}")
        elif row_has_payload(row, ignored_fields):
            blank_refs.append(BlankReference(location, label, field))


def parse_research_log(
    path: Path, references: dict[str, list[str]], blank_refs: list[BlankReference]
) -> None:
    if not path.exists():
        return
    in_table = False
    data_rows = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("| Date | Source ID |"):
            in_table = True
            data_rows = 0
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            if data_rows > 0:
                break
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        if all(re.fullmatch(r"[-: ]*", cell) for cell in cells):
            continue
        data_rows += 1
        source_id = cells[1]
        location = "99-research-log.md"
        row = cells[0] or f"row-{data_rows}"
        payload = any(cell for idx, cell in enumerate(cells) if idx != 1)
        if source_id:
            references[source_id].append(f"{location}:{row}")
        elif payload:
            blank_refs.append(BlankReference(location, row, "Source ID"))


def expected_markdown_docs(docs_dir: Path) -> list[Path]:
    docs: list[Path] = []
    for path in sorted(docs_dir.glob("[0-9][0-9]-*.md")):
        if path.name.startswith("00-") or path.name.startswith("99-"):
            continue
        docs.append(path)
    return docs


def normalize_heading(value: str) -> str:
    return value.strip().lower()


def split_h2_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        match = SECTION_HEADING_PATTERN.match(stripped)
        if match:
            if current_heading is not None:
                sections[current_heading] = current_lines[:]
            current_heading = match.group(1).strip()
            current_lines = []
            continue
        if current_heading is not None:
            current_lines.append(raw_line)

    if current_heading is not None:
        sections[current_heading] = current_lines

    return {
        heading: "\n".join(lines).strip()
        for heading, lines in sections.items()
    }


def line_has_meaningful_markdown_content(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("<!--") and stripped.endswith("-->"):
        return False
    if TABLE_DIVIDER_PATTERN.fullmatch(stripped):
        return False
    if re.fullmatch(r"[-*_`#> ]+", stripped):
        return False
    if PLACEHOLDER_BULLET_PATTERN.fullmatch(stripped):
        return False
    if PLACEHOLDER_NUMBERED_PATTERN.fullmatch(stripped):
        return False
    return is_meaningful(stripped)


def section_has_meaningful_content(text: str) -> bool:
    return any(
        line_has_meaningful_markdown_content(line) for line in text.splitlines()
    )


def uncited_evidence_sections(text: str) -> list[str]:
    sections = split_h2_sections(text)
    indexed_sections = {
        normalize_heading(heading): content
        for heading, content in sections.items()
    }
    missing: list[str] = []
    for heading_key, display_name in EVIDENCE_SECTION_NAMES.items():
        content = indexed_sections.get(heading_key, "")
        if not section_has_meaningful_content(content):
            continue
        if not CITATION_PATTERN.search(content):
            missing.append(display_name)
    return list(dict.fromkeys(missing))


def scan_markdown_docs(
    docs_dir: Path, references: dict[str, list[str]]
) -> tuple[list[tuple[str, str]], int]:
    docs_without_citations: list[tuple[str, str]] = []
    scanned = 0
    for path in expected_markdown_docs(docs_dir):
        text = path.read_text(encoding="utf-8")
        found = sorted(set(CITATION_PATTERN.findall(text)))
        scanned += 1
        if found:
            for source_id in found:
                references[source_id].append(f"{path.name}:markdown")
        missing_sections = uncited_evidence_sections(text)
        if missing_sections:
            docs_without_citations.append(
                (path.name, ", ".join(missing_sections))
            )
    return docs_without_citations, scanned


def collect_ledger(docs_dir: Path) -> tuple[dict[str, dict[str, str]], dict[str, int], list[str]]:
    ledger_path = docs_dir / "data" / "source-ledger.csv"
    if not ledger_path.exists():
        return {}, {}, ["data/source-ledger.csv"]
    rows = read_csv_rows(ledger_path)
    ledger_ids: dict[str, dict[str, str]] = {}
    duplicates: dict[str, int] = defaultdict(int)
    for row in rows:
        source_id = row.get("source_id", "").strip()
        if not source_id:
            continue
        duplicates[source_id] += 1
        if source_id not in ledger_ids:
            ledger_ids[source_id] = row
    duplicate_ids = {source_id: count for source_id, count in duplicates.items() if count > 1}
    return ledger_ids, duplicate_ids, []


def run_evidence_audit(docs_dir: Path, language: str) -> EvidenceAuditResult:
    ledger_ids, duplicate_ids, missing_files = collect_ledger(docs_dir)
    references: dict[str, list[str]] = defaultdict(list)
    blank_refs: list[BlankReference] = []

    data_dir = docs_dir / "data"
    structured_multi = [
        (
            "data/formula-catalog.csv",
            "source_ids",
            ["name", "expression", "variables", "units", "version_scope", "notes"],
        ),
        (
            "data/asset-taxonomy.csv",
            "source_ids",
            ["subtype", "reusable_or_bespoke", "priority", "notes"],
        ),
        (
            "data/archetype-metrics.csv",
            "source_ids",
            ["observed_band", "target_band", "notes"],
        ),
    ]
    for relative_path, field, payload_fields in structured_multi:
        path = docs_dir / relative_path
        if not path.exists():
            continue
        add_multi_source_refs(
            read_csv_rows(path),
            field,
            relative_path,
            payload_fields,
            references,
            blank_refs,
        )

    experiment_dir = data_dir / "experiments"
    if experiment_dir.exists():
        for path in sorted(experiment_dir.glob("*.csv")):
            add_single_source_refs(
                read_csv_rows(path),
                "source_id",
                str(path.relative_to(docs_dir)),
                references,
                blank_refs,
            )

    parse_research_log(docs_dir / "99-research-log.md", references, blank_refs)
    docs_without_citations, markdown_docs_scanned = scan_markdown_docs(
        docs_dir, references
    )

    reference_ids = sorted(references)
    unknown_ids = {
        source_id: locations
        for source_id, locations in references.items()
        if source_id not in ledger_ids
    }
    unused_ids = sorted(source_id for source_id in ledger_ids if source_id not in references)

    if missing_files or duplicate_ids or unknown_ids:
        status = "FAIL"
    elif unused_ids or blank_refs or docs_without_citations or not references:
        status = "WARN"
    else:
        status = "PASS"

    return EvidenceAuditResult(
        status=status,
        ledger_ids=ledger_ids,
        duplicate_ids=duplicate_ids,
        references=dict(references),
        unknown_ids=unknown_ids,
        unused_ids=unused_ids,
        blank_references=blank_refs,
        docs_without_citations=docs_without_citations,
        markdown_docs_scanned=markdown_docs_scanned,
        missing_files=missing_files,
        language=language,
    )


def build_markdown(result: EvidenceAuditResult, docs_dir: Path) -> str:
    label = LABELS[result.language]
    manifest = {}
    manifest_path = docs_dir / "research-manifest.yaml"
    if manifest_path.exists():
        for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
            if raw_line.startswith("game:"):
                manifest["game"] = raw_line.split(":", 1)[1].strip().strip('"')
                break
    game = manifest.get("game", docs_dir.name)

    lines = [f"# {label['title'].format(game=game)}", ""]
    lines.extend(
        [
            f"## {label['snapshot']}",
            "",
            f"- {label['status']}: `{result.status}`",
            f"- {label['ledger_ids']}: `{len(result.ledger_ids)}`",
            f"- {label['referenced_ids']}: `{len(result.references)}`",
            f"- {label['unknown_ids']}: `{len(result.unknown_ids)}`",
            f"- {label['unused_ids']}: `{len(result.unused_ids)}`",
            f"- {label['blank_refs']}: `{len(result.blank_references)}`",
            f"- {label['duplicates']}: `{len(result.duplicate_ids)}`",
            f"- {label['markdown_docs']}: `{result.markdown_docs_scanned}`",
            f"- {label['docs_without_citations']}: `{len(result.docs_without_citations)}`",
            f"- {label['missing_files']}: `{len(result.missing_files)}`",
        ]
    )

    lines.extend(["", f"## {label['findings']}", ""])

    headers = label["headers_unknown"]
    lines.extend(["", f"### {label['unknown_section']}", ""])
    if result.unknown_ids:
        lines.append(f"- {label['fail_unknown']}")
        lines.extend([
            "",
            f"| {headers[0]} | {headers[1]} |",
            "| --- | --- |",
        ])
        for source_id, locations in sorted(result.unknown_ids.items()):
            lines.append(f"| {source_id} | {'; '.join(locations)} |")
    else:
        lines.append(f"- {label['no_items']}")

    headers = label["headers_duplicate"]
    lines.extend(["", f"### {label['duplicate_section']}", ""])
    if result.duplicate_ids:
        lines.extend([
            "",
            f"| {headers[0]} | {headers[1]} |",
            "| --- | --- |",
        ])
        for source_id, count in sorted(result.duplicate_ids.items()):
            lines.append(f"| {source_id} | {count} |")
    else:
        lines.append(f"- {label['no_items']}")

    headers = label["headers_unused"]
    lines.extend(["", f"### {label['unused_section']}", ""])
    if result.unused_ids:
        lines.append(f"- {label['warn_unused']}")
        lines.extend([
            "",
            f"| {headers[0]} | {headers[1]} | {headers[2]} |",
            "| --- | --- | --- |",
        ])
        for source_id in result.unused_ids:
            row = result.ledger_ids.get(source_id, {})
            lines.append(
                f"| {source_id} | {row.get('source_type','')} | {row.get('title','')} |"
            )
    else:
        lines.append(f"- {label['no_items']}")

    headers = label["headers_blank"]
    lines.extend(["", f"### {label['blank_section']}", ""])
    if result.blank_references:
        lines.append(f"- {label['warn_blank']}")
        lines.extend([
            "",
            f"| {headers[0]} | {headers[1]} | {headers[2]} |",
            "| --- | --- | --- |",
        ])
        for item in result.blank_references:
            lines.append(f"| {item.location} | {item.row} | {item.field} |")
    else:
        lines.append(f"- {label['no_items']}")

    headers = label["headers_docs"]
    lines.extend(["", f"### {label['doc_section']}", ""])
    if result.docs_without_citations:
        lines.append(f"- {label['warn_docs']}")
        lines.extend([
            "",
            f"| {headers[0]} | {headers[1]} |",
            "| --- | --- |",
        ])
        for filename, sections in result.docs_without_citations:
            lines.append(f"| {filename} | {sections} |")
    else:
        lines.append(f"- {label['no_items']}")

    headers = label["headers_missing"]
    lines.extend(["", f"### {label['missing_section']}", ""])
    if result.missing_files:
        lines.extend([
            "",
            f"| {headers[0]} |",
            "| --- |",
        ])
        for path in result.missing_files:
            lines.append(f"| {path} |")
    else:
        lines.append(f"- {label['no_items']}")

    return "\n".join(lines).rstrip() + "\n"


def render_summary(result: EvidenceAuditResult) -> str:
    label = LABELS[result.language]
    return label["summary"].format(
        status=result.status,
        ledger=len(result.ledger_ids),
        referenced=len(result.references),
        unknown=len(result.unknown_ids),
        unused=len(result.unused_ids),
        blank=len(result.blank_references),
        duplicates=len(result.duplicate_ids),
        doc_gaps=len(result.docs_without_citations),
    )


def resolve_output_path(docs_dir: Path, output: str | None) -> Path | None:
    if not output:
        return None
    path = Path(output)
    if not path.is_absolute():
        path = docs_dir / path
    return path


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir).expanduser().resolve()
    if not docs_dir.is_dir():
        raise NotADirectoryError(f"{docs_dir} is not a directory.")

    language = detect_language(docs_dir) if args.language == "auto" else args.language
    result = run_evidence_audit(docs_dir, language)
    print(render_summary(result))

    output_path = resolve_output_path(docs_dir, args.output)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_markdown(result, docs_dir), encoding="utf-8")
        print(f"Wrote evidence audit report to {output_path}")

    has_fail = result.status == "FAIL"
    has_warn = result.status == "WARN"
    if has_fail or (args.strict and has_warn):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
