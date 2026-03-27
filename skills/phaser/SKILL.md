---
name: "phaser"
description: "Phaser 3 browser game development, debugging, and feature-delivery skill for new or existing projects. Use when Codex needs to create or modify a Phaser 3 game, scaffold or extend a TypeScript + Vite setup, organize scenes, load assets, wire input, Arcade Physics, cameras, tweens, animations, or tilemaps, or diagnose browser runtime and asset-pipeline issues in a Phaser repository."
---

# Phaser

Use this skill to build, extend, and debug Phaser 3 browser games with the
official Phaser docs, examples, and upstream repository as the primary
references.

## Start

- Confirm the target is Phaser 3, not Phaser 2/CE or Phaser 4.
- Inspect `package.json`, the lockfile, bundler config, TypeScript config, and
  the current scene and asset layout before planning edits.
- Prefer the repository's existing stack when the project already exists. For
  new work, default to TypeScript plus Vite.
- Identify the `new Phaser.Game(config)` entrypoint, scene registration
  pattern, asset directory, and whether the project already uses Arcade
  Physics, Matter, tilemaps, DOM overlays, or custom plugins.
- Read only the references needed for the task:
  - `references/project-setup.md` for scaffolding or repo bootstrap
  - `references/scene-and-assets.md` for scenes, loader flow, registry, and
    scene transitions
  - `references/gameplay-systems.md` for input, animations, tweens, cameras,
    Arcade Physics, and tilemaps
  - `references/debugging-checklist.md` for black screens, runtime failures,
    asset issues, resize problems, or listener leaks
  - `references/official-sources.md` when you need the exact official doc,
    example, or repository entrypoint

## Working Mode

- Treat scenes as the primary unit of game flow. Avoid letting one file own
  boot, preload, gameplay, UI, and transitions unless the repository already
  does so.
- Keep asset keys stable, descriptive, and unique. Do not rename working keys
  without updating all call sites.
- Prefer a dedicated boot or preload scene for shared assets in multi-scene
  projects.
- Default physics work to Arcade Physics unless the user explicitly asks for
  Matter or the repository already depends on it.
- Preserve the project's current input style, update-loop structure, and asset
  conventions before introducing a new pattern.
- Prefer official Phaser 3 docs, examples, and upstream source over third-party
  tutorials.
- Validate behavior in a browser after non-trivial changes instead of stopping
  at a successful build.

## Workflow

1. Inspect the project shape.
- Find the bundler, entrypoint, scene registration pattern, and asset paths.
- Confirm whether the work belongs in an existing scene, a new scene, or shared
  boot and setup code.

2. Set up or extend the project.
- For a new project, prefer the official create-game path or a minimal Vite
  setup with `phaser` installed.
- For an existing project, adapt to the current stack instead of re-scaffolding
  it.

3. Stabilize the game config.
- Check renderer choice, parent mount, width and height policy, scale mode,
  physics config, and scene list.
- Keep scale and physics settings consistent with the requested device target
  and gameplay feel.

4. Implement scene and asset changes.
- Add or update `preload`, `create`, and `update` work in the correct scene.
- Load assets before use, keep keys consistent, and isolate scene-local versus
  shared resources.
- Use scene data, registry, or explicit method wiring instead of hidden
  globals.

5. Implement gameplay systems.
- Wire input, animations, tweens, cameras, collisions, overlaps, and tilemaps
  in the scene that owns the behavior.
- Keep physics body sizing, offsets, and collision layers explicit instead of
  relying on defaults when gameplay depends on them.

6. Validate the result.
- Run the local dev server or preview build.
- Exercise the changed flow in a browser.
- Inspect console errors, failed network requests, and obvious gameplay
  regressions before finishing.

## Reference Routing

- Read `references/project-setup.md` when creating a Phaser 3 app, adding
  Phaser to an existing Vite project, or checking the expected folder layout.
- Read `references/scene-and-assets.md` when changing scene lifecycle code,
  preload behavior, scene transitions, asset keys, loader flow, or registry
  usage.
- Read `references/gameplay-systems.md` when implementing or debugging input,
  animation playback, tweens, camera follow, Arcade Physics, or tilemap
  integration.
- Read `references/debugging-checklist.md` when the game boots to a blank
  screen, assets fail to load, input stops responding, physics bodies misalign,
  scale behavior is wrong, or scene listeners leak across restarts.
- Read `references/official-sources.md` when you need the exact official URL or
  want to jump from docs to examples or upstream source.

## Check Before You Finish

- Confirm the target code is Phaser 3.
- Confirm every new asset path resolves from the running app, not just from
  source layout assumptions.
- Confirm scenes start, transition, and shut down cleanly without duplicate
  listeners or duplicate objects.
- Confirm input, collisions, tweens, and camera behavior match the requested
  gameplay change.
- Confirm the changed flow was exercised in a browser and the console is free
  of relevant errors.
