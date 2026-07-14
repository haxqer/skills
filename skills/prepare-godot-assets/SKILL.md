---
name: prepare-godot-assets
description: "Audit, deduplicate, classify, normalize, convert, validate, and index game assets into a standalone, portable library suitable for Godot 4.x. Use when Codex needs to turn a messy downloaded asset dump into a clean asset library with purpose-revealing paths and filenames, preserve provenance and rights, identify corrupt or unsafe files, convert mixed image/audio/3D formats, create human-readable and machine-readable indexes plus a package-level AGENTS.md guide for AI discovery, or optionally check compatibility with an existing Godot project. The deliverable is an asset library, not a Godot project."
---

# Prepare Godot Assets

Turn untrusted, unstructured game files into a standalone, portable asset
library. Make every accepted asset understandable from its path and filename and
selectable from the catalog without opening every file.

## Output Contract

- Deliver a library directory, never a generated Godot project:

  ```text
  asset_library/
    AGENTS.md     # AI entry point: type-to-directory map and package usage
    assets/       # normalized, usable assets and adjacent metadata sidecars
    catalog/      # JSONL, JSON summary, and Markdown indexes
    licenses/     # verified license and attribution texts when available
  ```

- Keep audit reports, quarantine, conversion scratch files, Godot caches, and
  temporary staging outside `asset_library/`.
- Treat the source dump as read-only. Never rename, delete, or convert files in
  place. Pin every staged operation to the audited source SHA-256.
- Keep integrity, content quality, Godot compatibility, metadata completeness,
  and usage rights as separate decisions. Godot import verification is optional
  evidence and does not change the output into a project.
- Preserve cohesive dependencies. Keep a model with its textures, materials,
  skeleton, animations, and license metadata when flattening would break it.
- Include a sidecar for every accepted asset or indivisible asset bundle. Do not
  mark an asset `ready_for_agent` unless its catalog metadata explains what it is,
  where it is, when to use it, and any known restrictions.

## Start

1. Resolve `SKILL_DIR` to this skill's directory.
2. Define four separate locations: immutable `SOURCE`, disposable `WORK`, final
   `LIBRARY`, and `QUARANTINE`. Do not place `LIBRARY` inside `SOURCE`.
3. If the user supplies an existing Godot project, inspect its Godot version,
   renderer, platform targets, and naming/import conventions as compatibility
   constraints only. Never create a project when none was supplied.
4. Locate only the tools needed by the selected workflow with `godot --version`,
   `magick -version`, `ffmpeg -version`, `ffprobe -version`, and
   `blender --version`.
5. Read the relevant references:
   - Read [taxonomy-and-catalog.md](references/taxonomy-and-catalog.md) before
     designing directories, renaming files, writing sidecars, or building indexes.
   - Read [godot-compatibility.md](references/godot-compatibility.md) before
     choosing delivery formats or optionally testing an existing Godot project.
   - Read [conversion-and-quality.md](references/conversion-and-quality.md)
     before converting or accepting images, animation sets, audio, or 3D assets.

## Workflow

### 1. Audit the source

Run the dependency-free auditor before opening or converting untrusted files:

```bash
python3 "$SKILL_DIR/scripts/audit_assets.py" SOURCE \
  --output-dir WORK/audit
```

Use `inventory.jsonl` as the source of truth. Review `AUDIT.md` and
`audit_summary.json` for exact duplicates, empty or corrupt files,
extension-content mismatches, conversion candidates, conditional formats, and
quarantined content. Hashes prove only exact identity; inspect perceptual or
semantic duplicates before choosing a canonical asset.

### 2. Triage and inspect

Assign every file one disposition: `candidate`, `convert`, `review`,
`quarantine`, or `reject`. Preview candidates at their intended game scale.
Inspect alpha, padding, frame geometry and order, tile seams, audio duration and
loops, model dependencies and materials, animation clips, scale, orientation,
and relevant quality issues. Record decisions instead of silently dropping files.

Treat scripts, executables, Godot scenes/resources, shaders, archives, SVGs, and
symlinks from untrusted packs as active or review-required content. Keep unsafe,
corrupt, misleading, and unresolved files outside the final library.

### 3. Design the library and plan

Apply [taxonomy-and-catalog.md](references/taxonomy-and-catalog.md). Use category
directories and purpose-revealing filenames. A caller should understand the
subject, gameplay/UI role, state, variant, and sequence position from a path such
as `assets/2d/characters/hero/animations/hero_run_side_03.png`.

Create a JSONL plan with one object per selected derivative. Include complete
catalog metadata in every row:

```json
{"source":"Pack 1/Hero Run (4).PNG","destination":"2d/characters/hero/animations/hero_run_side_03.png","action":"copy","expected_sha256":"<64 lowercase hex>","metadata":{"asset_id":"character.hero.run.side.03","name":"Hero run side frame 03","description":"Fourth side-view frame of the playable hero run cycle.","category":"2d/characters","tags":["hero","player","run","side-view","animation-frame"],"license":{"status":"unknown"},"source":{"original_path":"Pack 1/Hero Run (4).PNG"},"usage":{"recommended_for":["playable hero side-view run animation"],"avoid":["portrait or standalone illustration"]},"relationships":{"animation_set":"character.hero.run.side","sequence_index":3},"technical_status":"ready"}}
```

Use only `copy`, `image-png`, `audio-wav`, or `audio-ogg` actions with the bundled
materializer. Handle 3D conversion and content-aware sprite/tile operations
explicitly, then audit their derivatives again.

Validate the complete plan before applying it directly to the final `assets/`
tree. `--require-metadata` rejects rows that cannot produce a useful index:

```bash
python3 "$SKILL_DIR/scripts/materialize_asset_plan.py" WORK/asset-plan.jsonl \
  --source-root SOURCE --destination-root LIBRARY/assets --require-metadata

python3 "$SKILL_DIR/scripts/materialize_asset_plan.py" WORK/asset-plan.jsonl \
  --source-root SOURCE --destination-root LIBRARY/assets --require-metadata \
  --apply --report WORK/materialize-report.json
```

The materializer rejects traversal, symlinks, source drift, inconsistent source
hash metadata, disguised extensions, duplicate destinations or asset IDs,
overlapping roots, missing tools, and overwrites.

### 4. Apply quality gates

Follow [conversion-and-quality.md](references/conversion-and-quality.md). Prefer
PNG for pixel art, sprites, UI, masks, and lossless textures; Ogg Vorbis for
music and ambience; WAV for short latency-sensitive effects; and glTF/GLB for 3D.
Do not upscale low-resolution art to manufacture detail or repeatedly transcode
lossy sources. Keep source provenance and derivative settings in metadata.

Re-run `audit_assets.py` on `LIBRARY/assets`. Resolve every mismatch, decode
failure, unsupported format, accidental duplicate, unsafe file, and broken
dependency. Review every final path and filename for selection clarity.

### 5. Build and inspect the indexes

Build the standalone catalog from the final library. An import report is optional
and only records compatibility evidence from a user-supplied existing project:

```bash
python3 "$SKILL_DIR/scripts/build_asset_catalog.py" LIBRARY/assets \
  --library-root LIBRARY --output-dir LIBRARY/catalog
```

Use:

- `AGENTS.md` as the Agent's package-level entry point, directory map, and usage
  guide;
- `catalog/asset_catalog.jsonl` as the complete Agent retrieval source;
- `catalog/asset_catalog.summary.json` for counts and automated checks;
- `catalog/ASSET_CATALOG.md` for human scanning by purpose, category, status,
  rights, and portable library path.

Inspect records with missing metadata and fix their sidecars. The final catalog
must let a user or Agent search by intended use, subject, role, state, viewpoint,
variant, technical traits, rights, and relationships, then locate the asset via
`library_path` without relying on `res://` or a project layout.

### 6. Optionally verify an existing Godot project

Run this step only when the user supplied a target project and asks for importer
or runtime validation. Copy or link a disposable snapshot of the library into
that project's approved asset location; do not mutate the standalone library
with `.godot/`, `.import`, `.uid`, project files, or test scenes.

```bash
python3 "$SKILL_DIR/scripts/verify_godot_import.py" EXISTING_PROJECT \
  --asset-root assets --output-dir WORK/godot-verify \
  --godot GODOT_EXECUTABLE

python3 "$SKILL_DIR/scripts/build_asset_catalog.py" LIBRARY/assets \
  --library-root LIBRARY --output-dir LIBRARY/catalog \
  --import-report WORK/godot-verify/godot_import_report.json
```

Treat importer failure as compatibility evidence, not permission to turn the
library into a Godot project. Record the exact Godot version and test
representative assets in real scenes only when that integration was requested.

### 7. Report the library

Report the final library path and:

- counts by category, technical status, metadata status, rights status, and
  optional Godot compatibility status;
- exact duplicates and the retained canonical asset;
- conversions with source and derivative hashes;
- rejected or quarantined files with reasons;
- Agent index and catalog paths plus the `ready_for_agent` count;
- unresolved visual, dependency, license, attribution, or compatibility risks.

## Scripts

- `scripts/audit_assets.py`: inspect signatures, hashes, metadata, duplicates,
  and preliminary Godot format status without modifying source files.
- `scripts/materialize_asset_plan.py`: validate and safely apply a hash-pinned
  copy/image/audio plan into the standalone library.
- `scripts/build_asset_catalog.py`: merge assets and sidecars into deterministic
  JSONL, JSON summary, and Markdown indexes, including the root `AGENTS.md`
  package guide, using portable library paths.
- `scripts/verify_godot_import.py`: optionally test a snapshot inside an existing
  Godot project; never use it to create the library itself.

## Check Before Finishing

- Confirm the original dump was not modified and the final output contains no
  `project.godot`, `.godot/`, imported cache, temporary reports, or quarantine.
- Confirm the library has `AGENTS.md`, `assets/`, `catalog/`, and applicable
  `licenses/` deliverables at its top level.
- Confirm normalized paths are collision-free, filenames reveal intended use,
  and cohesive dependency references work.
- Confirm every accepted asset has a stable ID, non-empty description, semantic
  tags, recommended uses, rights status, source provenance, and `library_path`.
- Confirm `ASSET_CATALOG.md` is useful for scanning and every JSONL record can be
  located relative to the library root.
- Confirm root `AGENTS.md` maps every catalog category to its actual directory,
  summarizes typical uses, and explains how to select and integrate the pack.
- Confirm compatibility is marked `not_tested` unless evidence came from the
  exact user-supplied Godot target; never generate a project just to change it.
