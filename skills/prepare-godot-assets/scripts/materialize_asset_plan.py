#!/usr/bin/env python3
"""Safely copy or convert assets from an explicit, hash-pinned JSONL plan."""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from _asset_utils import FORMAT_BY_EXTENSION, inspect_file, sha256_file


DESTINATION_RE = re.compile(r"^[a-z0-9][a-z0-9_./-]*$")
ALLOWED_ACTIONS = {"copy", "image-png", "audio-wav", "audio-ogg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "plan",
        type=Path,
        help="JSONL plan with source, destination, action, and expected_sha256",
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Materialize the plan; default is validation only",
    )
    parser.add_argument("--report", type=Path, help="Optional JSON execution report")
    return parser.parse_args()


def relative_path(
    value: Any, field: str, *, normalized_destination: bool = False
) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if "\\" in value:
        raise ValueError(f"{field} must use forward slashes: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"{field} must be a clean relative path: {value!r}")
    if normalized_destination and (
        not DESTINATION_RE.fullmatch(value) or "//" in value
    ):
        raise ValueError(
            f"destination must be lowercase ASCII snake_case/path-case: {value!r}"
        )
    return path


def load_plan(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error
            if not isinstance(row, dict):
                raise ValueError(f"Plan line {line_number} must be a JSON object")
            row["_line"] = line_number
            rows.append(row)
    if not rows:
        raise ValueError("Plan contains no operations")
    return rows


def roots_overlap(first: Path, second: Path) -> bool:
    try:
        first.relative_to(second)
        return True
    except ValueError:
        pass
    try:
        second.relative_to(first)
        return True
    except ValueError:
        return False


@functools.lru_cache(maxsize=None)
def resolve_tool(action: str) -> str | None:
    if action == "image-png":
        for candidate in ("magick", "convert"):
            tool = shutil.which(candidate)
            if not tool:
                continue
            result = subprocess.run(
                [tool, "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if "ImageMagick" in ((result.stdout or "") + (result.stderr or "")):
                return tool
        return None
    if action in {"audio-wav", "audio-ogg"}:
        return shutil.which("ffmpeg")
    return None


@functools.lru_cache(maxsize=None)
def ffmpeg_encoders(tool: str) -> frozenset[str]:
    result = subprocess.run(
        [tool, "-hide_banner", "-encoders"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return frozenset()
    names = set()
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*[VAS][A-Z.]{5}\s+(\S+)", line)
        if match:
            names.add(match.group(1))
    return frozenset(names)


def validate_row(
    row: dict[str, Any],
    source_root: Path,
    destination_root: Path,
    destinations: set[Path],
) -> dict[str, Any]:
    line = row["_line"]
    source_rel = relative_path(row.get("source"), f"source on line {line}")
    destination_rel = relative_path(
        row.get("destination"),
        f"destination on line {line}",
        normalized_destination=True,
    )
    source = source_root.joinpath(*source_rel.parts)
    destination = destination_root.joinpath(*destination_rel.parts)
    if destination in destinations:
        raise ValueError(f"Duplicate destination on line {line}: {destination_rel}")
    destinations.add(destination)
    if not source.is_file() or source.is_symlink():
        raise ValueError(
            f"Source must be a regular, non-symlink file on line {line}: {source_rel}"
        )

    expected_hash = row.get("expected_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_hash
    ):
        raise ValueError(f"expected_sha256 must be a lowercase SHA-256 on line {line}")
    actual_hash = sha256_file(source)
    if actual_hash != expected_hash:
        raise ValueError(f"Source hash changed on line {line}: {source_rel}")

    action = row.get("action")
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported action on line {line}: {action!r}")
    details = inspect_file(source)
    destination_format = FORMAT_BY_EXTENSION.get(destination.suffix.lower())
    if action == "copy":
        if details["detected_format"] != destination_format:
            raise ValueError(
                f"copy cannot disguise {details['detected_format']!r} as {destination.suffix!r} on line {line}"
            )
    elif action == "image-png":
        if details["media_type"] != "image" or destination.suffix != ".png":
            raise ValueError(
                f"image-png requires an image source and .png destination on line {line}"
            )
    elif action == "audio-wav":
        if details["media_type"] != "audio" or destination.suffix != ".wav":
            raise ValueError(
                f"audio-wav requires an audio source and .wav destination on line {line}"
            )
    elif action == "audio-ogg":
        if details["media_type"] != "audio" or destination.suffix != ".ogg":
            raise ValueError(
                f"audio-ogg requires an audio source and .ogg destination on line {line}"
            )

    tool = resolve_tool(action)
    if action != "copy" and not tool:
        raise ValueError(
            f"Required conversion tool is unavailable for {action} on line {line}"
        )
    if action == "audio-wav" and "pcm_s16le" not in ffmpeg_encoders(tool):
        raise ValueError(
            f"FFmpeg lacks the pcm_s16le encoder required by audio-wav on line {line}"
        )
    if action == "audio-ogg" and "libvorbis" not in ffmpeg_encoders(tool):
        raise ValueError(
            f"FFmpeg lacks libvorbis required by audio-ogg on line {line}; "
            "keep a Godot-compatible source or choose audio-wav"
        )
    metadata = row.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(f"metadata must be an object on line {line}")

    existing = None
    if destination.exists():
        if not destination.is_file() or destination.is_symlink():
            raise ValueError(
                f"Destination is not a regular file on line {line}: {destination_rel}"
            )
        if action == "copy" and sha256_file(destination) == actual_hash:
            existing = "identical"
        elif action != "copy":
            existing = "compare-derivative"
        else:
            raise ValueError(
                f"Refusing to overwrite destination on line {line}: {destination_rel}"
            )

    return {
        "line": line,
        "source": source,
        "source_rel": source_rel.as_posix(),
        "destination": destination,
        "destination_rel": destination_rel.as_posix(),
        "action": action,
        "tool": tool,
        "metadata": metadata,
        "source_sha256": actual_hash,
        "existing": existing,
    }


def run_conversion(operation: dict[str, Any], temp_path: Path) -> None:
    source = operation["source"]
    action = operation["action"]
    tool = operation["tool"]
    if action == "copy":
        shutil.copy2(source, temp_path)
        return
    if action == "image-png":
        command = [tool, str(source), "-auto-orient", "-strip", str(temp_path)]
    elif action == "audio-wav":
        command = [
            tool,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map_metadata",
            "-1",
            "-vn",
            "-c:a",
            "pcm_s16le",
            str(temp_path),
        ]
    else:
        command = [
            tool,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map_metadata",
            "-1",
            "-vn",
            "-c:a",
            "libvorbis",
            "-q:a",
            "6",
            str(temp_path),
        ]
    subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )


def write_sidecar(operation: dict[str, Any]) -> None:
    if not operation["metadata"]:
        return
    sidecar = Path(str(operation["destination"]) + ".asset.json")
    payload = dict(operation["metadata"])
    payload.setdefault("source_sha256", operation["source_sha256"])
    encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{sidecar.name}.", dir=sidecar.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
        os.replace(name, sidecar)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def prepare_operations(operations: list[dict[str, Any]], scratch_root: Path) -> None:
    for operation in operations:
        if operation["existing"] == "identical":
            continue
        prepared = scratch_root / operation["destination_rel"]
        prepared.parent.mkdir(parents=True, exist_ok=True)
        run_conversion(operation, prepared)
        if not prepared.is_file() or prepared.stat().st_size == 0:
            raise RuntimeError(
                f"Operation produced no usable file: {operation['destination_rel']}"
            )
        details = inspect_file(prepared)
        expected_format = FORMAT_BY_EXTENSION.get(
            operation["destination"].suffix.lower()
        )
        if (
            details["detected_format"] != expected_format
            or details["godot_status"] == "quarantine"
        ):
            raise RuntimeError(
                f"Prepared derivative failed validation: {operation['destination_rel']} "
                f"({', '.join(details['issues']) or details['detected_format']})"
            )
        if operation["existing"] == "compare-derivative":
            if sha256_file(prepared) != sha256_file(operation["destination"]):
                raise RuntimeError(
                    f"Refusing to overwrite a different derivative: {operation['destination_rel']}"
                )
            operation["existing"] = "identical"
            prepared.unlink()
            continue
        operation["prepared"] = prepared


def commit_operations(operations: list[dict[str, Any]]) -> list[str]:
    results = []
    for operation in operations:
        if operation["existing"] == "identical":
            write_sidecar(operation)
            results.append("existing-identical")
            continue
        destination = operation["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(operation["prepared"], destination)
        write_sidecar(operation)
        results.append("created")
    return results


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    destination_root = args.destination_root.resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist: {source_root}")
    if roots_overlap(source_root, destination_root):
        raise SystemExit("Source and destination roots must not overlap")

    try:
        rows = load_plan(args.plan)
        destinations: set[Path] = set()
        operations = [
            validate_row(row, source_root, destination_root, destinations)
            for row in rows
        ]
    except ValueError as error:
        raise SystemExit(str(error)) from error

    operation_results = ["validated"] * len(operations)
    if args.apply:
        destination_root.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(
                prefix=".asset-plan-", dir=destination_root.parent
            ) as scratch:
                prepare_operations(operations, Path(scratch))
                operation_results = commit_operations(operations)
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() if error.stderr else str(error)
            raise SystemExit(f"Conversion failed: {message}") from error
        except RuntimeError as error:
            raise SystemExit(str(error)) from error

    results = []
    for operation, result in zip(operations, operation_results):
        results.append(
            {
                "line": operation["line"],
                "source": operation["source_rel"],
                "destination": operation["destination_rel"],
                "action": operation["action"],
                "result": result,
            }
        )
    report = {
        "applied": args.apply,
        "operation_count": len(results),
        "operations": results,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
