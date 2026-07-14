# Standalone Asset Taxonomy and Catalog

Use this reference when mapping source files to portable library paths and when
writing metadata that lets a human or Agent select an asset without opening every
file.

## Library Structure

Use this shallow, task-oriented baseline:

```text
asset_library/
  AGENTS.md
  assets/
    2d/
      characters/<character_id>/{animations,portraits,parts}/
      environments/{backgrounds,props,tilesets}/
      ui/{controls,icons,panels}/
      vfx/
    3d/
      characters/<character_id>/{models,materials,textures,animations}/
      environments/<environment_id>/{models,materials,textures}/
      props/<prop_id>/{models,materials,textures,animations}/
    audio/{ambience,music,sfx,voice}/
    fonts/
    shaders/
    data/
  catalog/
    asset_catalog.jsonl
    asset_catalog.summary.json
    ASSET_CATALOG.md
  licenses/
```

Keep generated audits, plans, conversion logs, quarantine, and Godot caches
outside `asset_library/`. Do not add `project.godot`, scenes, scripts, addons, or
import caches merely to make the directory look like a project.

Preserve a cohesive 3D bundle or pack below its owning category when relative
dependencies matter. Do not create one directory per file and do not mirror
arbitrary download-site folders.

## Purpose-Revealing Naming

- Use lowercase ASCII paths and `snake_case` filenames. Restrict paths to letters,
  digits, `_`, `-`, `.`, and `/`.
- Name by use, not by source name or appearance alone. Prefer this sequence when
  applicable: `<subject>_<role-or-action>_<state>_<view>_<variant>_<index>`.
- Include only tokens that change selection behavior. The category path already
  supplies broad context, so avoid redundant noise.
- Use stable, zero-padded indices for ordered variants and frames.
- Keep related state vocabulary consistent: `idle`, `walk`, `run`, `attack`,
  `hit`, `death`; `normal`, `hover`, `pressed`, `disabled`; `day`, `night`.
- Name texture maps by material role: `oak_bark_albedo.png`,
  `oak_bark_normal.png`, `oak_bark_roughness.png`.
- Name audio by gameplay role and event: `sfx_sword_impact_metal_01.wav`,
  `ambience_forest_night_loop.ogg`, `music_boss_phase_02_loop.ogg`.
- Name UI by component and state: `inventory_slot_hover.png`,
  `icon_health_potion_32.png`.
- Name animation frames with subject, action, view, and frame:
  `hero_run_side_03.png`, not `run_3.png` or `sprite_17.png`.
- Avoid unexplained adjectives, spaces, Unicode lookalikes, download IDs, version
  noise, `final`, `new`, `copy`, and opaque abbreviations.
- Keep the extension consistent with decoded content. Renaming is not conversion.
- Resolve case-folding collisions before materialization.

Before accepting a name, ask: could a new user infer what the asset is for, how it
differs from siblings, and whether it belongs in a sequence? If not, rename it or
improve the directory context.

## Sidecar Contract

Store metadata next to every accepted asset as `<filename>.asset.json`; for
`hero_run_side_03.png`, use `hero_run_side_03.png.asset.json`. Treat a tightly
coupled multi-file model as one logical bundle only when the catalog record lists
all dependencies.

```json
{
  "asset_id": "character.hero.run.side.03",
  "name": "Hero run side frame 03",
  "description": "Fourth side-view frame of the playable hero run cycle.",
  "category": "2d/characters",
  "tags": ["hero", "player", "run", "side-view", "animation-frame"],
  "technical_status": "ready",
  "license": {
    "status": "allowed",
    "spdx": "CC-BY-4.0",
    "author": "Example Artist",
    "attribution": "Example Artist, CC BY 4.0"
  },
  "source": {
    "url": "https://example.invalid/pack",
    "original_path": "Knight/Run (4).png",
    "retrieved_at": "2026-07-13",
    "sha256": "<source sha256>"
  },
  "usage": {
    "recommended_for": ["playable hero side-view run animation"],
    "avoid": ["portrait or standalone illustration"]
  },
  "relationships": {
    "animation_set": "character.hero.run.side",
    "sequence_index": 3,
    "next": "character.hero.run.side.04"
  },
  "import": {
    "filter": "nearest",
    "mipmaps": false,
    "pivot": [0.5, 1.0]
  }
}
```

### Retrieval Requirements

- `asset_id`: Assign a stable semantic ID. Do not rely on the path-derived
  fallback for a final accepted asset.
- `name`: Use a concise human label that distinguishes the asset from siblings.
- `description`: Explain both depicted content and gameplay/UI role; do not merely
  restate the filename.
- `category`: Use the normalized taxonomy.
- `tags`: Include selection traits not fully recoverable from the path, such as
  viewpoint, biome, faction, mood, material, state, weapon, UI role, loop, or
  animation action.
- `usage.recommended_for`: Include at least one concrete intended use. Add
  `usage.avoid` when a visually plausible use would be wrong.
- `technical_status`: Use `ready` only after applicable integrity, dependency, and
  quality checks pass. Use `review`, `conversion-required`, `quarantined`, or
  `unsupported` otherwise.
- `license.status`: Use `owned`, `cleared`, `allowed`, `public-domain`,
  `restricted`, or `unknown`. Record SPDX only when verified.
- `source`: Preserve original path and known URL, pack, author, retrieval date,
  and hash. Never fabricate missing provenance.
- `relationships`: Link frames, variants, layers, LODs, texture maps, model
  dependencies, matching UI states, and loop groups by asset ID.
- `import`: Record suggested Godot import intent. It is portable metadata, not an
  imported cache or proof of compatibility.

## Catalog Semantics

`build_asset_catalog.py` emits one record per asset with:

- identity and retrieval: `asset_id`, name, description, category, tags, usage;
- location: asset-root-relative `path` and portable library-root-relative
  `library_path`;
- integrity: format, media type, size, SHA-256, and technical metadata;
- decisions: technical, metadata, rights, and optional Godot compatibility status;
- context: license, source, relationships, import intent, and issues;
- eligibility: `ready_for_agent`, true only when technical status is `ready`,
  retrieval metadata is complete, rights permit use, and optional compatibility
  evidence has not failed.

Use JSONL as the complete retrieval source and Markdown as a bounded overview.
The path remains portable because it never assumes `res://` or a Godot project.
Godot compatibility uses `verified` for successful external imports,
`not_applicable` for Godot-native resources that do not use the external importer,
`not_tested` without target evidence, and `failed` for actual import failures.

## Agent Package Index

Generate `AGENTS.md` at the library root as the package-level AI entry point.
Build it from the final catalog so it stays synchronized with actual assets. It
must summarize the package's main uses, map every present category to the common
directory where that type is stored, show ready and total counts, link the catalog
files, and explain selection, dependency, import, and rights handling. Keep exact
per-asset metadata in JSONL and sidecars rather than duplicating it in this guide.

Useful query shapes:

```bash
jq -c 'select(.ready_for_agent and .category == "audio/sfx")' asset_catalog.jsonl
jq -r 'select(.usage.recommended_for[]? | contains("run animation")) | [.asset_id, .library_path] | @tsv' asset_catalog.jsonl
jq -r 'select(.tags | index("forest")) | [.asset_id, .description, .library_path] | @tsv' asset_catalog.jsonl
rg 'character\.hero|"animation_set":"character.hero' asset_catalog.jsonl
```

## Deduplication and Variants

- Use SHA-256 to collapse exact duplicates only after confirming metadata and
  rights are compatible. Retain the best provenance record and relevant aliases.
- Do not collapse visually similar files automatically. Different crops, alpha,
  compression, pivots, palettes, frames, or licenses can be meaningful variants.
- Choose a canonical asset using verified rights, technical quality, source
  resolution, clean alpha/audio, complete dependencies, and intended use.
- Record replacements and variant relationships instead of silently deleting
  evidence from the audit.
