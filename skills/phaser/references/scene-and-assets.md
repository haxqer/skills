# Scene And Assets

## Scene Lifecycle

- Use scenes to split loading, menus, gameplay, overlays, and cutscenes into
  logical units.
- In class-based projects, prefer `extends Phaser.Scene` with a stable scene
  key.
- Place startup work in the appropriate lifecycle method:
  - `init()` for small incoming data and scene startup state
  - `preload()` for queueing assets
  - `create()` for constructing objects, input bindings, cameras, and events
  - `update()` for per-frame logic that cannot be event driven
- Remember that a scene can be started, paused, slept, resumed, stopped, and
  started again. Clean up listeners on `shutdown` when they should not survive a
  restart.

## Scene Organization

- In single-scene prototypes, one scene is acceptable.
- In growing projects, split at least into a boot or preload scene and one or
  more gameplay scenes.
- Keep UI overlays, pause menus, or HUDs in separate scenes when they need
  independent control or camera behavior.
- Avoid hidden global state. Prefer scene data, the game registry, or explicit
  method calls.

## Game Config Notes

Typical config shape:

```ts
import Phaser from "phaser";
import { BootScene } from "./scenes/BootScene";
import { GameScene } from "./scenes/GameScene";

export const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: "app",
  width: 1280,
  height: 720,
  scene: [BootScene, GameScene],
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  physics: {
    default: "arcade",
    arcade: {
      debug: false,
    },
  },
};
```

- Keep the scene list explicit.
- Prefer configuring scale, parent, and physics in the main config instead of
  scattering them across scenes.
- Use `preBoot` or `postBoot` only when startup work truly belongs at the game
  level.

## Loader Strategy

- Load assets before first use.
- Keep shared assets in a boot or preload scene in multi-scene projects.
- Keep scene-local assets in the scene that owns them.
- Use `this.load.setPath()` or `baseURL` only when it materially simplifies the
  asset tree.
- Track failed requests and loader events when diagnosing 404s or broken builds.

## Asset Keys

- Keep keys descriptive and stable, such as `player-idle`, `ui-button-primary`,
  or `tiles-dungeon`.
- Avoid duplicate keys within the same asset type.
- Prefer one naming convention across images, atlases, audio, JSON, and
  tilemaps.
- If a repository already has a naming pattern, continue it.

## Scene Transitions

- Use `this.scene.start()` when handing control to a replacement scene.
- Use `this.scene.launch()` or `this.scene.run()` for overlays that should
  coexist with the current scene.
- Pass only the data the next scene actually needs.
- When a scene subscribes to external events, detach them on `shutdown` or
  `destroy` if they should not outlive that scene instance.
