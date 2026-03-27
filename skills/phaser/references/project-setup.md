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

## Vite Build Warnings

- Treat `[plugin builtin:vite-reporter] Some chunks are larger than 500 kB
  after minification` as a warning, not an automatic build failure.
- Check the installed Vite major version before editing config. Vite 8 and
  newer expose `build.rolldownOptions`; older projects may still use
  `build.rollupOptions`, and newer Vite versions keep it as a compatibility
  alias.
- Do not add `dynamic import()` just to silence the warning. Use lazy loading
  only when the game has a real runtime boundary, such as optional editors,
  debug tools, separate campaigns, or large data packs that are not needed for
  the first screen.
- For many Phaser games with one main boot flow, a single entry chunk is an
  acceptable outcome. After checking the emitted file sizes and first-load
  cost, raising `build.chunkSizeWarningLimit` is often more pragmatic than
  forcing extra chunk boundaries.
- If the bundle really contains separable subsystems, prefer a real split:
  `dynamic import()` for optional code paths, or `output.manualChunks` in the
  bundler config that matches the installed Vite version.
- Validate the decision with a production build plus preview. Confirm scene
  boot still works, asset URLs still resolve, and the initial load behavior is
  still acceptable for the target device class.

## Setup Checklist

- Confirm the package is `phaser` and still on a Phaser `3.x` release line.
- Confirm the entrypoint mounts the game into the expected DOM parent.
- Confirm `width`, `height`, and `scale` settings match the intended viewport
  model.
- Confirm asset directories resolve correctly in both the dev server and a
  production build.
- Confirm any Vite or Rolldown large-chunk warning was handled deliberately,
  not left behind as an unexplained build artifact.
- Confirm the repository has an obvious place for shared boot, preload, and
  gameplay scenes before adding new files.
