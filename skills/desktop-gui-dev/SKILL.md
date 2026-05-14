---
name: desktop-gui-dev
description: Build, debug, package, and review Tauri desktop GUI applications. Use when Codex needs to scaffold or modify a Tauri app, wire Rust commands and frontend calls, add Tauri plugins or capabilities, handle local persistence, platform integrations, signing, packaging, updater work, or release-readiness validation for a Tauri desktop app.
---

# Desktop GUI Dev

## Overview

Use this skill only for Tauri desktop applications.

- Treat the app as a Tauri shell with an unprivileged frontend, a Rust native layer, local data or persistence, and platform integration.
- Keep frontend contracts, Rust commands, capabilities, packaging metadata, and runtime behavior aligned across every surface you touch.
- Do not add guidance for other desktop frameworks to this skill.

## Start Here

- Determine whether the user wants a new Tauri app, a feature addition, a bug fix, or packaging and release work.
- Read the actual build files and app manifests before editing. Prefer source over stale docs.
- If the user does not specify implementation choices and the repo does not already constrain them, default to Tauri 2.x, React 19 + TypeScript, Tailwind CSS 4, Zustand, SQLite via Rust `rusqlite`, and Recharts.
- Use `rg` for search and keep changes scoped to the smallest set of files that preserves frontend, Rust, capability, and packaging consistency.
- For scaffold commands, prerequisites, plugin setup, permissions, packaging, signing, updater work, and security-sensitive defaults, prefer the official Tauri docs when they differ from memory or repo notes.
- Read [references/tauri.md](references/tauri.md) for Tauri project creation, command boundaries, capabilities, plugins, packaging, and validation.

## Default Stack When Unspecified

- Desktop framework: Tauri 2.x with Rust for native commands, persistence, and platform integration.
- Frontend: React 19 with TypeScript.
- Styling: Tailwind CSS 4.
- State management: Zustand.
- Database: SQLite accessed from Rust via `rusqlite`.
- Charts: Recharts.
- Treat this as the greenfield baseline. Only diverge when the user, repo, or target platform requirements clearly justify it.

## Implementation Path

- Use a bridge-first architecture: frontend code stays unprivileged and talks to typed Rust-backed adapters.
- Define request, response, and error shapes before wiring UI behavior.
- Prefer typed frontend wrapper functions around Tauri commands so components do not scatter raw `invoke` calls.
- Keep command names, payload shapes, serialization rules, and error handling stable across Rust handlers and frontend callers.
- When adding privileged behavior, update implementation, capabilities, command exposure, tests, and UI consumers in the same pass.

## Scaffold Deterministically

- Use [references/tauri.md](references/tauri.md) for current project creation and runtime commands.
- For the default stack, start from the React + TypeScript starter and add Tailwind CSS 4, Zustand, Recharts, and Rust-side SQLite access via `rusqlite` unless the repo already chose alternatives.
- If the frontend already exists, use Tauri's manual setup flow and preserve the repo's existing package manager, scripts, and build layout.

## Trigger Examples

- "Build a Tauri desktop app with a system tray and auto-start."
- "Scaffold a Tauri app with React and local SQLite storage."
- "Turn this existing web app into a Tauri desktop app."
- "Add global shortcuts, notifications, and deep links to this Tauri app."
- "Package and sign the Windows installer and macOS build for this Tauri app."
- "Review this Tauri app architecture before we add updater support."
- "Audit this Tauri release plan before we ship."

## When Not To Use

- Do not use this skill for browser-only web apps with no Tauri runtime.
- Do not use this skill for mobile-only apps, backend services, or CLI-only tools.
- Do not use this skill for desktop apps built with a non-Tauri runtime.
- Do not use this skill for website design or frontend work unless the request explicitly includes Tauri packaging, native integrations, or desktop runtime behavior.

## Plan Before Coding

- Define the smallest vertical slice that proves the app shape: one window, one navigation path, one state flow, and one persistence or native command action.
- Decide the boundary between UI code and privileged Rust operations before wiring features.
- List required Tauri integrations up front: tray, global shortcuts, file dialogs, notifications, deep links, auto-start, background workers, updater, signing, and installer targets.
- Keep project structure obvious. Separate UI, typed command wrappers, Rust commands, domain logic, persistence, capabilities, and packaging assets.

## Use The Right Entry Point

- For greenfield work, scaffold the app shell first, then wire one end-to-end feature before expanding the surface area.
- For UI work, start in the window layout, routes or screens, shared components, and state containers.
- For command or plugin work, update the Rust implementation, the typed frontend wrapper layer, capabilities, and every consumer in the same pass.
- For data work, trace the full path from schema or storage change through migrations, Rust repository access, typed models, and the UI that reads the data.
- For platform integration, update window config, Tauri plugins, capabilities, app manifest, menu or tray code, icons, and packaging metadata together.

## Keep These Surfaces In Sync

- Shared payloads must stay aligned across Rust structs, generated or hand-written TypeScript types, Tauri command wrappers, and UI consumers.
- Keep naming and casing conventions stable. Do not let transport formats drift between layers.
- Add backward-aware migrations for persisted data. Existing user profiles and databases must remain readable unless the user explicitly accepts a break.
- When adding a privileged capability, update both implementation and permission or capability declarations in the same change.
- Treat Tauri capability files and custom command exposure as separate security controls.
- Keep user-visible copy, keyboard shortcuts, and menu labels consistent across the window UI and native surfaces.
- When introducing platform-specific code paths, leave a clear fallback or explicit unsupported-path behavior for other operating systems.

## Protect User Data And System State

- Assume the app may point at real user data, config directories, cache paths, or system services.
- Prefer temporary profiles, fixture data, or disposable databases while developing destructive flows.
- Do not delete real data, overwrite user settings, or modify auto-start, tray, or background behavior unless the task clearly requires it.
- Guard long-running Rust work with cancellation, timeout, or progress reporting when the UI could otherwise freeze or appear hung.

## Apply Task-Specific Workflow

### New app or large feature work

- Confirm platform targets, distribution channel, frontend choices, persistence needs, and required Tauri integrations.
- If the user leaves the stack open for a new app, use the default stack above instead of spending time re-deciding the baseline.
- Create the shell, establish folder boundaries, and implement one end-to-end feature before broadening the design.
- Add typed command helpers early so Tauri calls do not spread as raw stringly typed invocations through the UI.

### UI and interaction work

- Validate resize behavior, focus order, keyboard navigation, high-DPI rendering, and error states.
- Check that window chrome, modal flow, and shortcut handling feel correct on the target OS.

### Native command, plugin, or background work

- Define the request and response contract first, including failure states.
- Validate serialization, capability coverage, cancellation behavior, and recovery after app reload or relaunch.
- Keep long-running work off the UI path and report progress when operations can take noticeable time.

### Persistence work

- Choose the lightest store that matches the data shape: config files, SQLite, or another repo-established local store.
- Prefer Rust-side SQLite access via `rusqlite` for the default stack.
- Add migrations, import and export paths, and corruption-aware recovery behavior when persistent state matters.

### Platform integration work

- Verify menus, tray icons, notifications, file dialogs, drag and drop, deep links, global shortcuts, and auto-start on the operating systems the user actually targets.
- Keep platform-specific behavior isolated so the rest of the app can remain portable.

### Packaging and release work

- Validate bundle identifiers, app icons, version metadata, installer configuration, signing inputs, updater configuration, and update feed wiring.
- Smoke test the packaged app, not just the development runner.
- On macOS, check entitlements, hardened runtime, notarization, stapling, and first-launch behavior when release scope includes them.
- On Windows, check signing inputs, installer upgrade path, and unsigned or SmartScreen-sensitive failure modes when release scope includes them.
- On Linux, check package targets, desktop-file metadata, icon integration, and runtime dependency expectations when release scope includes them.

## Validate Before Finishing

- Run the frontend lint, typecheck, build, and test commands that match the repo.
- Run Rust validation such as `cargo fmt`, `cargo clippy`, and `cargo test` when the change touches Rust code.
- Launch the app in the Tauri runtime when the change crosses the native boundary.
- Exercise the main user path plus any touched platform feature such as tray, menu, dialog, persistence, updater, or file access.
- For new scaffolds, verify a clean install, first launch, and a packaged build path before calling the app ready.
- State explicitly which validation steps were not run and why.

## Use References Selectively

- Load [references/tauri.md](references/tauri.md) when working on Tauri scaffolding, capabilities, Rust command boundaries, plugins, persistence, platform integration, packaging, updater setup, or release validation.
