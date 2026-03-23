#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME/skills"
SOURCE_DIR="$ROOT_DIR/skills"

mkdir -p "$SKILLS_DIR"

for skill_root in "$SOURCE_DIR"/*; do
  [[ -d "$skill_root" ]] || continue
  [[ -f "$skill_root/SKILL.md" ]] || continue
  skill_name="$(basename "$skill_root")"
  ln -sfn "$skill_root" "$SKILLS_DIR/$skill_name"
done

printf 'Linked skills into %s\n' "$SKILLS_DIR"
