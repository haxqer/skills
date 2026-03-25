# Asset Catalog — Complete Inventory

> Last updated: 2025-03-25. All sprites are **48×48 px RGBA PNGs** with transparent backgrounds unless noted.

## Contents

- `Player Characters`
- `Monsters`
- `NPCs`
- `Items`
- `Effects`
- `Tiles`
- `Decorations`
- `Backgrounds`
- `UI`
- `Summary`

---

## Player Characters (`art/player/`)

5 classes × 14 frames = 70 frames. Each in its own subdirectory.

| Class | Directory | Frames |
|-------|-----------|--------|
| Beginner | `beginner/` | idle(2), run(4), attack(2), jump(1), fall(1), hurt(1), death(1), climb(2) |
| Warrior | `warrior/` | idle(2), run(4), attack(2), jump(1), fall(1), hurt(1), death(1), climb(2) |
| Mage | `mage/` | idle(2), run(4), attack(2), jump(1), fall(1), hurt(1), death(1), climb(2) |
| Thief | `thief/` | idle(2), run(4), attack(2), jump(1), fall(1), hurt(1), death(1), climb(2) |
| Archer | `archer/` | idle(2), run(4), attack(2), jump(1), fall(1), hurt(1), death(1), climb(2) |

---

## Monsters (`art/monsters/`)

### In Subdirectories (original — 7 types × 6 frames = 42 frames)

| Monster | Directory | Frames |
|---------|-----------|--------|
| Green Slime | `slime_green/` | idle(2), hop(2), hurt(1), death(1) |
| Blue Slime | `slime_blue/` | idle(2), hop(2), hurt(1), death(1) |
| Blue Snail | `snail_blue/` | idle(2), hop(2), hurt(1), death(1) |
| Orange Mushroom | `mushroom_orange/` | idle(2), hop(2), hurt(1), death(1) |
| Wild Boar | `boar_wild/` | idle(2), hop(2), hurt(1), death(1) |
| Mushroom King (Boss) | `boss_mushroom_king/` | idle(2), hop(2), hurt(1), death(1) |
| Dragon King (Boss) | `boss_dragon_king/` | idle(2), hop(2), hurt(1), death(1) |

### Flat Files (new — 5 types × 6 frames = 30 frames)

| Monster | Files | Frames |
|---------|-------|--------|
| Red Snail | `snail_red_*.png` | idle(2), hop(2), hurt(1), death(1) |
| Fire Boar | `boar_fire_*.png` | idle(2), hop(2), hurt(1), death(1) |
| Ice Drake | `drake_ice_*.png` | idle(2), hop(2), hurt(1), death(1) |
| Dark Stump | `stump_dark_*.png` | idle(2), hop(2), hurt(1), death(1) |
| Zombie Mushroom King (Boss) | `boss_zombie_mushroom_*.png` | idle(2), hop(2), hurt(1), death(1) |

> **Note**: New monsters are stored as flat files in `art/monsters/` (not subdirectories). Move them into subdirectories when wiring into Godot scenes if desired.

---

## NPCs (`art/npcs/`)

8 NPCs × 2 idle frames = 16 frames.

| NPC | Files |
|-----|-------|
| Shopkeeper | `npc_shopkeeper_idle_00.png`, `_01.png` |
| Healer | `npc_healer_idle_00.png`, `_01.png` |
| Warrior Trainer | `npc_warrior_trainer_idle_00.png`, `_01.png` |
| Wizard | `npc_wizard_idle_00.png`, `_01.png` |
| **Mage Trainer** ★ | `npc_mage_trainer_idle_00.png`, `_01.png` |
| **Thief Trainer** ★ | `npc_thief_trainer_idle_00.png`, `_01.png` |
| **Archer Trainer** ★ | `npc_archer_trainer_idle_00.png`, `_01.png` |
| **Mayor** ★ | `npc_mayor_idle_00.png`, `_01.png` |

★ = newly generated

---

## Items (`art/items/`)

19 item icons (single frame each).

| Item | File | New? |
|------|------|------|
| Sword | `icon_sword.png` | |
| Bow | `icon_bow.png` | |
| Dagger | `icon_dagger.png` | |
| Staff | `icon_staff.png` | |
| Red Potion | `icon_potion_red.png` | |
| Blue Potion | `icon_potion_blue.png` | |
| Scroll | `icon_scroll.png` | |
| Coin | `icon_coin.png` | |
| **Iron Helmet** | `icon_helmet_iron.png` | ★ |
| **Wooden Shield** | `icon_shield_wood.png` | ★ |
| **Dark Cape** | `icon_cape_dark.png` | ★ |
| **Gold Ring** | `icon_ring_gold.png` | ★ |
| **Leather Armor** | `icon_armor_leather.png` | ★ |
| **Iron Boots** | `icon_boots_iron.png` | ★ |
| **Leather Gloves** | `icon_gloves_leather.png` | ★ |
| **Green Potion** | `icon_potion_green.png` | ★ |
| **Return Scroll** | `icon_scroll_return.png` | ★ |
| **Meso Bag** | `icon_meso_bag.png` | ★ |
| **Ore Crystal** | `icon_ore_crystal.png` | ★ |

---

## Effects (`art/effects/`)

23 effect frames across 8 effect types.

| Effect | Frames | Files | New? |
|--------|--------|-------|------|
| Slash | 3 | `slash_00.png` ~ `slash_02.png` | |
| Hit Spark | 2 | `hit_spark_00.png`, `_01.png` | |
| Level Up | 3 | `levelup_00.png` ~ `levelup_02.png` | |
| Portal | 4 | `portal_00.png` ~ `portal_03.png` | |
| **Death Poof** | 3 | `death_poof_00.png` ~ `_02.png` | ★ |
| **Pickup Glow** | 3 | `pickup_glow_00.png` ~ `_02.png` | ★ |
| **Fire Arrow** | 3 | `fire_arrow_00.png` ~ `_02.png` | ★ |
| **Ice Strike** | 2 | `ice_strike_00.png`, `_01.png` | ★ |

---

## Tiles (`art/tiles/`)

8 tile sprites.

| Tile | File | New? |
|------|------|------|
| Grass Top | `tile_grass_top.png` | |
| Dirt | `tile_dirt.png` | |
| Stone | `tile_stone.png` | |
| Wood Platform | `tile_wood_platform.png` | |
| **Snow Top** | `tile_snow_top.png` | ★ |
| **Ice** | `tile_ice.png` | ★ |
| **Brick** | `tile_brick.png` | ★ |
| **Metal Platform** | `tile_metal_platform.png` | ★ |

---

## Decorations (`art/decorations/`)

7 decoration sprites.

| Decoration | File | New? |
|------------|------|------|
| Bush | `decor_bush.png` | |
| Flower | `decor_flower.png` | |
| Signpost | `decor_signpost.png` | |
| **Tree** | `decor_tree.png` | ★ |
| **Mushroom** | `decor_mushroom.png` | ★ |
| **Lantern** | `decor_lantern.png` | ★ |
| **Tombstone** | `decor_tombstone.png` | ★ |

---

## Backgrounds (`art/backgrounds/`)

6 parallax layers (**NOT** 48×48, full resolution ~1344×768).

| Layer | File | New? |
|-------|------|------|
| Far Hills | `bg_far_hills.png` | |
| Near Trees | `bg_near_trees.png` | |
| Sky | `bg_sky.png` | |
| **Snow Mountains** | `bg_snow_mountains.png` | ★ |
| **Dark Forest** | `bg_dark_forest.png` | ★ |
| **Town Rooftops** | `bg_town_rooftops.png` | ★ |

---

## UI (`art/ui/`)

41 UI assets (panels, bars, buttons, skill icons, other).

### Panels (7)
`panel_character.png`, `panel_dialog.png`, `panel_inventory.png`, `panel_quest.png`, `panel_skill.png`, `panel_tooltip.png`, `panel_vendor.png`

### Bars (6)
`bar_hp_bg.png`, `bar_hp_fg.png`, `bar_mp_bg.png`, `bar_mp_fg.png`, `bar_exp_bg.png`, `bar_exp_fg.png`

### Buttons (9)
`btn_primary_normal.png`, `btn_primary_hover.png`, `btn_primary_pressed.png`, `btn_secondary_normal.png`, `btn_secondary_hover.png`, `btn_secondary_pressed.png`, `btn_danger_normal.png`, `btn_danger_hover.png`, `btn_danger_pressed.png`

### Skill Icons (16)
`skill_basic_attack.png`, `skill_power_strike.png`, `skill_slash_blast.png`, `skill_iron_body.png`, `skill_rage.png`, `skill_magic_bolt.png`, `skill_magic_guard.png`, `skill_ice_strike.png`, `skill_double_shot.png`, `skill_fire_arrow.png`, `skill_arrow_rain.png`, `skill_lucky_seven.png`, `skill_haste.png`, `skill_dark_sight.png`, `skill_heal.png`, `skill_blessing.png`

### Other (3)
`portrait_frame.png`, `quickbar_slot.png`, `quickbar_cooldown.png`

---

## Summary

| Category | Existing | New ★ | Total |
|----------|----------|-------|-------|
| Player Characters | 70 | 0 | 70 |
| Monsters | 42 | 30 | 72 |
| NPCs | 8 | 8 | 16 |
| Items | 8 | 11 | 19 |
| Effects | 12 | 11 | 23 |
| Tiles | 4 | 4 | 8 |
| Decorations | 3 | 4 | 7 |
| Backgrounds | 3 | 3 | 6 |
| UI | 41 | 0 | 41 |
| **Total** | **191** | **71** | **262** |
