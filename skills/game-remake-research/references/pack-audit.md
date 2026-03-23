# Pack Audit

Use this reference when a remake research pack needs a fast quality gate before merge or handoff.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Purpose

`audit_remake_pack.py` checks for:

- missing core markdown files
- missing required section headings in the core docs
- default scaffold placeholders that are still blank
- missing or empty support CSVs
- incomplete role coverage
- archetype-pack coherence
- experiment-pack coherence
- baseline-version placeholders that were never replaced
- stale generated artifacts such as experiment summaries, evidence-link reports, status reports, handoff dossiers, and handoff manifests

## Workflow

1. Update the pack docs and support CSVs.
2. Regenerate experiment summaries and metric rollups if those files are in scope.
3. Run:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/audit_remake_pack.py" \
  --docs-dir ./docs/remake-maplestory
```

4. Fix every reported error.
5. Decide whether warnings are acceptable or whether the pack still needs another pass.

Run with `--strict` when warnings should also fail the handoff:

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/audit_remake_pack.py" \
  --docs-dir ./docs/remake-maplestory \
  --strict
```

Use `--language en` when you want to pin the output explicitly. `--language auto` currently resolves to `en`.

## Output Semantics

- `PASS`: no errors and no warnings
- `WARN`: no structural errors, but scaffold debt or incomplete support data still exists
- `FAIL`: required files or required sections are missing

Warnings are meant to highlight unfinished research, not stylistic differences.
They also include stale derived artifacts, because an accurate pack can still mislead reviewers if its summaries, dossiers, or audit exports lag behind newer source edits.
