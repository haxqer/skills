---
name: "game-asset-gen"
description: "Generate pixel-art game assets and frame sequences for MapleStory-style or similar 2D platformers. Use when Codex needs to create or iterate on 48x48 sprites, monsters, NPCs, items, effects, tiles, decorations, or UI icons with a pure green (#00FF00) chroma-key background during generation and transparent final PNG output via the bundled Gemini-based scripts."
---

# Game Asset Generation

Use this skill to produce retro pixel-art assets and short animation sets for a
side-scrolling RPG or platformer. The bundled `scripts/` cover Gemini-based
image generation, batch jobs, basic chroma keying, and a smarter halo-resistant
background remover for production cleanup.

## Start

- Confirm the asset category first: player, monster, NPC, item, effect, tile,
  decoration, UI, or background.
- Confirm whether the user needs one image, a full frame set, or iteration on
  existing art.
- Default sprite target is `48x48` PNG with a transparent final background. Use
  flat `#00FF00` only as the generation background unless the asset itself is a
  background.
- Preserve the project's existing palette, proportions, and silhouette rules if
  a repository already contains art. If there is no established style, default
  to chibi retro pixel art with a limited palette and a `1px` dark outline.
- Require `GEMINI_API_KEY` before live generation. The bundled CLI looks for a
  `.env` by walking upward from the current working directory first, then from
  the script location. An explicit environment variable still takes precedence.
- Read only the references needed for the task:
  - `references/prompt-templates.md` for copyable prompt shapes
  - `references/animation-frames.md` for per-frame pose guidance
  - `references/naming-conventions.md` for file and directory conventions
  - `references/asset-catalog.md` only when the user needs a sample backlog or
    wants to align with an existing MapleStory-style inventory

## Working Mode

- Keep one stable character or monster description block across all frames in an
  animation. Vary only pose, motion, or VFX state.
- Always state the canvas, background color, outline rule, and style anchor in
  the prompt.
- Prefer readable silhouettes over extra detail. If the sprite becomes muddy at
  `48x48`, simplify the prompt instead of adding detail.
- Treat backgrounds differently from sprites: backgrounds may use larger aspect
  ratios and usually should skip chroma keying.

## Workflow

1. Lock the deliverable.
- Decide the output path, naming pattern, frame count, and whether the result is
  a raw generation, a cleaned sprite, or a final in-game asset.
- If the asset must fit an existing project tree, read
  `references/naming-conventions.md` before generating.

2. Build the prompt.
- Start from `references/prompt-templates.md`.
- Include these prompt components:
  - style anchor such as `chibi retro pixel art, MapleStory v62 aesthetic`
  - canvas such as `48x48 pixel canvas`
  - background such as `solid flat pure green (#00FF00), no shadows, no ground`
  - subject description
  - pose or frame-specific action
  - consistency instruction for multi-frame work
  - avoid clause for blur, realism, gradients, and watermarks

3. Generate raw outputs.
- Use `scripts/generate_asset.py` for single assets or JSONL-driven batch jobs.
- For production sprite work, prefer `--no-chroma-key` and run
  `scripts/smart_remove_bg.py` afterward. The built-in chroma key path is fine
  for quick iteration but is less reliable around green halos.

```bash
python "$ASSET_GEN" generate \
  --prompt "chibi retro pixel art warrior, MapleStory v62 style. 48x48 pixel canvas. 1px dark outline. Pose: standing neutral, facing right. Background: solid flat pure green (#00FF00), no shadows, no ground. Avoid: realistic proportions; blurry edges; watermark." \
  --out tmp/raw/idle_00.png \
  --no-chroma-key
```

```bash
python "$ASSET_GEN" generate-batch \
  --input tmp/frames.jsonl \
  --out-dir tmp/raw/ \
  --concurrency 3 \
  --no-chroma-key
```

4. Clean and downscale.
- Use `scripts/smart_remove_bg.py` as the default cleanup path for character,
  monster, NPC, item, and VFX sprites generated against green backgrounds.
- Keep the simpler `chroma-key` commands in `generate_asset.py` for quick local
  cleanup or cases where halo quality is not critical.

```bash
python "$SMART_BG" \
  --input-dir tmp/raw/ \
  --output-dir art/player/warrior/ \
  --fuzz 100 \
  --downscale 48
```

5. Validate at final size.
- Check silhouette readability at the final output size, not only at the raw
  generated size.
- Confirm there is no green fringing, unexpected transparency loss, or outline
  damage.
- For animation, preview frames at roughly `8-12 FPS` and verify consistent
  proportions, anchor points, and pose progression.

## Scripts

- `scripts/generate_asset.py`
  - `generate`: single prompt to PNG
  - `generate-batch`: JSONL-driven batch generation
  - `chroma-key`: basic green-screen removal for one file
  - `chroma-key-dir`: basic green-screen removal for one directory
- `scripts/smart_remove_bg.py`
  - flood-fill background removal that is safer for Gemini-style green halos
  - optional nearest-neighbor downscaling after cleanup

If dependencies are not installed, prefer `uv` for one-shot execution:

```bash
uv run --with google-genai --with Pillow python "$ASSET_GEN" generate --prompt "..." --dry-run
```

## Model Notes

- The script default is `gemini-2.5-flash-image`.
- Use faster or cheaper models for prompt iteration and layout exploration.
- Use higher-quality Gemini image models only when the user explicitly wants a
  hero asset, polished icon, or final promotional art.

## References

- `references/prompt-templates.md`: copyable prompt recipes by asset category
- `references/animation-frames.md`: frame-by-frame pose guidance
- `references/naming-conventions.md`: naming rules and directory structure
- `references/asset-catalog.md`: sample asset inventory for backlog planning or
  alignment with an existing MapleStory-style content set

## Common Failure Modes

- Changing the character design from frame to frame instead of only changing the
  pose.
- Adding gradients, shadow planes, or soft edges that break the pixel-art read.
- Generating directly to the final asset directory before validating raw output.
- Relying on simple chroma keying when the generated outline still carries a
  dark green halo.
- Using inconsistent naming, frame suffixes, or directory placement.
- Over-specifying prompts with conflicting camera, pose, and lighting rules.

## Check Before You Finish

- Confirm the output path and file names match the expected asset convention.
- Confirm the final sprite is transparent unless the asset is intentionally a
  background or other non-cutout image.
- Confirm the asset still reads clearly at `48x48`.
- Confirm multi-frame sets keep the same proportions, palette, and outline
  weight.
- Confirm any requested batch output includes all required states and frame
  counts before finishing.
