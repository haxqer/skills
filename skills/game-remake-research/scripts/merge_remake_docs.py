#!/usr/bin/env python3
"""Merge a remake research pack into one markdown dossier."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_OUTPUT = "remake-dossier.md"
DEFAULT_MODE = "full"
DOSSIER_TEMPLATE_FILE = "remake-dossier-template.md"
EXPERIMENT_DESIGN_FILE = "09-experiment-design.md"
EXPERIMENT_SUMMARY_FILE = "10-experiment-summary.md"
EXPERIMENT_SUMMARY_COMPACT_FILE = "10-experiment-summary-compact.md"


def numeric_prefix(path: Path) -> tuple[int, str]:
    match = re.match(r"^(\d+)-", path.name)
    if match:
        return int(match.group(1)), path.name
    return 10_000, path.name


def load_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def is_generated_dossier(path: Path) -> bool:
    return (
        path.name == DEFAULT_OUTPUT
        or path.name == DOSSIER_TEMPLATE_FILE
        or path.name.endswith("-dossier.md")
        or path.name.endswith("-dossier-template.md")
    )


def select_experiment_summary(paths: list[Path], mode: str) -> set[str]:
    names = {path.name for path in paths}
    selected: set[str] = set()
    preferred = (
        [EXPERIMENT_SUMMARY_COMPACT_FILE, EXPERIMENT_SUMMARY_FILE]
        if mode == "compact"
        else [EXPERIMENT_SUMMARY_FILE, EXPERIMENT_SUMMARY_COMPACT_FILE]
    )
    for name in preferred:
        if name in names:
            selected.add(name)
            break
    return selected


def collect_markdown_files(
    input_dir: Path, output_name: str, include_log: bool, mode: str
) -> list[Path]:
    all_paths = sorted(input_dir.glob("*.md"), key=numeric_prefix)
    selected_summary_names = select_experiment_summary(all_paths, mode)

    files = []
    for path in all_paths:
        if path.name == output_name:
            continue
        if not include_log and path.name.startswith("99-"):
            continue
        if is_generated_dossier(path):
            continue
        if path.name in {
            EXPERIMENT_SUMMARY_FILE,
            EXPERIMENT_SUMMARY_COMPACT_FILE,
        } and path.name not in selected_summary_names:
            continue
        if mode == "compact":
            if path.name == EXPERIMENT_DESIGN_FILE:
                continue
        files.append(path)
    return files


def build_output(title: str, files: list[Path]) -> str:
    contents_heading = "Contents"
    lines = [f"# {title}", "", f"## {contents_heading}", ""]
    for path in files:
        heading = load_title(path)
        anchor = heading.lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)
        anchor = re.sub(r"\s+", "-", anchor).strip("-")
        lines.append(f"- [{heading}](#{anchor})")

    for path in files:
        lines.extend(["", "---", ""])
        lines.append(path.read_text(encoding="utf-8").rstrip())

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge a remake research pack into a single markdown dossier."
    )
    directory = parser.add_mutually_exclusive_group(required=True)
    directory.add_argument(
        "--docs-dir",
        help="Research pack directory.",
    )
    directory.add_argument(
        "--input-dir",
        help="Legacy alias for --docs-dir.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output file name inside the input directory. Defaults to {DEFAULT_OUTPUT}.",
    )
    parser.add_argument(
        "--title",
        help="Optional dossier title. Defaults to the input directory name.",
    )
    parser.add_argument(
        "--include-log",
        action="store_true",
        help="Include 99-research-log.md in the merged dossier.",
    )
    parser.add_argument(
        "--mode",
        choices=("full", "compact"),
        default=DEFAULT_MODE,
        help=(
            "Merge mode. `compact` excludes 09-experiment-design.md and prefers "
            "10-experiment-summary-compact.md when present."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir_arg = args.docs_dir or args.input_dir
    input_dir = Path(input_dir_arg).expanduser().resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(f"{input_dir} is not a directory.")

    output_path = input_dir / args.output
    if output_path.exists() and not args.force:
        raise FileExistsError(
            f"{output_path} already exists. Re-run with --force to overwrite."
        )

    files = collect_markdown_files(
        input_dir, output_path.name, args.include_log, args.mode
    )
    if not files:
        raise FileNotFoundError("No markdown files found to merge.")

    title = args.title or f"{input_dir.name} dossier"
    output = build_output(title, files)
    output_path.write_text(output, encoding="utf-8")

    print(f"Merged {len(files)} files into {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
