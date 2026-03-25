# Naming Conventions

File naming and directory structure rules for all game art assets.

## Contents

- `General Rules`
- `Directory Naming`
- `File Naming by Category`
- `Monster Naming Convention`
- `Player Class Names`

---

## General Rules

1. **All lowercase** with underscores (`snake_case`)
2. **No spaces, hyphens, or special characters** in file or directory names
3. **Animation frames** use zero-padded two-digit suffix: `_00`, `_01`, `_02`, ...
4. **File format**: PNG (32-bit RGBA) — always `.png` extension
5. **Canvas size**: 48×48 pixels for all sprites; backgrounds may differ

---

## Directory Naming

| Category | Path pattern | Example |
|----------|-------------|---------|
| Player class | `art/player/{class_name}/` | `art/player/warrior/` |
| Monster | `art/monsters/{monster_name}/` | `art/monsters/slime_green/` |
| Boss monster | `art/monsters/boss_{boss_name}/` | `art/monsters/boss_dragon_king/` |
| NPC | `art/npcs/` (flat) | `art/npcs/` |
| Item icon | `art/items/` (flat) | `art/items/` |
| Effect | `art/effects/` (flat) | `art/effects/` |
| Tile | `art/tiles/` (flat) | `art/tiles/` |
| Decoration | `art/decorations/` (flat) | `art/decorations/` |
| UI | `art/ui/` (flat) | `art/ui/` |
| Background | `art/backgrounds/` (flat) | `art/backgrounds/` |

---

## File Naming by Category

### Player & Monster Animation Frames

Pattern: `{state}_{frame:02d}.png`

```
idle_00.png
idle_01.png
run_00.png
run_01.png
run_02.png
run_03.png
attack_00.png
attack_01.png
jump_00.png
fall_00.png
hurt_00.png
death_00.png
climb_00.png
climb_01.png
```

For monsters with hop movement: `hop_00.png`, `hop_01.png`
For monsters with walk movement: `walk_00.png`, `walk_01.png`

### NPCs

Pattern: `npc_{role}_{state}_{frame:02d}.png`

```
npc_shopkeeper_idle_00.png
npc_shopkeeper_idle_01.png
npc_healer_idle_00.png
```

### Items

Pattern: `icon_{item_name}.png`

```
icon_sword.png
icon_potion_red.png
icon_scroll.png
```

### Effects

Pattern: `{effect_name}_{frame:02d}.png`

```
slash_00.png
slash_01.png
hit_spark_00.png
levelup_00.png
portal_00.png
death_poof_00.png
pickup_glow_00.png
```

### Tiles

Pattern: `tile_{name}.png`

```
tile_grass_top.png
tile_dirt.png
tile_stone.png
tile_wood_platform.png
```

### Decorations

Pattern: `decor_{name}.png`

```
decor_bush.png
decor_flower.png
decor_signpost.png
```

### UI Elements

Patterns by sub-type:

| Sub-type | Pattern | Example |
|----------|---------|---------|
| Skill icon | `skill_{name}.png` | `skill_power_strike.png` |
| Panel | `panel_{name}.png` | `panel_inventory.png` |
| Bar | `bar_{type}_{layer}.png` | `bar_hp_fg.png` |
| Button | `btn_{style}_{state}.png` | `btn_primary_hover.png` |
| Quickbar | `quickbar_{name}.png` | `quickbar_slot.png` |
| Portrait | `portrait_{name}.png` | `portrait_frame.png` |

### Backgrounds

Pattern: `bg_{name}.png`

```
bg_sky.png
bg_far_hills.png
bg_near_trees.png
```

---

## Monster Naming Convention

| Type | Name pattern | Examples |
|------|-------------|----------|
| Standard | `{species}_{color/variant}` | `slime_green`, `slime_blue`, `snail_blue`, `mushroom_orange` |
| Compound | `{descriptor}_{species}` | `boar_wild` |
| Boss | `boss_{name}` | `boss_mushroom_king`, `boss_dragon_king` |

---

## Player Class Names

Use the exact class identifier in the directory name:

| Class | Directory name |
|-------|---------------|
| Beginner | `beginner` |
| Warrior | `warrior` |
| Mage | `mage` |
| Thief | `thief` |
| Archer | `archer` |

Future classes should follow the same single-word lowercase pattern.
