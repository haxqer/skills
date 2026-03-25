# Prompt Templates for Game Asset Generation

Ready-to-use prompt recipes for a MapleStory-style 2D platformer. Copy, fill in the bracketed placeholders, and run via the bundled `scripts/generate_asset.py` CLI.

All prompts include the mandatory style anchor and green background directive.

## Contents

- `Character Sprites`
- `Monster Sprites`
- `Equipment / Item Icons`
- `NPC Sprites`
- `Effect / VFX Frame Sequences`
- `Tiles & Decorations`
- `UI Skill Icons`
- `Backgrounds`
- `Batch Generation`

---

## Character Sprites (Player Classes)

### Single Frame (any pose)

```
Use case: pixel-art-sprite
Asset type: player character animation frame
Primary request: chibi retro pixel art character, MapleStory v62 sprite style.
Character: [class name] class — [describe outfit, weapon, hair color, distinguishing features].
48×48 pixel canvas. 1px dark outline. Limited color palette, no anti-aliasing, no dithering.
Pose: [describe exact pose — e.g. "standing neutral, arms at sides, facing right"].
Background: solid flat pure green (#00FF00), no shadows on background, no ground, character floating centered.
Constraints: maintain pixel-perfect crispness; strong readable silhouette at small size.
Avoid: realistic proportions; soft gradients; blurry edges; background elements; watermark.
Quality: high
```

### Full Animation Set (batch JSONL pattern)

For each frame, keep the **Character** block identical and vary only the **Pose** line:

| Frame | Pose description |
|-------|-----------------|
| `idle_00` | Standing neutral, arms at sides, facing right, weight on both feet |
| `idle_01` | Slight breathing shift — one hand slightly raised or head tilted |
| `run_00` | Right foot forward, left arm forward, body leaning right |
| `run_01` | Transition mid-stride, both feet near ground, neutral arms |
| `run_02` | Left foot forward, right arm forward, body leaning right (mirror of 00) |
| `run_03` | Transition mid-stride returning to start (mirror of 01) |
| `attack_00` | Wind-up pose — weapon pulled back, body coiled |
| `attack_01` | Swing follow-through — weapon extended forward, body stretched |
| `jump_00` | Upward leap — arms up, legs tucked, slight upward arc |
| `fall_00` | Falling — arms out to sides, legs dangling, looking down |
| `hurt_00` | Flinching backward — body recoiled, head tilted, one eye closed |
| `death_00` | Collapsed flat on ground, eyes X-shaped or ghost departing above body |
| `climb_00` | Gripping rope/ladder — right hand up, left hand down, body straight |
| `climb_01` | Alternate grip — left hand up, right hand down |

---

## Monster Sprites

### Single Monster Frame

```
Use case: pixel-art-sprite
Asset type: monster sprite animation frame
Primary request: chibi retro pixel art monster, MapleStory v62 sprite style.
Monster: [name] — [describe body shape, color, features, size relative to canvas].
48×48 pixel canvas. 1px dark outline. Limited color palette, no anti-aliasing.
Pose: [describe exact pose].
Expression: [cute-menacing / angry / sleepy / alert].
Background: solid flat pure green (#00FF00), no shadows, no ground, monster floating centered.
Constraints: strong silhouette; recognizable at small size.
Avoid: realistic proportions; blurry edges; background elements; watermark.
Quality: high
```

### Monster Animation Poses

| Frame | Pose description |
|-------|-----------------|
| `idle_00` | Default resting pose, facing right |
| `idle_01` | Slight bounce or breathing variation from idle_00 |
| `hop_00` | Compressed low, about to hop — body squished |
| `hop_01` | Extended upward in mid-hop — body stretched |
| `hurt_00` | Knocked back, flashing — body tilted, squished expression |
| `death_00` | Flattened / exploding / dissolving into particles |

### Boss Monster Variations

Bosses may use the same template with larger emphasis on detail. Consider adding:

| Frame | Pose description |
|-------|-----------------|
| `attack_00` | Boss wind-up — telegraphing attack |
| `attack_01` | Boss strike — attack extended |
| `skill_00` | Charging special ability — glowing aura |
| `skill_01` | Releasing special ability |
| `enrage_00` | Powered up — red tint, larger presence |

---

## Equipment / Item Icons

```
Use case: pixel-art-icon
Asset type: game inventory item icon
Primary request: chibi retro pixel art item icon, MapleStory v62 style.
Item: [name] — [describe the item: shape, material, color, glow effects].
48×48 pixel canvas. Centered. 1px dark outline on the item.
Background: solid flat pure green (#00FF00).
Style: clean, iconic, recognizable at small size. Slight metallic sheen or magical glow if appropriate.
Constraints: single item only; no text; no labels.
Avoid: clutter; multiple items; realistic proportions; watermark.
Quality: high
```

### Common Item Types

| Category | Example prompt detail |
|----------|----------------------|
| Sword | "short silver sword with brass crossguard, slight gleam on blade" |
| Staff | "wooden staff topped with glowing blue crystal orb" |
| Bow | "curved wooden bow with taut string, simple design" |
| Dagger | "twin daggers with dark metal blades, wrapped handles" |
| Potion (red) | "round glass bottle with red liquid, cork stopper, small heart symbol" |
| Potion (blue) | "round glass bottle with blue liquid, cork stopper, small star symbol" |
| Scroll | "rolled parchment scroll with wax seal, slightly unfurled" |
| Coin | "shiny gold coin with maple leaf imprint" |
| Helmet | "iron knight helmet with visor, small plume" |
| Shield | "round wooden shield with metal rim and emblem" |
| Cape | "flowing dark cape, slightly billowing" |
| Ring | "gold ring with small gem setting" |

---

## NPC Sprites

```
Use case: pixel-art-sprite
Asset type: NPC idle animation frame
Primary request: chibi retro pixel art NPC character, MapleStory v62 style.
NPC: [role] — [describe appearance, outfit, accessories, expression].
48×48 pixel canvas. 1px dark outline. Limited color palette.
Pose: [idle_00: default stand / idle_01: subtle variation].
Background: solid flat pure green (#00FF00), no shadows, no ground, NPC floating centered.
Constraints: NPC should look friendly and approachable (or stern for trainers).
Avoid: combat poses; realistic proportions; watermark.
Quality: high
```

### Existing NPC Types

| NPC | Appearance notes |
|-----|-----------------|
| Shopkeeper | Apron, friendly smile, maybe holding a wand or item |
| Healer | White/green robes, gentle glow, staff or book |
| Warrior Trainer | Heavy armor, serious expression, large weapon |
| Wizard | Pointed hat, flowing robes, magic aura |

---

## Effect / VFX Frame Sequences

```
Use case: pixel-art-vfx
Asset type: visual effect animation frame
Primary request: pixel art visual effect, MapleStory v62 style.
Effect: [name] — frame [N] of [total] — [describe this specific frame in the sequence].
48×48 pixel canvas. Bold, bright colors. Slight glow.
Background: solid flat pure green (#00FF00).
Constraints: effect should be visually impactful even at small size; semi-transparent elements ok.
Avoid: realistic effects; photograph-like; watermark.
Quality: high
```

### VFX Sequence Examples

**Slash (3 frames)**:
- Frame 00: Small curved slash arc, white-blue, just starting
- Frame 01: Full arc expanded, bright center with trailing edge
- Frame 02: Fading dissipating arc, particles scattering

**Death Poof (3 frames)**:
- Frame 00: Subject beginning to crack/flash white
- Frame 01: Explosion of particles, star-shaped burst
- Frame 02: Scattered particles fading, small sparkles remaining

**Item Pickup Glow (3 frames)**:
- Frame 00: Small sparkle ring forming at center
- Frame 01: Expanding golden ring with upward particles
- Frame 02: Burst of light with floating sparkle particles fading

**Level Up (3 frames)**:
- Frame 00: Column of golden light starting at bottom
- Frame 01: Full column with expanding rings and rising sparkles
- Frame 02: Burst at top, particles showering outward

---

## Tiles & Decorations

```
Use case: pixel-art-tile
Asset type: tileable game tile / decoration sprite
Primary request: retro pixel art [tile/decoration], MapleStory v62 style.
Subject: [describe — e.g. "grass-topped dirt block" or "flowering bush"].
48×48 pixel canvas. 1px outline where appropriate.
Background: solid flat pure green (#00FF00).
Constraints: [if tile: seamless edges on left-right or top-bottom as needed].
Avoid: realistic textures; watermark.
Quality: high
```

---

## UI Skill Icons

```
Use case: pixel-art-icon
Asset type: skill icon for quickbar/skill panel
Primary request: retro pixel art skill icon, MapleStory v62 style.
Skill: [name] — [describe the visual metaphor: element, weapon motion, aura type].
48×48 pixel canvas. Bold, iconic, readable at small size.
Background: solid flat pure green (#00FF00).
Style: painterly pixel art with slight glow/energy feel. Dark border frame.
Constraints: single clear focal element; no text.
Avoid: clutter; realistic style; watermark.
Quality: high
```

---

## Backgrounds (exception: larger canvas)

Backgrounds break the 48×48 rule and use wider canvases.

```
Use case: pixel-art-background
Asset type: parallax background layer
Primary request: retro pixel art background layer, MapleStory v62 style.
Scene: [describe — e.g. "distant rolling hills with soft clouds" or "dense forest canopy"].
Canvas: [specify size, e.g. 960×540 or 1920×1080].
Style: pixel art with limited palette, flat shading, parallax-ready.
Depth: [far / mid / near layer].
Constraints: tileable horizontally if possible; no foreground objects.
Avoid: realistic gradients; photographic style; watermark.
Quality: high
```

---

## Batch Generation: Full Character Set Example

To generate all 14 frames for a new player class, build a JSONL file:

```jsonl
{"prompt":"chibi retro pixel art character, MapleStory v62 sprite style. Character: Pirate class — bandana, open vest, cutlass at hip, confident grin. 48x48 pixel canvas. 1px dark outline. Pose: standing neutral, arms at sides, facing right, weight on both feet. Background: solid flat pure green (#00FF00), no shadows, character floating centered. Avoid: realistic proportions; blurry edges; watermark.","out_name":"idle_00.png"}
{"prompt":"chibi retro pixel art character, MapleStory v62 sprite style. Character: Pirate class — bandana, open vest, cutlass at hip, confident grin. 48x48 pixel canvas. 1px dark outline. Pose: slight breathing shift, one hand on hip, head tilted slightly. Background: solid flat pure green (#00FF00), no shadows, character floating centered. Avoid: realistic proportions; blurry edges; watermark.","out_name":"idle_01.png"}
```

Continue for all 14 poses. Then run:

```bash
# Generate all frames
python "$ASSET_GEN" generate-batch \
  --input tmp/frames.jsonl \
  --out-dir tmp/raw_pirate/ \
  --concurrency 3

# Post-process: chroma key + downscale to 48×48
python "$ASSET_GEN" chroma-key-dir \
  --input-dir tmp/raw_pirate/ \
  --output-dir art/player/pirate/ \
  --downscale 48
```
