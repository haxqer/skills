---
name: "game-asset-gen"
description: "Generate 2D game art assets — characters, monsters, NPCs, equipment, items, VFX, tiles, UI icons, and animation frame sequences — through OpenAI-compatible (gpt-image-2, gpt-image-1, dall-e) or Gemini image backends. Use when Codex needs to create or iterate on sprites and game-ready art with a configurable provider/base-url/model, transparent or chroma-key cutouts, and outputs prepared for downstream cutout (抠图), Spine skeletal animation, and paper-doll (纸娃娃) equipment-layering systems."
---

# Game Asset Generation

Use this skill to produce 2D game art and short animation sets, then prepare it
for downstream pipelines: cutout (抠图), Spine skeletal animation, and paper-doll
(纸娃娃) equipment layering. The bundled `scripts/` cover multi-provider image
generation, image editing for consistency, batch jobs, and background removal.

The generator is **provider-agnostic**. The same CLI talks to:

- **OpenAI-compatible Images API** — `POST {base}/images/generations`, `/images/edits`
  (models like `gpt-image-2`, `gpt-image-1`, `dall-e-3`).
- **OpenAI-compatible Responses API** — `POST {base}/responses` with the
  `image_generation` tool.
- **Gemini** — `google-genai` SDK (`gemini-2.5-flash-image`, Imagen).

Custom **base URL**, **model**, and **API key** are all configurable, so it works
against the real OpenAI API, Google, or any OpenAI-compatible gateway/relay.

## Start

1. **Pick the backend and model.** Default is `auto`:
   - model starts with `gpt-image` / `dall-e` → `openai`
   - model starts with `gemini` / `imagen` → `gemini`
   - a `--base-url` is set → `openai` (assume an OpenAI-compatible gateway)
   - otherwise → `gemini`
   Override with `--backend openai|openai-responses|gemini`.
2. **Confirm the asset category:** character/player, monster, NPC, equipment,
   item, effect, tile, decoration, UI, or background.
3. **Confirm the deliverable:** one image, a frame set, an edit/iteration on
   existing art, or layered parts for paper-doll / Spine.
4. **Decide transparency strategy** (this drives cutout, Spine, paper-doll):
   - OpenAI `gpt-image-*`: request `--transparent` (default) → real alpha PNG,
     **no chroma key needed**.
   - Gemini (no transparent mode): generate on flat `#00FF00`, then chroma-key
     or run `scripts/smart_remove_bg.py`.
5. **Set up credentials** (first match wins):
   - OpenAI key: `--api-key`, `OPENAI_API_KEY`, `IMAGE_API_KEY`
   - OpenAI base: `--base-url`, `OPENAI_BASE_URL`, `IMAGE_API_BASE_URL`
     (default `https://api.openai.com/v1`)
   - Gemini key: `--api-key`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `IMAGE_API_KEY`
   - Default model: `--model`, `IMAGE_MODEL`
   The CLI also auto-loads a nearby `.env` (walks up from the working directory).
6. **Read only the references you need:**
   - `references/api-backends.md` — provider config, transparent vs chroma-key,
     custom URL/model, env keys, troubleshooting
   - `references/pipeline-spine-paperdoll.md` — cutout → Spine → paper-doll
     workflow, layer separation, anchor/canvas rules
   - `references/prompt-templates.md` — copyable prompt shapes by category
   - `references/animation-frames.md` — per-frame pose guidance
   - `references/naming-conventions.md` — file/directory conventions
   - `references/asset-catalog.md` — sample backlog / inventory alignment

## Working Mode

- **Consistency is the core challenge** for game art. Keep one stable subject
  description block across all frames or equipment layers; vary only pose,
  motion, VFX, or the single swapped part.
- For tight consistency, prefer the **`edit` subcommand**: feed the base/reference
  image plus a change instruction instead of regenerating from scratch. This is
  how paper-doll layers and animation frames stay on-model.
- Always state in the prompt: canvas/size, background mode (transparent or flat
  `#00FF00`), outline/style anchor, subject, and an avoid clause.
- Prefer readable silhouettes over detail. If a sprite reads muddy at the target
  size, simplify the prompt rather than adding detail.
- Treat backgrounds (parallax, scenes) differently from sprites: larger aspect
  ratios, and usually skip cutout entirely.

## Workflow

1. **Lock the deliverable.** Output path, naming pattern, frame/layer count, and
   whether the result is a raw generation, a cleaned cutout, or a final asset.
   Read `references/naming-conventions.md` if fitting an existing tree.

2. **Build the prompt** from `references/prompt-templates.md`. Include: style
   anchor, canvas/size, background mode, subject, pose/frame action, consistency
   instruction for multi-frame work, and an avoid clause (blur, realism,
   gradients, watermarks).

3. **Generate.**

   OpenAI `gpt-image-2`, transparent PNG (no chroma key needed):
   ```bash
   python "$ASSET_GEN" generate \
     --backend openai --model gpt-image-2 \
     --prompt "front-facing RPG hero base body, neutral T-pose, clean cel-shaded, transparent background, no ground shadow" \
     --out art/hero/base.png --size 1024x1024
   ```

   Custom OpenAI-compatible gateway:
   ```bash
   python "$ASSET_GEN" generate \
     --base-url https://my-gateway.example.com/v1 --model gpt-image-2 \
     --prompt "..." --out out.png
   ```

   OpenAI Responses API (`image_generation` tool):
   ```bash
   python "$ASSET_GEN" generate \
     --backend openai-responses --model gpt-5 \
     --prompt "..." --out out.png
   ```

   Gemini pixel sprite on green, auto chroma-keyed + downscaled:
   ```bash
   python "$ASSET_GEN" generate \
     --backend gemini --model gemini-2.5-flash-image \
     --prompt "chibi retro pixel art warrior, 48x48 canvas, 1px dark outline, solid flat pure green (#00FF00) background, no shadow" \
     --out art/player/warrior/idle_00.png --downscale 48
   ```

4. **Edit for consistency / paper-doll.** Keep pose and anchor stable by editing
   the base image instead of regenerating:
   ```bash
   python "$ASSET_GEN" edit \
     --backend openai --model gpt-image-2 \
     --image art/hero/base.png \
     --prompt "the exact same character in the same pose and position, now wearing steel plate armor; keep transparent background" \
     --out art/hero/equip/armor_steel.png
   ```
   OpenAI edits accept an optional `--mask` (transparent area = region to change)
   and multiple `--image` inputs for composition.

5. **Batch** a frame set or asset list from JSONL:
   ```bash
   python "$ASSET_GEN" generate-batch \
     --input tmp/frames.jsonl --out-dir tmp/raw/ --concurrency 3
   ```
   Each JSONL line may override `backend`, `model`, `out_name`, `prompt`,
   `input_images`, `background`, `chroma_key`, `downscale`, `aspect_ratio`,
   `size`, `fuzz`.

6. **Cutout (抠图).** For green/opaque outputs, produce clean transparent PNGs:
   ```bash
   python "$SMART_BG" --input-dir tmp/raw/ --output-dir art/player/warrior/ --fuzz 100 --downscale 48
   ```
   `smart_remove_bg.py` auto-detects the dominant corner color, so it works for
   green screens **and** other solid backgrounds (white, etc.). Transparent
   OpenAI outputs usually need no cutout at all.

7. **Validate at final size.** Check silhouette readability, no background
   fringing, intact outline, and correct alpha. For animation, preview at
   `8–12 FPS`; for paper-doll/Spine, confirm every layer shares the same canvas,
   anchor point, and registration. See `references/pipeline-spine-paperdoll.md`.

## Scripts

- `scripts/generate_asset.py`
  - `generate` — single prompt → image (any backend)
  - `edit` — image(s) + prompt → image (consistency, paper-doll layers, masking)
  - `generate-batch` — JSONL-driven batch
  - `chroma-key` / `chroma-key-dir` — basic green-screen removal
- `scripts/smart_remove_bg.py` — flood-fill cutout that auto-detects the
  background color (green or otherwise) and resists halos; optional downscale.

If dependencies are missing, use `uv` for one-shot runs. The OpenAI backends only
need `Pillow` (HTTP via stdlib); Gemini also needs `google-genai`:
```bash
uv run --with Pillow python "$ASSET_GEN" generate --backend openai --model gpt-image-2 --prompt "..." --dry-run
uv run --with google-genai --with Pillow python "$ASSET_GEN" generate --backend gemini --prompt "..." --dry-run
```

## Model Notes

- **OpenAI `gpt-image-2` / `gpt-image-1`**: native transparent background, multi-
  image edits, masking — best for paper-doll, Spine parts, and clean cutouts.
- **`dall-e-3`**: no transparency; generate then cutout via `smart_remove_bg.py`.
- **Gemini `gemini-2.5-flash-image`**: fast, strong for pixel art; no transparent
  mode, so use the green-screen + chroma-key path. Good default for cheap
  iteration; reserve higher-quality models for hero assets and final art.

## References

- `references/api-backends.md`: provider/url/model/env config and troubleshooting
- `references/pipeline-spine-paperdoll.md`: cutout → Spine → paper-doll pipeline
- `references/prompt-templates.md`: copyable prompt recipes by category
- `references/animation-frames.md`: frame-by-frame pose guidance
- `references/naming-conventions.md`: naming rules and directory structure
- `references/asset-catalog.md`: sample asset inventory for backlog planning

## Common Failure Modes

- Changing the subject design between frames/layers instead of only the pose or
  swapped part. Use `edit` from a fixed base to stay on-model.
- Adding gradients, soft shadows, or ground planes that break cutout and pixel
  reads, or that misalign paper-doll layers.
- Using Gemini and expecting a transparent PNG — it has no transparent mode;
  generate on green and cut out.
- Forgetting `--size`/canvas consistency, so paper-doll/Spine layers don't
  register to the same anchor.
- Generating straight into the final asset directory before validating raw
  output and alpha quality.
- Hardcoding `https://api.openai.com` when the user has a custom gateway — pass
  `--base-url` or set `OPENAI_BASE_URL`.

## Check Before You Finish

- Output paths and file names match the expected convention.
- Final sprites are transparent unless intentionally a background/full scene.
- Asset reads clearly at its final size.
- Multi-frame sets and paper-doll/Spine layers share canvas, anchor, proportions,
  palette, and outline weight.
- Requested batches include all required states/frames/layers.
