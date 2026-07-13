#!/usr/bin/env python3
"""Build a deterministic JSONL catalog for a normalized Godot asset tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from _asset_utils import category_hint, inspect_file, path_tokens


EXCLUDED_SUFFIXES = {".import", ".uid"}
EXCLUDED_NAMES = {"project.godot", ".gdignore"}
ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9_/-]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "asset_root", type=Path, help="Normalized asset directory to index"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Godot project root used to calculate res:// paths",
    )
    parser.add_argument(
        "--import-report", type=Path, help="Report produced by verify_godot_import.py"
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


def merge_tags(relative: str, sidecar: dict[str, Any]) -> list[str]:
    explicit = sidecar.get("tags", [])
    if not isinstance(explicit, list) or any(
        not isinstance(tag, str) for tag in explicit
    ):
        raise ValueError(f"tags must be an array of strings for {relative}")
    return sorted(set(path_tokens(relative) + [slug(tag) for tag in explicit]))


def object_field(sidecar: dict[str, Any], field: str, relative: str) -> dict[str, Any]:
    value = sidecar.get(field, {})
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object for {relative}")
    return value


def rights_status(license_data: dict[str, Any], relative: str) -> str:
    status = license_data.get("status", "unknown")
    allowed = {
        "owned",
        "cleared",
        "allowed",
        "public-domain",
        "restricted",
        "unknown",
    }
    if status not in allowed:
        raise ValueError(
            f"license.status must be one of {', '.join(sorted(allowed))} for {relative}"
        )
    return status


def build_record(
    asset: Path,
    asset_root: Path,
    project_root: Path | None,
    import_results: dict[str, dict[str, Any]],
    godot_version: str | None,
) -> dict[str, Any]:
    relative = asset.relative_to(asset_root).as_posix()
    details = inspect_file(asset)
    sidecar = load_sidecar(asset)
    category = sidecar.get("category") or category_hint(relative, details["media_type"])
    if not isinstance(category, str) or not CATEGORY_RE.fullmatch(category):
        raise ValueError(f"category must be a normalized lowercase path for {relative}")
    if project_root:
        try:
            resource_relative = asset.relative_to(project_root).as_posix()
        except ValueError as error:
            raise ValueError(f"Asset is outside project root: {asset}") from error
    else:
        resource_relative = relative

    identity_seed = f"{relative}\0{details['sha256']}".encode("utf-8")
    fallback_id = f"asset:{slug(str(Path(relative).with_suffix('')))}:{hashlib.sha1(identity_seed).hexdigest()[:10]}"
    asset_id = sidecar.get("asset_id", fallback_id)
    if not isinstance(asset_id, str) or not ASSET_ID_RE.fullmatch(asset_id):
        raise ValueError(f"asset_id contains unsupported characters for {relative}")
    name = sidecar.get("name") or asset.stem
    description = sidecar.get("description", "")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"name must be a non-empty string for {relative}")
    if not isinstance(description, str):
        raise ValueError(f"description must be a string for {relative}")
    license_data = object_field(sidecar, "license", relative)
    source_data = object_field(sidecar, "source", relative)
    usage_data = object_field(sidecar, "usage", relative)
    relationships_data = object_field(sidecar, "relationships", relative)
    import_data = object_field(sidecar, "import", relative)
    import_result = import_results.get(relative)
    technical_status = sidecar.get("technical_status")
    if technical_status is None:
        if import_result and import_result.get("status") == "imported":
            technical_status = "ready"
        else:
            technical_status = {
                "importable": "candidate",
                "conditional": "review",
                "review": "review",
                "convert": "conversion-required",
                "quarantine": "quarantined",
                "unsupported": "unsupported",
            }[details["godot_status"]]
    if not isinstance(technical_status, str):
        raise ValueError(f"technical_status must be a string for {relative}")
    if (
        technical_status == "ready"
        and details["godot_status"] in {"importable", "conditional"}
        and (not import_result or import_result.get("status") != "imported")
    ):
        raise ValueError(
            f"External asset cannot be ready without a successful Godot import result: {relative}"
        )
    rights = rights_status(license_data, relative)

    record = {
        "schema_version": 1,
        "asset_id": asset_id,
        "name": name,
        "description": description,
        "category": category,
        "tags": merge_tags(relative, sidecar),
        "path": relative,
        "res_path": f"res://{resource_relative}",
        "media_type": details["media_type"],
        "format": details["detected_format"],
        "sha256": details["sha256"],
        "size_bytes": details["size_bytes"],
        "technical": details["technical"],
        "technical_status": technical_status,
        "rights_status": rights,
        "ready_for_agent": technical_status == "ready"
        and rights in {"allowed", "cleared", "owned", "public-domain"},
        "license": license_data or {"status": "unknown"},
        "source": source_data,
        "usage": usage_data,
        "relationships": relationships_data,
        "import": {
            **import_data,
            **(
                {"verification_status": import_result.get("status")}
                if import_result
                else {}
            ),
            **({"godot_version": godot_version} if godot_version else {}),
        },
        "issues": details["issues"],
    }
    return record


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
    rights = Counter(record["rights_status"] for record in records)
    summary = {
        "schema_version": 1,
        "asset_count": len(records),
        "ready_for_agent_count": sum(
            bool(record["ready_for_agent"]) for record in records
        ),
        "category_counts": dict(sorted(categories.items())),
        "technical_status_counts": dict(sorted(technical.items())),
        "rights_status_counts": dict(sorted(rights.items())),
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
        "",
        "## Categories",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {category} | {count} |"
        for category, count in summary["category_counts"].items()
    )
    lines.extend(
        [
            "",
            "## Assets",
            "",
            "| ID | Category | Status | Rights | Resource |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for record in records[: max(0, markdown_limit)]:
        lines.append(
            f"| `{record['asset_id']}` | {record['category']} | {record['technical_status']} | "
            f"{record['rights_status']} | `{record['res_path']}` |"
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
    project_root = args.project_root.resolve() if args.project_root else None
    output_dir = args.output_dir.resolve()
    if not asset_root.is_dir():
        raise SystemExit(f"Asset root does not exist: {asset_root}")
    if project_root and not (project_root / "project.godot").is_file():
        raise SystemExit(f"Not a Godot project root: {project_root}")

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
            build_record(asset, asset_root, project_root, import_results, godot_version)
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
