# Pipeline: Cutout → Spine → Paper-Doll (纸娃娃)

Game assets are rarely used as raw generated images. They feed downstream
systems that demand **transparency, consistent registration, and separated
parts**. Plan for this before generating, not after.

## The end-to-end flow

```
generate ──► cutout (抠图) ──► normalize canvas/anchor ──► slice into parts ──► import to Spine / paper-doll
```

1. **Generate** with a transparency strategy:
   - OpenAI `gpt-image-*` → `--transparent` (real alpha, skip cutout).
   - Gemini / `dall-e` → flat `#00FF00` (or any solid bg) → cut out.
2. **Cutout (抠图)** to clean transparent PNGs:
   - Already transparent OpenAI output → usually no cutout.
   - Otherwise `scripts/smart_remove_bg.py` (auto-detects bg color, halo-safe)
     or `generate_asset.py chroma-key` for quick green removal.
3. **Normalize canvas + anchor** so every frame/part shares one coordinate space.
4. **Separate parts** (for Spine bones / paper-doll slots).
5. **Import** to the target tool.

## Registration: the non-negotiable rule

Every frame and every layer must share the **same canvas size and the same
anchor (pivot) position**. If the head sits at different pixel coordinates across
two generations, Spine bones and paper-doll overlays will jitter.

- Fix one canvas size up front (e.g. `1024x1024`, or `48x48` for pixel art).
- Keep the subject centered with consistent ground/hip position.
- Generate frames and equipment as **edits of one base image** rather than fresh
  generations — this is the single most effective way to hold registration.

```bash
# 1. Make the canonical base pose once.
python generate_asset.py generate --backend openai --model gpt-image-2 \
  --prompt "RPG hero base body, neutral A-pose, centered, feet on bottom edge, transparent background, flat cel shading, no props" \
  --out art/hero/base.png --size 1024x1024

# 2. Derive every variant by editing the base (same pose, same position).
python generate_asset.py edit --backend openai --model gpt-image-2 \
  --image art/hero/base.png \
  --prompt "the exact same character in the exact same pose and position; only add steel plate armor; transparent background" \
  --out art/hero/equip/armor_steel.png
```

## Paper-doll (纸娃娃) layering

A paper-doll character is composited from a fixed base plus swappable equipment
layers (hair, face, top, bottom, weapon, hat, cape, …), each occupying a known
slot and drawn in a fixed z-order.

### Approach A — full-body layers (simplest)

Each layer is a full-canvas transparent PNG aligned to the base. The base shows
through wherever a layer is transparent. Composite by stacking in z-order.

- Pros: dead simple registration, no per-part slicing.
- Cons: a layer can only cover, not reveal occluded geometry; many near-identical
  full frames.

Generate each slot by editing the base with **only that slot's item visible** and
everything else transparent:
```bash
python generate_asset.py edit --image art/hero/base.png \
  --prompt "same pose/position; show ONLY a wizard hat fitted to the head; everything else fully transparent" \
  --out art/hero/layers/hat_wizard.png
```

Suggested z-order (back to front):
```
cape → back-weapon → body(base) → bottom → top → arms → face → hair → hat → main-weapon
```

### Approach B — masked region edits

Use OpenAI `--mask` to constrain changes to a slot region while keeping the rest
pixel-identical to the base. The mask is a PNG where the **transparent area marks
what may change**.
```bash
python generate_asset.py edit --image art/hero/base.png --mask masks/head.png \
  --prompt "replace the headgear with a golden crown" --out art/hero/layers/crown.png
```

### Layer naming

Extend `naming-conventions.md` with slot-aware names so a paper-doll loader can
map files to slots and z-order:
```
art/hero/base.png
art/hero/layers/{slot}_{variant}.png      # hair_short, face_smile, top_leather,
                                          # bottom_cloth, hat_wizard, cape_red,
                                          # weapon_sword, weapon_back_bow
```
Keep one `{slot}` vocabulary across the project; it doubles as the z-order key.

## Spine (skeletal 2D animation)

Spine animates **separated body parts** attached to bones, not baked frames. Feed
it transparent part PNGs, one image per attachment.

- Generate the character, then split into parts: head, torso, upper-arm-L,
  lower-arm-L, hand-L (and R), thigh/shin/foot L/R, plus props.
- Each part is its own transparent PNG, ideally on its own small canvas with a
  recorded pivot, or on the shared full canvas (then trimmed in Spine).
- Keep a neutral, limbs-separated source pose (A-pose / T-pose) so parts don't
  overlap and are easy to isolate.
- Prompt the model to render parts cleanly separable, or generate the full body
  and cut parts manually/with masks.

```bash
# A-pose source with clearly separated limbs, transparent bg.
python generate_asset.py generate --backend openai --model gpt-image-2 \
  --prompt "side-scroller hero, strict T-pose, arms and legs fully separated and not overlapping, flat shading, transparent background, even lighting, no cast shadow" \
  --out art/hero/spine_source.png --size 1024x1536
```

Spine import checklist:
- One PNG per attachment, all sharing the project's pixel scale.
- Consistent pivots; record them or trim transparent margins consistently.
- No baked shadows or motion blur (they break clean bone deformation).
- Power-of-two-friendly atlas sizes if the runtime needs them.

## Frame animation (sprite sheets)

For classic frame animation instead of skeletal, generate each frame as an edit
of the previous/base pose (see `animation-frames.md`), cut out, downscale, and
keep `{state}_{frame:02d}.png` naming. Preview at 8–12 FPS to verify the anchor
and proportions hold across frames.

## Quality gates before handoff

- Transparency is clean: no background fringe/halo, no semi-transparent speckle
  in solid areas.
- All frames/layers/parts share canvas size and anchor.
- Z-order is documented for paper-doll; pivots are documented for Spine.
- No baked shadows, gradients on the cutout edge, or watermarks.
- File names follow a single slot/state vocabulary the loader can parse.
