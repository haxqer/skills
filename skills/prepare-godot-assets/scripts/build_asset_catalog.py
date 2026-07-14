#!/usr/bin/env python3
"""Build deterministic indexes for a standalone Godot-ready asset library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from _asset_utils import category_hint, inspect_file, path_tokens


SCHEMA_VERSION = 2
EXCLUDED_SUFFIXES = {".import", ".uid"}
EXCLUDED_NAMES = {"project.godot", ".gdignore"}
ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9_/-]*$")
RIGHTS_STATUSES = {
    "owned",
    "cleared",
    "allowed",
    "public-domain",
    "restricted",
    "unknown",
}
TECHNICAL_STATUSES = {
    "ready",
    "candidate",
    "review",
    "conversion-required",
    "quarantined",
    "unsupported",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "asset_root", type=Path, help="Normalized asset directory to index"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--library-root",
        type=Path,
        help="Portable library root; defaults to the parent of asset_root",
    )
    parser.add_argument(
        "--import-report",
        type=Path,
        help="Optional report from an existing project's Godot import check",
    )
    parser.add_argument(
        "--markdown-limit",
        type=int,
        default=300,
        help="Maximum assets listed in Markdown",
    )
    return parser.parse_args()


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return result or "unnamed"


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_string_list(value: Any, *, allow_empty: bool) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(nonempty_string(item) for item in value)
    )


def load_sidecar(asset: Path) -> dict[str, Any]:
    sidecar = Path(str(asset) + ".asset.json")
    if not sidecar.exists():
        return {}
    try:
        value = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid asset sidecar {sidecar}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Asset sidecar must contain a JSON object: {sidecar}")
    return value


def object_field(sidecar: dict[str, Any], field: str, relative: str) -> dict[str, Any]:
    value = sidecar.get(field, {})
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object for {relative}")
    return value


def validate_optional_string_list(
    value: Any, field: str, relative: str, *, allow_empty: bool = True
) -> None:
    if not valid_string_list(value, allow_empty=allow_empty):
        qualifier = "an array" if allow_empty else "a non-empty array"
        raise ValueError(f"{field} must be {qualifier} of non-empty strings for {relative}")


def merge_tags(relative: str, sidecar: dict[str, Any]) -> list[str]:
    explicit = sidecar.get("tags", [])
    validate_optional_string_list(explicit, "tags", relative)
    return sorted(set(path_tokens(relative) + [slug(tag) for tag in explicit]))


def rights_status(license_data: dict[str, Any], relative: str) -> str:
    status = license_data.get("status", "unknown")
    if not isinstance(status, str) or status not in RIGHTS_STATUSES:
        allowed = ", ".join(sorted(RIGHTS_STATUSES))
        raise ValueError(f"license.status must be one of {allowed} for {relative}")
    return status


def metadata_issues(
    sidecar: dict[str, Any],
    usage: dict[str, Any],
    source: dict[str, Any],
) -> list[str]:
    issues = []
    for field in ("asset_id", "name", "description", "category"):
        if not nonempty_string(sidecar.get(field)):
            issues.append(f"missing:{field}")
    if not valid_string_list(sidecar.get("tags"), allow_empty=False):
        issues.append("missing:tags")
    if not valid_string_list(usage.get("recommended_for"), allow_empty=False):
        issues.append("missing:usage.recommended_for")
    if not nonempty_string(source.get("original_path")):
        issues.append("missing:source.original_path")
    return issues


def compatibility_result(
    import_result: dict[str, Any] | None, godot_version: str | None
) -> dict[str, Any]:
    if not import_result:
        return {"status": "not_tested"}
    import_status = import_result.get("status")
    compatibility_status = {
        "imported": "verified",
        "not-external-import": "not_applicable",
    }.get(import_status, "failed")
    result: dict[str, Any] = {"status": compatibility_status}
    if godot_version:
        result["godot_version"] = godot_version
    if import_status != "imported" and nonempty_string(import_status):
        result["import_status"] = import_status
    return result


def build_record(
    asset: Path,
    asset_root: Path,
    library_root: Path,
    import_results: dict[str, dict[str, Any]],
    godot_version: str | None,
) -> dict[str, Any]:
    relative = asset.relative_to(asset_root).as_posix()
    library_relative = asset.relative_to(library_root).as_posix()
    details = inspect_file(asset)
    sidecar = load_sidecar(asset)
    category = sidecar.get("category") or category_hint(relative, details["media_type"])
    if not isinstance(category, str) or not CATEGORY_RE.fullmatch(category):
        raise ValueError(f"category must be a normalized lowercase path for {relative}")

    identity_seed = f"{relative}\0{details['sha256']}".encode("utf-8")
    fallback_id = (
        f"asset:{slug(str(Path(relative).with_suffix('')))}:"
        f"{hashlib.sha1(identity_seed).hexdigest()[:10]}"
    )
    asset_id = sidecar.get("asset_id", fallback_id)
    if not isinstance(asset_id, str) or not ASSET_ID_RE.fullmatch(asset_id):
        raise ValueError(f"asset_id contains unsupported characters for {relative}")
    name = sidecar.get("name") or asset.stem
    description = sidecar.get("description", "")
    if not nonempty_string(name):
        raise ValueError(f"name must be a non-empty string for {relative}")
    if not isinstance(description, str):
        raise ValueError(f"description must be a string for {relative}")

    license_data = object_field(sidecar, "license", relative)
    source_data = object_field(sidecar, "source", relative)
    usage_data = object_field(sidecar, "usage", relative)
    relationships_data = object_field(sidecar, "relationships", relative)
    import_data = object_field(sidecar, "import", relative)
    validate_optional_string_list(
        usage_data.get("recommended_for", []), "usage.recommended_for", relative
    )
    validate_optional_string_list(usage_data.get("avoid", []), "usage.avoid", relative)

    metadata_problem_list = metadata_issues(sidecar, usage_data, source_data)
    metadata_status = "complete" if not metadata_problem_list else "incomplete"
    import_result = import_results.get(relative) or import_results.get(library_relative)
    compatibility = compatibility_result(import_result, godot_version)

    technical_status = sidecar.get("technical_status")
    if technical_status is None:
        technical_status = {
            "importable": "candidate",
            "conditional": "review",
            "review": "review",
            "convert": "conversion-required",
            "quarantine": "quarantined",
            "unsupported": "unsupported",
        }[details["godot_status"]]
    if not isinstance(technical_status, str) or technical_status not in TECHNICAL_STATUSES:
        allowed = ", ".join(sorted(TECHNICAL_STATUSES))
        raise ValueError(f"technical_status must be one of {allowed} for {relative}")
    if technical_status == "ready" and details["godot_status"] in {
        "quarantine",
        "unsupported",
    }:
        raise ValueError(
            f"Unsafe or unsupported asset cannot be marked ready: {relative}"
        )

    rights = rights_status(license_data, relative)
    issues = sorted(
        set(details["issues"] + [f"metadata:{issue}" for issue in metadata_problem_list])
    )
    ready_for_agent = (
        technical_status == "ready"
        and metadata_status == "complete"
        and rights in {"allowed", "cleared", "owned", "public-domain"}
        and compatibility["status"] != "failed"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "asset_id": asset_id,
        "name": name,
        "description": description,
        "category": category,
        "tags": merge_tags(relative, sidecar),
        "path": relative,
        "library_path": library_relative,
        "media_type": details["media_type"],
        "format": details["detected_format"],
        "sha256": details["sha256"],
        "size_bytes": details["size_bytes"],
        "technical": details["technical"],
        "technical_status": technical_status,
        "metadata_status": metadata_status,
        "metadata_issues": metadata_problem_list,
        "rights_status": rights,
        "godot_compatibility": compatibility,
        "ready_for_agent": ready_for_agent,
        "license": license_data or {"status": "unknown"},
        "source": source_data,
        "usage": usage_data,
        "relationships": relationships_data,
        "import": import_data,
        "issues": issues,
    }


def should_index(path: Path, relative: Path) -> bool:
    if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith(".asset.json"):
        return False
    if any(part.startswith(".") for part in relative.parts):
        return False
    return path.is_file() and not path.is_symlink()


def load_import_report(
    path: Path | None,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    if path is None:
        return {}, None
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid import report {path}: {error}") from error
    if not isinstance(report, dict) or not isinstance(report.get("assets"), list):
        raise ValueError(f"Invalid import report schema: {path}")
    results: dict[str, dict[str, Any]] = {}
    for result in report["assets"]:
        if not isinstance(result, dict) or not isinstance(result.get("path"), str):
            raise ValueError(f"Invalid asset result in import report: {path}")
        results[result["path"]] = result
    version = report.get("godot_version")
    return results, version if isinstance(version, str) else None


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_outputs(
    output_dir: Path, records: list[dict[str, Any]], markdown_limit: int
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "asset_catalog.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")

    categories = Counter(record["category"] for record in records)
    technical = Counter(record["technical_status"] for record in records)
    metadata = Counter(record["metadata_status"] for record in records)
    rights = Counter(record["rights_status"] for record in records)
    compatibility = Counter(
        record["godot_compatibility"]["status"] for record in records
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "asset_count": len(records),
        "ready_for_agent_count": sum(
            bool(record["ready_for_agent"]) for record in records
        ),
        "category_counts": dict(sorted(categories.items())),
        "technical_status_counts": dict(sorted(technical.items())),
        "metadata_status_counts": dict(sorted(metadata.items())),
        "rights_status_counts": dict(sorted(rights.items())),
        "godot_compatibility_counts": dict(sorted(compatibility.items())),
    }
    (output_dir / "asset_catalog.summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Asset Catalog",
        "",
        f"- Assets: {summary['asset_count']}",
        f"- Ready for agent use: {summary['ready_for_agent_count']}",
        f"- Incomplete metadata: {summary['metadata_status_counts'].get('incomplete', 0)}",
        "",
        "## Categories",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {markdown_cell(category)} | {count} |"
        for category, count in summary["category_counts"].items()
    )
    lines.extend(
        [
            "",
            "## Assets",
            "",
            "| ID | Asset | Recommended use | Category | Status | Metadata | Rights | Library path |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records[: max(0, markdown_limit)]:
        recommended = record["usage"].get("recommended_for", [])
        purpose = "; ".join(recommended) or record["description"] or "Metadata required"
        asset_summary = record["name"]
        if record["description"]:
            asset_summary += f": {record['description']}"
        lines.append(
            f"| `{markdown_cell(record['asset_id'])}` | {markdown_cell(asset_summary)} | "
            f"{markdown_cell(purpose)} | "
            f"{markdown_cell(record['category'])} | {record['technical_status']} | "
            f"{record['metadata_status']} | {record['rights_status']} | "
            f"`{markdown_cell(record['library_path'])}` |"
        )
    if len(records) > markdown_limit:
        lines.extend(
            [
                "",
                f"Showing {markdown_limit} of {len(records)} assets. Query `asset_catalog.jsonl` for the full catalog.",
            ]
        )
    lines.append("")
    (output_dir / "ASSET_CATALOG.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    asset_root = args.asset_root.resolve()
    library_root = (
        args.library_root.resolve() if args.library_root else asset_root.parent
    )
    output_dir = args.output_dir.resolve()
    if not asset_root.is_dir():
        raise SystemExit(f"Asset root does not exist: {asset_root}")
    if not library_root.is_dir():
        raise SystemExit(f"Library root does not exist: {library_root}")
    try:
        asset_root.relative_to(library_root)
    except ValueError as error:
        raise SystemExit("Asset root must stay within the library root") from error

    try:
        import_results, godot_version = load_import_report(args.import_report)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    assets = sorted(
        path
        for path in asset_root.rglob("*")
        if should_index(path, path.relative_to(asset_root))
        and output_dir not in path.parents
    )
    try:
        records = [
            build_record(
                asset,
                asset_root,
                library_root,
                import_results,
                godot_version,
            )
            for asset in assets
        ]
    except ValueError as error:
        raise SystemExit(str(error)) from error
    ids = Counter(record["asset_id"] for record in records)
    duplicates = sorted(asset_id for asset_id, count in ids.items() if count > 1)
    if duplicates:
        raise SystemExit("Duplicate asset_id values: " + ", ".join(duplicates))
    write_outputs(output_dir, records, args.markdown_limit)
    print(
        json.dumps(
            {
                "catalog": str(output_dir / "asset_catalog.jsonl"),
                "assets": len(records),
                "ready_for_agent": sum(
                    bool(record["ready_for_agent"]) for record in records
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
