#!/usr/bin/env python3
"""Audit an untrusted asset dump without modifying the source tree."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _asset_utils import category_hint, inspect_file, path_tokens


SCHEMA_VERSION = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Asset dump to inspect recursively")
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="Directory for audit artifacts"
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories",
    )
    return parser.parse_args()


def is_hidden(relative: Path) -> bool:
    return any(part.startswith(".") for part in relative.parts)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def scan(source: Path, output_dir: Path, include_hidden: bool) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root, directories, files in os.walk(source, followlinks=False):
        root_path = Path(root)
        retained_directories = []
        for name in sorted(directories):
            path = root_path / name
            relative = path.relative_to(source)
            if not include_hidden and is_hidden(relative):
                continue
            if path.is_symlink():
                records.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "path": relative.as_posix(),
                        "name": path.name,
                        "media_type": "unknown",
                        "godot_status": "quarantine",
                        "recommended_action": "do-not-follow-symlink",
                        "size_bytes": None,
                        "sha256": None,
                        "technical": {"entry_type": "directory-symlink"},
                        "issues": ["symlink"],
                        "category_hint": "unclassified/unknown",
                        "tag_hints": path_tokens(relative.as_posix()),
                    }
                )
                continue
            if is_within(path.resolve(), output_dir):
                continue
            retained_directories.append(name)
        directories[:] = retained_directories
        for name in sorted(files):
            path = root_path / name
            relative = path.relative_to(source)
            if not include_hidden and is_hidden(relative):
                continue
            base = {
                "schema_version": SCHEMA_VERSION,
                "path": relative.as_posix(),
                "name": path.name,
            }
            if path.is_symlink():
                base.update(
                    {
                        "media_type": "unknown",
                        "godot_status": "quarantine",
                        "recommended_action": "do-not-follow-symlink",
                        "size_bytes": None,
                        "sha256": None,
                        "technical": {},
                        "issues": ["symlink"],
                        "category_hint": "unclassified/unknown",
                        "tag_hints": path_tokens(relative.as_posix()),
                    }
                )
                records.append(base)
                continue
            try:
                details = inspect_file(path)
            except (OSError, PermissionError) as error:
                base.update(
                    {
                        "media_type": "unknown",
                        "godot_status": "quarantine",
                        "recommended_action": "fix-read-permission-or-reject",
                        "size_bytes": None,
                        "sha256": None,
                        "technical": {},
                        "issues": [f"read-failed:{type(error).__name__}"],
                        "category_hint": "unclassified/unknown",
                        "tag_hints": path_tokens(relative.as_posix()),
                    }
                )
                records.append(base)
                continue
            base.update(details)
            base["category_hint"] = category_hint(
                relative.as_posix(), details["media_type"]
            )
            base["tag_hints"] = path_tokens(relative.as_posix())
            records.append(base)
    return records


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(record["godot_status"] for record in records)
    media_types = Counter(record["media_type"] for record in records)
    formats = Counter(record.get("detected_format") or "unknown" for record in records)
    issue_counts = Counter(
        issue.split(":", 1)[0] for record in records for issue in record["issues"]
    )
    duplicate_map: dict[str, list[str]] = defaultdict(list)
    for record in records:
        if record.get("sha256"):
            duplicate_map[record["sha256"]].append(record["path"])
    duplicate_groups = [
        {"sha256": digest, "paths": sorted(paths), "count": len(paths)}
        for digest, paths in sorted(duplicate_map.items())
        if len(paths) > 1
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "total_files": len(records),
        "total_bytes": sum(record.get("size_bytes") or 0 for record in records),
        "status_counts": dict(sorted(statuses.items())),
        "media_type_counts": dict(sorted(media_types.items())),
        "format_counts": dict(sorted(formats.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "duplicate_groups": duplicate_groups,
        "duplicate_file_count": sum(group["count"] for group in duplicate_groups),
    }


def write_outputs(
    output_dir: Path, records: list[dict[str, Any]], summary: dict[str, Any]
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = output_dir / "inventory.jsonl"
    with inventory_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
    (output_dir / "audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Asset Audit",
        "",
        f"- Files: {summary['total_files']}",
        f"- Bytes: {summary['total_bytes']}",
        f"- Exact duplicate groups: {len(summary['duplicate_groups'])}",
        "",
        "## Godot Triage",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {status} | {count} |" for status, count in summary["status_counts"].items()
    )
    lines.extend(["", "## Issues", "", "| Issue | Count |", "| --- | ---: |"])
    lines.extend(
        f"| {issue} | {count} |" for issue, count in summary["issue_counts"].items()
    )
    lines.extend(["", "## Exact Duplicates", ""])
    if summary["duplicate_groups"]:
        for group in summary["duplicate_groups"]:
            lines.append(
                f"- `{group['sha256'][:12]}`: "
                + ", ".join(f"`{path}`" for path in group["paths"])
            )
    else:
        lines.append("No exact duplicates found.")
    lines.append("")
    (output_dir / "AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output_dir = args.output_dir.resolve()
    if not source.is_dir():
        raise SystemExit(f"Source directory does not exist: {source}")
    records = scan(source, output_dir, args.include_hidden)
    summary = build_summary(records)
    write_outputs(output_dir, records, summary)
    print(
        json.dumps(
            {
                "inventory": str(output_dir / "inventory.jsonl"),
                "summary": str(output_dir / "audit_summary.json"),
                "files": len(records),
                "statuses": summary["status_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
