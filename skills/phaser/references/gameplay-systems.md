# Gameplay Systems

## Input

- Use Phaser input plugins instead of raw DOM listeners unless the repository
  already mixes both intentionally.
- Enable interactivity only on objects that need it.
- Keep pointer, keyboard, and gamepad handling close to the scene that owns the
  behavior.
- For menu or UI scenes, prefer explicit hover, down, and up handling over
  overloading one callback with multiple responsibilities.

## Animations

- Use frame-based animations for sprites and atlases.
- Prefer global animations for assets reused across multiple sprites or scenes.
- Prefer local animations only when the animation truly belongs to one object
  instance.
- Keep animation keys stable and collocated with the asset load path that
  provides their frames.

## Tweens

- Use tweens for short, time-based state changes such as UI motion, pickups,
  fades, bounce, shake, or camera-like property interpolation.
- Do not start a fresh tween every frame inside `update()` unless the effect is
  explicitly designed that way.
- If a tween is part of scene teardown or restart logic, stop or remove it
  explicitly.

## Cameras

- Keep one main camera unless the feature truly needs split-screen, picture in
  picture, or overlay cameras.
- Set camera bounds when following a player in a finite world.
- Use follow plus deadzones and lerp deliberately instead of stacking multiple
  competing camera effects.
- Prefer camera effects for transitions and brief emphasis, not for permanent
  motion logic.

## Arcade Physics

- Default to Arcade Physics for platformers, top-down action, simple projectiles
  and collision-heavy browser games.
- Enable physics in the game config or per scene before adding Arcade bodies.
- Set body size, offset, gravity, immovable state, and collision rules
  explicitly when they matter to gameplay.
- Use `collider` for blocking interactions and `overlap` for triggers,
  collectibles, or damage zones.
- Keep debug rendering temporary and disable it before finishing unless the user
  explicitly wants it.

## Tilemaps

- Default tilemap work to Tiled JSON unless the project already uses CSV or a
  generated array format.
- Load the map data and the tileset textures before creating layers.
- Keep layer names aligned with the names in the map editor.
- Make collision layers explicit and set collision by property, index, or layer
  selection instead of relying on implicit defaults.
- When spawning objects from object layers, keep the translation from map data
  to Phaser objects centralized so it remains debuggable.

## System Integration Order

Use this order for most feature work:

1. Load assets.
2. Create game objects and layers.
3. Enable input or physics as needed.
4. Register collisions, overlaps, animations, and tweens.
5. Configure camera follow or scene transitions.
6. Validate the changed loop in a browser.
