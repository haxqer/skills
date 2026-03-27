# Project Setup

## Preferred Defaults

- For new Phaser 3 work, default to TypeScript plus Vite.
- For existing repositories, keep the current bundler and package manager
  unless there is a concrete problem to solve.
- Prefer the official create-game flow when starting from scratch.
- Avoid CDN-based setups unless the repository already uses one or the user
  explicitly asks for a single-file prototype.

## New Project Paths

### Official Create-Game CLI

The official docs recommend the create-game app:

```bash
npm create @phaserjs/game@latest
```

Other official entrypoints exist as well:

```bash
npx @phaserjs/create-game@latest
pnpm create @phaserjs/game@latest
bun create @phaserjs/game@latest
```

- For first-time users, prefer the official `Web Bundler` plus `Vite` path.
- Prefer a TypeScript template unless the repository or user explicitly wants
  plain JavaScript.

### Minimal Vite Setup

If you are wiring Phaser into an existing or empty Vite app, use:

```bash
npm install phaser
```

Then keep the structure simple:

```text
src/
  main.ts
  game/
    config.ts
    scenes/
      BootScene.ts
      PreloadScene.ts
      GameScene.ts
public/
  assets/
```

- Keep `main.ts` responsible for bootstrapping the browser app and constructing
  `new Phaser.Game(config)`.
- Keep scene classes under `src/game/scenes/` or the existing repository
  equivalent.
- Keep static assets under `public/assets/` unless the project already uses a
  different bundler-aware asset path.

## TypeScript Notes

- Phaser ships TypeScript definitions in its package. Modern editors normally
  pick them up automatically through the package `types` entry.
- If the current `tsconfig.json` fails to resolve Phaser types, inspect the
  official installation guidance before adding custom `typeRoots`.
- Keep DOM libs enabled. Phaser browser projects typically need at least
  `dom`-related TypeScript libraries.

## Setup Checklist

- Confirm the package is `phaser` and still on a Phaser `3.x` release line.
- Confirm the entrypoint mounts the game into the expected DOM parent.
- Confirm `width`, `height`, and `scale` settings match the intended viewport
  model.
- Confirm asset directories resolve correctly in both the dev server and a
  production build.
- Confirm the repository has an obvious place for shared boot, preload, and
  gameplay scenes before adding new files.
