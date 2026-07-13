---
name: prepare-godot-assets
description: "Audit, deduplicate, classify, normalize, convert, validate, and index game assets for Godot 4.x. Use when Codex needs to turn a messy downloaded asset dump into a Godot-ready library; identify corrupt, mislabeled, duplicate, unsafe, unsupported, or toolchain-dependent files; migrate mixed image, sprite, audio, font, model, material, and data packs; troubleshoot assets Godot cannot import; create a normalized staging tree; verify imports with the target Godot executable; or generate a machine-readable asset catalog that AI agents can query reliably."
---

# Prepare Godot Assets

Turn untrusted, unstructured game files into a traceable library whose assets are
actually importable by the target Godot version and discoverable by agents.

## Operating Contract

- Treat the source dump as read-only. Write audit, staging, quarantine, and final
  outputs elsewhere. Never rename, delete, or convert files in place.
- Pin every staged operation to the audited source SHA-256. Never trust an
  extension as proof of content or compatibility.
- Keep technical readiness, visual/gameplay quality, and usage rights as three
  separate decisions. Never infer a license from a filename or download host.
- Treat scripts, executables, Godot scenes/resources, shaders, archives, and
  symlinks from untrusted packs as active or review-required content.
- Prefer stable, open interchange formats and project-local dependencies.
- Call an asset `ready` only after the target Godot importer succeeds. Call it
  `ready_for_agent` only when technical status is `ready` and rights status is
  explicitly allowed.
- Preserve cohesive dependencies. Keep a model with its textures, materials,
  skeleton, animations, and license metadata until references are repaired.

## Start

1. Resolve `SKILL_DIR` to this skill's directory.
2. Inspect the target repository, `project.godot`, current asset tree, Godot
   version, renderer, platform targets, and existing naming/import conventions.
3. Locate available tools with `godot --version`, `magick -version`,
   `ffmpeg -version`, `ffprobe -version`, and `blender --version`. Do not install
   or invoke a converter unless the selected workflow needs it.
4. Define four locations: immutable source, audit output, staging output, and
   target project. Keep audit output outside the source tree.
5. Read only the needed references:
   - Read [godot-compatibility.md](references/godot-compatibility.md) before
     choosing target formats or diagnosing importer behavior.
   - Read [taxonomy-and-catalog.md](references/taxonomy-and-catalog.md) before
     renaming, classifying, writing sidecars, or designing Agent retrieval.
   - Read [conversion-and-quality.md](references/conversion-and-quality.md)
     before converting or accepting images, animation sets, audio, or 3D assets.

## Workflow

### 1. Audit the source

Run the dependency-free auditor before opening or converting untrusted files:

```bash
python "$SKILL_DIR/scripts/audit_assets.py" SOURCE \
  --output-dir WORK/audit
```

Use `inventory.jsonl` as the source of truth. Review `AUDIT.md` and
`audit_summary.json` for exact duplicates, corrupt/empty files, extension-content
mismatches, conversion candidates, conditional imports, and quarantined content.
Do not deduplicate on filename, dimensions, or appearance alone. Hashes prove
only exact identity; compare perceptual or semantic duplicates visually.

### 2. Triage and inspect

Assign every file one disposition:

- `candidate`: content is plausibly usable and can move to staging.
- `convert`: preserve the original and create a canonical derivative.
- `review`: inspect native resources, archives, SVGs, shaders, scripts, license
  files, or toolchain-dependent formats before allowing them into staging.
- `quarantine`: keep outside the project because the file is corrupt, unsafe,
  misleading, or unresolved.
- `reject`: document the reason and leave the source untouched.

Preview candidates at their intended game scale. Inspect alpha, padding,
spritesheet geometry, frame ordering, tile seams, audio duration/peaks/loops,
model materials, external references, skeletons, clips, scale, and orientation.
Record decisions rather than silently dropping files.

### 3. Design the normalized tree and plan

Apply the taxonomy and naming rules from
[taxonomy-and-catalog.md](references/taxonomy-and-catalog.md). Preserve pack or
model subtrees when flattening would break references. Create a JSONL plan with
one object per selected derivative:

```json
{"source":"Pack 1/Hero Idle.PNG","destination":"art/characters/hero/animations/idle_00.png","action":"copy","expected_sha256":"<64 lowercase hex>","metadata":{"asset_id":"character.hero.idle.00","category":"art/characters","tags":["hero","idle"],"license":{"status":"unknown"},"source":{"original_path":"Pack 1/Hero Idle.PNG"}}}
```

Use only `copy`, `image-png`, `audio-wav`, or `audio-ogg` actions with the bundled
materializer. Handle 3D conversion and content-aware sprite/tile operations
explicitly, then audit their derivatives again.

Validate the complete plan first, then apply it:

```bash
python "$SKILL_DIR/scripts/materialize_asset_plan.py" WORK/asset-plan.jsonl \
  --source-root SOURCE --destination-root WORK/staging

python "$SKILL_DIR/scripts/materialize_asset_plan.py" WORK/asset-plan.jsonl \
  --source-root SOURCE --destination-root WORK/staging --apply \
  --report WORK/materialize-report.json
```

The materializer rejects traversal, symlinks, source drift, disguised extensions,
duplicate destinations, overlapping roots, missing tools, and overwrites.

### 4. Apply content-specific quality gates

Follow [conversion-and-quality.md](references/conversion-and-quality.md). Prefer
PNG for pixel art, masks, sprites, UI, and lossless textures; Ogg Vorbis for
music/ambience; WAV for short latency-sensitive effects; and glTF/GLB for 3D.
Do not upscale low-resolution art to manufacture detail. Do not transcode lossy
sources repeatedly. Keep source masters and document derivative settings.

Re-run `audit_assets.py` on staging. Resolve every mismatch, decode failure,
unsupported format, accidental duplicate, and quarantine item before import.

### 5. Verify with the target Godot version

Put staging under the target project only after active content is reviewed. If no
target exists, create a disposable minimal project using the intended Godot 4.x
executable and platform assumptions. Let Godot generate import sidecars and cache;
never reuse stale `.import` or `.godot/` data from downloaded packs.

```bash
python "$SKILL_DIR/scripts/verify_godot_import.py" PROJECT \
  --asset-root assets --output-dir WORK/godot-verify \
  --godot GODOT_EXECUTABLE
```

Treat a nonzero exit, importer error line, `valid=false`, or missing import
sidecar for an external resource as failure. Inspect warnings even when the
report passes. Test representative assets in actual scenes after import: frame
timing, tile alignment, texture filtering, audio loops, model materials,
animations, scale, and runtime memory are not proven by importer success.

### 6. Build the Agent index

Add `<asset filename>.asset.json` sidecars for descriptions, stable IDs, source,
rights, semantic tags, usage, relationships, and import intent. Then build the
catalog with the import report so theoretical support is not marked `ready`:

```bash
python "$SKILL_DIR/scripts/build_asset_catalog.py" PROJECT/assets \
  --project-root PROJECT --output-dir PROJECT/asset_catalog \
  --import-report WORK/godot-verify/godot_import_report.json
```

Use `asset_catalog.jsonl` for Agent queries, `asset_catalog.summary.json` for
automation, and `ASSET_CATALOG.md` for human scanning. Keep unknown-rights and
failed/review assets indexed but ineligible for production Agent selection.

### 7. Promote and report

Promote only verified staging assets into the project's owned asset tree. Keep
the source dump, audit artifacts, plan, materialization report, Godot report, and
catalog traceable to one run. Report:

- counts by disposition, category, technical status, and rights status;
- exact duplicates and the retained canonical copy;
- conversions with source and derivative hashes;
- rejected/quarantined files with reasons;
- Godot version and import failures/warnings;
- catalog path and number of `ready_for_agent` assets;
- unresolved visual, license, attribution, or runtime risks.

## Scripts

- `scripts/audit_assets.py`: inspect content signatures, hashes, metadata,
  duplicates, and preliminary Godot status without modifying source files.
- `scripts/materialize_asset_plan.py`: validate and safely apply a hash-pinned
  copy/image/audio plan into a non-overlapping staging tree.
- `scripts/verify_godot_import.py`: run Godot headlessly and check importer logs
  plus per-file `.import` state.
- `scripts/build_asset_catalog.py`: merge verified files and sidecars into
  deterministic JSONL, JSON summary, and Markdown indexes.

## Check Before Finishing

- Confirm the original dump was not modified.
- Confirm normalized names are collision-free and all dependency references work.
- Confirm staging contains no unresolved mismatches, unsafe content, or stale
  Godot caches.
- Confirm the exact target Godot version imported every promoted external asset.
- Confirm representative assets work in scenes at intended settings and scale.
- Confirm every catalog record has technical and rights status, and every
  `ready_for_agent` record has a valid `res://` path and stable asset ID.
- Confirm provenance, license text, attribution requirements, and transformation
  history are retained rather than guessed.
