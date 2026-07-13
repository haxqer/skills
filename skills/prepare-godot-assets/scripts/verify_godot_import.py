#!/usr/bin/env python3
"""Run the target Godot importer and report asset-level import results."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from _asset_utils import GODOT_CONDITIONAL, GODOT_IMPORTABLE, inspect_file


ERROR_RE = re.compile(
    r"(?:^|\s)(?:ERROR|SCRIPT ERROR):|error importing|failed (?:loading|to load|to import)|cannot open",
    re.IGNORECASE,
)
WARNING_RE = re.compile(r"(?:^|\s)WARNING:", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--asset-root",
        type=Path,
        default=Path("assets"),
        help="Project-relative asset directory",
    )
    parser.add_argument("--godot", help="Godot executable name or path")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    return parser.parse_args()


def resolve_godot(value: str | None) -> str:
    candidates = [value] if value else []
    candidates.extend(
        ["godot", "godot4", "/Applications/Godot.app/Contents/MacOS/Godot"]
    )
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path.resolve())
    raise ValueError("Godot executable not found; pass --godot or add Godot 4 to PATH")


def import_state(asset: Path, asset_root: Path) -> dict[str, Any]:
    relative = asset.relative_to(asset_root).as_posix()
    try:
        details = inspect_file(asset)
    except OSError as error:
        return {"path": relative, "status": "read-failed", "error": str(error)}
    asset_format = details["detected_format"]
    result = {
        "path": relative,
        "format": asset_format,
        "godot_status": details["godot_status"],
    }
    if asset_format not in GODOT_IMPORTABLE | GODOT_CONDITIONAL:
        result["status"] = "not-external-import"
        return result
    sidecar = Path(str(asset) + ".import")
    if not sidecar.is_file():
        result["status"] = "missing-import-sidecar"
        return result
    try:
        content = sidecar.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        result.update({"status": "sidecar-read-failed", "error": str(error)})
        return result
    if re.search(r"(?m)^valid\s*=\s*false\s*$", content):
        result["status"] = "invalid-import"
    else:
        result["status"] = "imported"
    return result


def should_check(path: Path, relative: Path, output_dir: Path) -> bool:
    if output_dir in path.parents:
        return False
    if any(part.startswith(".") for part in relative.parts):
        return False
    if path.name.endswith((".asset.json", ".import", ".uid")):
        return False
    return path.is_file() and not path.is_symlink()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()
    if not (project_root / "project.godot").is_file():
        raise SystemExit(f"Not a Godot project root: {project_root}")
    asset_root = (project_root / args.asset_root).resolve()
    try:
        asset_root.relative_to(project_root)
    except ValueError as error:
        raise SystemExit("--asset-root must stay within the project root") from error
    if not asset_root.is_dir():
        raise SystemExit(f"Asset root does not exist: {asset_root}")
    try:
        godot = resolve_godot(args.godot)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        version_result = subprocess.run(
            [godot, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        import_result = subprocess.run(
            [godot, "--headless", "--path", str(project_root), "--import"],
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SystemExit(f"Godot import exceeded {args.timeout} seconds") from error
    log = (import_result.stdout or "") + (import_result.stderr or "")
    (output_dir / "godot-import.log").write_text(log, encoding="utf-8")
    error_lines = [line for line in log.splitlines() if ERROR_RE.search(line)]
    warning_lines = [line for line in log.splitlines() if WARNING_RE.search(line)]

    assets = sorted(
        path
        for path in asset_root.rglob("*")
        if should_check(path, path.relative_to(asset_root), output_dir)
    )
    asset_results = [import_state(asset, asset_root) for asset in assets]
    failed_assets = [
        result
        for result in asset_results
        if result["status"]
        in {
            "missing-import-sidecar",
            "invalid-import",
            "sidecar-read-failed",
            "read-failed",
        }
    ]
    version = (version_result.stdout or version_result.stderr or "unknown").strip()
    passed = import_result.returncode == 0 and not error_lines and not failed_assets
    report = {
        "schema_version": 1,
        "passed": passed,
        "godot_executable": godot,
        "godot_version": version,
        "import_exit_code": import_result.returncode,
        "asset_count": len(asset_results),
        "failed_asset_count": len(failed_assets),
        "error_lines": error_lines,
        "warning_count": len(warning_lines),
        "assets": asset_results,
    }
    (output_dir / "godot_import_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "passed": passed,
                "report": str(output_dir / "godot_import_report.json"),
                "failed_assets": len(failed_assets),
                "errors": len(error_lines),
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
