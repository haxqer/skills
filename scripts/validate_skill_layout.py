#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


ALLOWED_TOP_LEVEL = {"SKILL.md", "agents", "scripts", "references", "assets"}
FORBIDDEN_DOC_PREFIXES = (
    "README",
    "CHANGELOG",
    "INSTALLATION_GUIDE",
    "QUICK_REFERENCE",
)
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,63}$")
FRONTMATTER_DELIMITER = "---"


@dataclass
class SkillReport:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Codex skill directory layout under a monorepo."
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Directory containing installable skill roots. Default: %(default)s",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Fail when warnings are present.",
    )
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir).resolve()
    if not skills_dir.is_dir():
        print(f"ERROR: skills directory does not exist: {skills_dir}")
        return 1

    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not skill_dirs:
        print(f"ERROR: no skill directories found under {skills_dir}")
        return 1

    reports = [validate_skill_dir(skill_dir) for skill_dir in skill_dirs]

    total_errors = 0
    total_warnings = 0
    for report in reports:
        print(f"[{report.path.name}]")
        if not report.errors and not report.warnings:
            print("  OK")
            continue
        for error in report.errors:
            total_errors += 1
            print(f"  ERROR: {error}")
        for warning in report.warnings:
            total_warnings += 1
            print(f"  WARNING: {warning}")

    print(
        f"\nSummary: {len(reports)} skills checked, {total_errors} error(s), {total_warnings} warning(s)"
    )

    if total_errors:
        return 1
    if args.strict_warnings and total_warnings:
        return 1
    return 0


def validate_skill_dir(skill_dir: Path) -> SkillReport:
    report = SkillReport(path=skill_dir)
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        report.errors.append("missing required SKILL.md")
        return report

    validate_top_level_entries(skill_dir, report)
    validate_forbidden_docs(skill_dir, report)

    text = skill_md.read_text(encoding="utf-8")
    metadata, body = parse_skill_frontmatter(text, report)

    name = metadata.get("name")
    description = metadata.get("description")

    if not name:
        report.errors.append("frontmatter is missing required field: name")
    elif not SKILL_NAME_PATTERN.fullmatch(name):
        report.errors.append(
            "frontmatter name must use lowercase letters, digits, and hyphens only, with max length 63"
        )
    elif skill_dir.name != name:
        report.errors.append(
            f"directory name must match frontmatter name: expected '{name}', found '{skill_dir.name}'"
        )

    if not description:
        report.errors.append("frontmatter is missing required field: description")

    if not body.strip():
        report.errors.append("SKILL.md body is empty")

    line_count = len(text.splitlines())
    if line_count > 500:
        report.warnings.append(
            f"SKILL.md is {line_count} lines; keep it under 500 lines when practical"
        )

    validate_agents(skill_dir, report)
    validate_optional_dir_mentions(skill_dir, text, report)

    return report


def validate_top_level_entries(skill_dir: Path, report: SkillReport) -> None:
    for entry in sorted(skill_dir.iterdir(), key=lambda path: path.name):
        if entry.name not in ALLOWED_TOP_LEVEL:
            report.errors.append(
                f"unexpected top-level entry '{entry.name}'; allowed entries are: {', '.join(sorted(ALLOWED_TOP_LEVEL))}"
            )


def validate_forbidden_docs(skill_dir: Path, report: SkillReport) -> None:
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        upper_name = path.name.upper()
        if upper_name.startswith(FORBIDDEN_DOC_PREFIXES):
            relative = path.relative_to(skill_dir)
            report.errors.append(
                f"forbidden auxiliary documentation file inside skill root: {relative}"
            )


def validate_agents(skill_dir: Path, report: SkillReport) -> None:
    agents_dir = skill_dir / "agents"
    if not agents_dir.exists():
        report.warnings.append("missing recommended agents/openai.yaml metadata")
        return
    if not agents_dir.is_dir():
        report.errors.append("agents exists but is not a directory")
        return

    openai_yaml = agents_dir / "openai.yaml"
    if not openai_yaml.is_file():
        report.warnings.append("agents directory exists without agents/openai.yaml")
        return

    yaml_text = openai_yaml.read_text(encoding="utf-8")
    if "interface:" not in yaml_text:
        report.warnings.append("agents/openai.yaml is missing interface metadata")
    for field in ("display_name:", "short_description:", "default_prompt:"):
        if field not in yaml_text:
            report.warnings.append(f"agents/openai.yaml is missing {field[:-1]}")


def validate_optional_dir_mentions(skill_dir: Path, text: str, report: SkillReport) -> None:
    for dirname in ("references", "scripts", "assets"):
        path = skill_dir / dirname
        if path.is_dir() and f"{dirname}/" not in text:
            report.warnings.append(
                f"SKILL.md does not mention '{dirname}/'; consider referencing bundled resources explicitly"
            )


def parse_skill_frontmatter(text: str, report: SkillReport) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    metadata: dict[str, str] = {}

    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        report.errors.append("SKILL.md must start with YAML frontmatter delimited by ---")
        return metadata, text

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_DELIMITER:
            closing_index = index
            break

    if closing_index is None:
        report.errors.append("SKILL.md frontmatter is missing a closing --- delimiter")
        return metadata, text

    frontmatter_lines = lines[1:closing_index]
    body_lines = lines[closing_index + 1 :]

    key_value_pattern = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
    for line in frontmatter_lines:
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue
        match = key_value_pattern.match(line)
        if not match:
            continue
        key, raw_value = match.groups()
        metadata[key] = strip_yaml_scalar(raw_value)

    return metadata, "\n".join(body_lines)


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


if __name__ == "__main__":
    sys.exit(main())
