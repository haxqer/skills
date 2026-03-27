# Official Sources

Use official Phaser material first. Prefer the docs, examples, and upstream
repository in this order:

| Source | URL | Use it for |
| --- | --- | --- |
| Installing | `https://docs.phaser.io/phaser/getting-started/installation` | Official install commands, create-game entrypoints, npm install flow, and TypeScript setup notes |
| Game | `https://docs.phaser.io/phaser/concepts/game` | `new Phaser.Game(config)`, boot callbacks, registry, and global game-level behavior |
| Scenes | `https://docs.phaser.io/phaser/concepts/scenes` | Scene lifecycle, scene manager behavior, scene creation patterns, and shutdown semantics |
| Cross Scene Communication | `https://docs.phaser.io/phaser/concepts/scenes/cross-scene-communication` | Registry, direct scene access, and scene-to-scene coordination patterns |
| Loader | `https://docs.phaser.io/phaser/concepts/loader` | Asset loading rules, key strategy, loader events, and path or base URL behavior |
| Input | `https://docs.phaser.io/phaser/concepts/input` | Pointer, keyboard, and gamepad input behavior |
| Animations | `https://docs.phaser.io/phaser/concepts/animations` | Global versus local animations, sprite sheets, atlases, and playback rules |
| Tweens | `https://docs.phaser.io/phaser/concepts/tweens` | Time-based motion and state interpolation |
| Cameras | `https://docs.phaser.io/phaser/concepts/cameras` | Camera follow, bounds, effects, shake, zoom, and multi-camera behavior |
| Scale Manager | `https://docs.phaser.io/phaser/concepts/scale-manager` | Canvas sizing, fit modes, resize handling, and centering |
| Physics | `https://docs.phaser.io/phaser/concepts/physics` | Choosing between Arcade Physics and Matter |
| Arcade Physics | `https://docs.phaser.io/phaser/concepts/physics/arcade` | Default physics workflow for platformers, top-down games, and light collision logic |
| Tilemaps API | `https://docs.phaser.io/api-documentation/namespace/tilemaps` | Tilemap namespace surface and related classes |
| Tilemap Class | `https://docs.phaser.io/api-documentation/class/tilemaps-tilemap` | Tiled JSON, CSV, layer creation, and runtime tilemap operations |
| Official Examples | `https://phaser.io/examples` | Minimal working patterns; keep examples aligned with Phaser 3, not Phaser 4 |
| Phaser Repo | `https://github.com/phaserjs/phaser` | Upstream source, `src/`, bundled types, changelog, and concrete engine behavior |
| Create Game Repo | `https://github.com/phaserjs/create-game` | Official starter CLI behavior and supported templates |

## Routing Rules

- Stay inside the Phaser 3 docs and examples unless the user explicitly asks
  for Phaser 4.
- Prefer concept pages when you need workflow guidance and API docs when you
  need exact property names, method signatures, or event names.
- If documentation is too high level, inspect `phaserjs/phaser` source and
  types before inventing an answer.
- Prefer official examples for working patterns such as camera follow,
  tilemaps, input wiring, or Arcade Physics collisions.
- Avoid third-party tutorials unless the user explicitly asks for them or the
  official sources do not cover the problem.
