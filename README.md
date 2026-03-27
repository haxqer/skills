# hax-skills

Monorepo for several reusable Codex skills, maintained as one Git repository.

The canonical installable skill roots live under `skills/` and follow the same
layout:

```text
skills/<skill-name>/
  SKILL.md
  agents/
  references/
  scripts/
```

That makes the repository easier to validate, install, and maintain with
generic tooling.

## Included Skills

| Skill Directory | Installed As | Purpose |
| --- | --- | --- |
| `skills/desktop-gui-dev/` | `desktop-gui-dev` | Desktop GUI app selection, scaffolding, implementation, packaging, and review |
| `skills/phaser/` | `phaser` | Phaser 3 browser game development, debugging, and runtime validation |
| `skills/game-asset-gen/` | `game-asset-gen` | Pixel-art sprite, icon, and frame-sequence generation for retro 2D games |
| `skills/game-remake-research/` | `game-remake-research` | Research-pack workflow for remaking an existing game |
| `skills/bdd-skill/` | `bdd-skill` | BDD and Gherkin drafting, refinement, and review |
| `skills/godot/` | `godot` | Godot project development, scene editing, export, and resource repair |
| `skills/ralph-loop/` | `ralph-loop` | Closed-loop autonomous engineering protocol until done |
| `skills/subagents/` | `subagents` | Lead-agent orchestration for branch-isolated multi-agent collaboration |

## Repository Layout

```text
hax-skills/
  skills/
    desktop-gui-dev/
    phaser/
    game-asset-gen/
    game-remake-research/
    bdd-skill/
    godot/
    ralph-loop/
    subagents/
  scripts/
    link-skills.sh
    package-godot-skill.sh
    validate_skill_layout.py
  tests/
    godot/
  .github/
    workflows/
      validate-skills.yml
      game-remake-research-ci.yml
```

Notes:

- Every directory under `skills/` is an installable Skill root.
- The folder name of each installed Skill matches the `name:` field in its
  `SKILL.md`.
- Repo-level helpers such as CI, packaging, and tests live outside `skills/`
  so the Skill payloads stay clean.

## Install Into Codex

Use the helper script to symlink every Skill in `skills/` into
`$CODEX_HOME/skills`.

```bash
./scripts/link-skills.sh
```

By default, the script links into `~/.codex/skills`. Override `CODEX_HOME` if
needed:

```bash
CODEX_HOME=/path/to/.codex ./scripts/link-skills.sh
```

## Maintenance

- Edit the installable payloads directly under `skills/`.
- Keep tests and packaging helpers outside the Skill roots.
- Use `scripts/package-godot-skill.sh` when you want a release zip for the `godot` Skill.
- Run `python3 ./scripts/validate_skill_layout.py --strict-warnings` before pushing structural Skill changes.
- The Game Remake Research smoke workflow lives at `.github/workflows/game-remake-research-ci.yml`.
- The repo-wide layout validator lives at `.github/workflows/validate-skills.yml`.

## Push To GitHub

Once the remote is configured, push the monorepo normally:

```bash
git push -u origin main
```
