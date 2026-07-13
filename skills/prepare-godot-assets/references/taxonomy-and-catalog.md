# Asset Taxonomy and Agent Catalog

Use this reference when mapping source files to stable project paths and when
writing metadata that lets an AI agent select assets without opening every file.

## Directory Taxonomy

Adapt to an existing project. For a new library, use this shallow baseline:

```text
assets/
  art/
    characters/<character_id>/{animations,portraits,parts}/
    environments/{backgrounds,props,tilesets}/
    ui/{controls,icons,panels}/
    vfx/
  audio/{ambience,music,sfx,voice}/
  fonts/
  models/{characters,environments,props}/
  materials/{textures,resources}/
  shaders/
  data/
```

Keep the tree task-oriented and shallow enough for scanning. Group a cohesive 3D
bundle or asset pack below its owning category when relative dependencies matter.
Do not create one directory per file and do not mirror arbitrary download-site
folders.

## Naming Rules

- Use lowercase ASCII paths. Use `snake_case` for semantic file names and stable,
  zero-padded numbers for ordered frames: `run_00.png`, `run_01.png`.
- Restrict destinations to letters, digits, `_`, `-`, `.`, and `/`. Avoid spaces,
  punctuation, Unicode lookalikes, version noise, `final`, `copy`, and download IDs.
- Name by role and identity, not appearance alone: `wooden_door_closed.png`, not
  `brown_thing_2.png`.
- Keep related animation states under one identity and use the same state names
  across characters when practical: `idle`, `walk`, `run`, `attack`, `hit`, `death`.
- Encode resolution or variant only when it changes selection behavior:
  `icon_inventory_32.png`, `background_forest_night.png`.
- Keep the extension consistent with decoded content. Renaming is not conversion.
- Resolve case-folding collisions before materialization. Paths must be unique when
  compared case-insensitively for cross-platform projects.

## Sidecar Contract

Store optional metadata next to an asset as `<filename>.asset.json`; for
`hero.png`, use `hero.png.asset.json`. The materializer can create this sidecar
from each plan row's `metadata` object.

```json
{
  "asset_id": "character.hero.idle.00",
  "name": "Hero idle frame 00",
  "description": "Front-facing idle frame for the playable knight.",
  "category": "art/characters",
  "tags": ["hero", "knight", "idle", "front"],
  "license": {
    "status": "allowed",
    "spdx": "CC-BY-4.0",
    "author": "Example Artist",
    "attribution": "Example Artist, CC BY 4.0"
  },
  "source": {
    "url": "https://example.invalid/pack",
    "original_path": "Knight/Idle (1).png",
    "retrieved_at": "2026-07-13"
  },
  "usage": {
    "recommended_for": ["player idle animation"],
    "avoid": ["large portrait"]
  },
  "relationships": {
    "animation_set": "character.hero.idle",
    "next": "character.hero.idle.01"
  },
  "import": {
    "filter": "nearest",
    "mipmaps": false,
    "pivot": [0.5, 1.0]
  }
}
```

### Required Semantics

- `asset_id`: Prefer a project-stable semantic ID. The catalog generates a
  deterministic fallback, but that fallback changes when path or content changes.
- `description`: State what the asset depicts and its gameplay/UI role. Do not
  repeat the filename.
- `category`: Use the normalized taxonomy. Correct an inferred category in the
  sidecar when filename heuristics are wrong.
- `tags`: Add semantic traits not recoverable from the path: viewpoint, biome,
  faction, mood, material, state, weapon, UI role, or animation action.
- `license.status`: Use `owned`, `cleared`, `allowed`, `public-domain`,
  `restricted`, or `unknown`. Record SPDX only when verified.
- `source`: Preserve URL, author, pack, original path, retrieval date, and source
  hash where available. Never fabricate missing provenance.
- `usage`: Record intended and prohibited uses that improve Agent selection.
- `relationships`: Link frames, variants, layers, LODs, matching normals, model
  dependencies, and audio loops by asset ID.
- `import`: Record intent useful to project code or an import-settings pass. This
  metadata does not replace Godot's actual importer configuration.

## Catalog Semantics

`build_asset_catalog.py` emits one JSON object per line with:

- identity: `asset_id`, name, description, category, tags;
- location: normalized path and actual `res://` path;
- integrity: format, media type, byte size, SHA-256, technical metadata;
- readiness: technical status, rights status, importer evidence, issues, and the
  derived `ready_for_agent` boolean;
- context: license, source, usage, relationships, and import intent.

Treat JSONL as the retrieval source and the Markdown file as a bounded overview.
Filter `ready_for_agent == true` for automatic selection. Permit review or unknown
rights only when the user explicitly broadens the policy; never hide that status.

Useful query shapes:

```bash
jq -c 'select(.ready_for_agent and .category == "audio/sfx")' asset_catalog.jsonl
jq -r 'select(.tags | index("forest")) | [.asset_id, .res_path] | @tsv' asset_catalog.jsonl
rg 'character\.hero|"animation_set":"character.hero' asset_catalog.jsonl
```

## Deduplication and Variants

- Use SHA-256 to collapse exact duplicates after confirming metadata and rights are
  compatible. Retain the best provenance record and all relevant aliases.
- Do not collapse visually similar files automatically. Different crops, alpha,
  compression, pivots, palettes, frames, or licenses can be meaningful variants.
- Choose a canonical asset using verified rights, technical quality, source
  resolution, clean alpha/audio, complete dependencies, and project fit.
- Record replacements and variant relationships instead of silently deleting
  evidence from the audit.
