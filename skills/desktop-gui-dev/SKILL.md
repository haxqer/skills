---
name: desktop-gui-dev
description: Choose, build, debug, package, and review desktop GUI applications. Use when Codex needs to scaffold or modify Tauri, Electron, or version-aware Wails apps, or to choose, review, and guide architecture, platform integration, persistence, packaging, signing, and release-readiness work for native-toolkit desktop apps such as Qt, SwiftUI, WinUI, GTK, or .NET MAUI.
---

# Desktop GUI Dev

## Overview

Treat a desktop GUI application as either a web-shell app or a native-toolkit app.

- Web-shell apps such as Tauri, Electron, and Wails have four coupled surfaces: the UI shell, the native bridge, local data and persistence, and platform integration.
- Native-toolkit apps such as Qt, SwiftUI, WinUI, GTK, or .NET MAUI collapse the UI and native layers into one codebase, but still need clear boundaries for state, persistence, background work, and packaging.
- Keep contracts, permissions, packaging metadata, and runtime behavior aligned across every surface you touch.

## Start Here

- Determine whether the user wants a new desktop app, a feature addition, a bug fix, or a packaging and release change.
- Identify the target platforms, required native capabilities, and whether the existing stack is fixed or still open.
- If the user does not specify a stack and the repo does not already constrain one, default new web-shell desktop work to Tauri 2.x (Rust), React 19 + TypeScript, Tailwind CSS 4, Zustand, SQLite via `rusqlite`, and Recharts.
- Identify the app family early: web-shell or native toolkit.
- For Wails repos, confirm the version boundary immediately from the import path, CLI, or docs domain before reusing commands or runtime assumptions.
- Read the actual build files and app manifests before editing. Prefer source over stale docs.
- For scaffold commands, install prerequisites, packaging steps, and security-sensitive defaults, prefer the official docs linked from the stack references when they differ from memory or older repo notes.
- Use `rg` for search and keep changes scoped to the smallest set of files that preserves cross-layer consistency.
- Read [references/framework-selection.md](references/framework-selection.md) when the framework is not already chosen.
- Read [references/desktop-architecture.md](references/desktop-architecture.md) before changing IPC, persistence, background tasks, menus, tray behavior, or window lifecycle.
- Read [references/release-checklist.md](references/release-checklist.md) before working on installers, signing, auto-update, or release validation.
- This skill goes deepest on Tauri, Electron, and version-aware Wails workflows. For Qt, SwiftUI, WinUI, GTK, and .NET MAUI, use it primarily for stack selection, architecture, cross-layer design, and release-readiness review, then defer toolkit-specific APIs and templates to the official toolkit docs.
- For signing, notarization, installers, or updater release work, treat the matching stack reference plus the official platform docs as authoritative before changing build, packaging, or CI configuration.
- After the stack is chosen, read the matching implementation guide:
  - [references/tauri.md](references/tauri.md)
  - [references/electron.md](references/electron.md)
  - [references/wails.md](references/wails.md) for Wails v2
  - [references/wails-v3.md](references/wails-v3.md) for Wails v3
  - [references/native-toolkits.md](references/native-toolkits.md)

## Choose The Right Stack

- Preserve the current stack unless the user explicitly asks to migrate.
- Prefer Tauri when bundle size, startup cost, Rust-native integrations, and a web UI are a good fit.
- Prefer Electron when Chromium and Node integrations, mature plugin coverage, or browser-level compatibility matter more than size.
- Prefer Wails when the team wants a Go backend with a web UI.
- For Wails repositories, confirm whether the repo is on v2 or v3 before reusing CLI, bindings, or frontend-runtime assumptions.
- Prefer Qt, SwiftUI, WinUI, GTK, or another native toolkit when platform-native widgets, accessibility fidelity, or heavy native UI behavior outweigh web-stack reuse.
- If the request is still exploratory, narrow the decision with OS targets, offline needs, updater requirements, team language preference, and required native APIs.

## Default Stack When Unspecified

- Use this default only when the user leaves the stack open and the repo does not already establish a different stack.
- Desktop framework: Tauri 2.x with Rust for native commands, persistence, and platform integration.
- Frontend: React 19 with TypeScript.
- Styling: Tailwind CSS 4.
- State management: Zustand.
- Database: SQLite accessed from Rust via `rusqlite`.
- Charts: Recharts.
- Treat this as the baseline greenfield stack. Only diverge when the user or repo requirements clearly point to Electron, Wails, or a native toolkit.

## Choose The Right Implementation Path

- For Tauri, Electron, and Wails, use a bridge-first architecture: renderer or frontend code stays unprivileged and talks to typed native adapters.
- For Qt, SwiftUI, WinUI, GTK, and similar stacks, use a native-app architecture: organize around screens or windows, view models or controllers, services, persistence, and platform adapters.
- Do not force IPC-heavy patterns onto native toolkits when direct typed application services are the simpler and safer design.

## Scaffold Deterministically

- For Tauri work, use [references/tauri.md](references/tauri.md) for the current project creation and runtime commands.
- For the default Tauri stack, start from the React + TypeScript starter and add Tailwind CSS 4, Zustand, Recharts, and Rust-side SQLite access via `rusqlite` unless the repo already chose alternatives.
- For Electron work, use [references/electron.md](references/electron.md) for Forge-based bootstrap, preload, packaging, and import guidance.
- For Wails v2 work, use [references/wails.md](references/wails.md) for CLI install, template selection, generated layout, and build commands.
- For Wails v3 work, use [references/wails-v3.md](references/wails-v3.md) for `wails3` install, generated bindings, frontend runtime boundaries, and build commands.
- For native toolkits, use [references/native-toolkits.md](references/native-toolkits.md) to narrow the toolkit, then start from the official platform template and official toolkit docs instead of inventing folder layout or build steps from scratch.

## Trigger Examples

- "Build a desktop app with a system tray and auto-start."
- "Scaffold a Tauri app with React and local SQLite storage."
- "Fix an Electron preload bridge and tighten the renderer security boundary."
- "Turn this existing web app into a desktop app."
- "Create a macOS menu bar app."
- "Add global shortcuts, notifications, and deep links to this desktop app."
- "Package and sign the Windows installer and macOS build."
- "Review the desktop app architecture before we add updater support."
- "Audit this desktop app release plan before we ship."
- "Review this SwiftUI menu bar app before we add login-item support."
- "Fix this WinUI app so window state and local settings survive relaunch."
- "Scaffold a Qt desktop app and keep services out of widget code."

## When Not To Use

- Do not use this skill for browser-only web apps with no desktop runtime.
- Do not use this skill for mobile-only apps, backend services, or CLI-only tools.
- Do not use this skill for website design or frontend work unless the request explicitly includes desktop packaging, native integrations, or desktop runtime behavior.

## Plan Before Coding

- Define the smallest vertical slice that proves the app shape: one window, one navigation path, one state flow, and one persistence or native bridge action.
- Decide the boundary between UI code and privileged native operations before wiring features.
- List required platform integrations up front: tray, global shortcuts, file dialogs, notifications, deep links, auto-start, background workers, updater, and signing.
- Keep project structure obvious. Separate UI, bridge or IPC adapters, domain logic, persistence, and packaging assets.

## Use The Right Entry Point

- For greenfield work, scaffold the app shell first, then wire one end-to-end feature before expanding the surface area.
- For UI work, start in the window layout, routes or screens, shared components, and state containers.
- For native or IPC work in web-shell apps, update the handler implementation, the typed wrapper layer, and every consumer in the same pass.
- For native-toolkit apps, update the command or action handler, the service layer, and every screen or view model that consumes it in the same pass.
- For data work, trace the full path from schema or storage change through migrations, repository access, typed models, and the UI that reads the data.
- For platform integration, update window config, app manifest or capabilities, menu or tray code, icons, and packaging metadata together.

## Keep These Surfaces In Sync

- Shared payloads must stay aligned across backend structs, generated or hand-written types, IPC wrappers, and UI consumers in web-shell apps.
- In native-toolkit apps, keep view-model state, command handlers, persistence models, and packaging metadata aligned instead of inventing a fake IPC layer.
- Keep naming and casing conventions stable within one app. Do not let transport formats drift between layers.
- Add backward-aware migrations for persisted data. Existing user profiles and databases must remain readable unless the user explicitly accepts a break.
- When adding a privileged capability, update both implementation and permission or capability declarations in the same change.
- Keep user-visible copy, keyboard shortcuts, and menu labels consistent across the window UI and native surfaces.
- When introducing platform-specific code paths, leave a clear fallback or explicit unsupported-path behavior for other operating systems.

## Protect User Data And System State

- Assume the app may point at real user data, config directories, cache paths, or system services.
- Prefer temporary profiles, fixture data, or disposable databases while developing destructive flows.
- Do not delete real data, overwrite user settings, or modify auto-start, tray, or background behavior unless the task clearly requires it.
- Guard long-running native work with cancellation, timeout, or progress reporting when the UI could otherwise freeze or appear hung.

## Apply Task-Specific Workflow

### New app or large feature work

- Confirm stack, platform targets, distribution channel, and required native integrations.
- If the user leaves the stack open for a new web-shell app, use the default stack above instead of spending time re-deciding the baseline.
- Create the shell, establish folder boundaries, and implement one end-to-end feature before broadening the design.
- For web-shell stacks, add typed bridge helpers early so IPC and native calls do not spread as raw stringly-typed calls through the UI.
- For native-toolkit stacks, add a clear service or view-model boundary early so platform calls do not leak into every view.

### UI and interaction work

- Validate resize behavior, focus order, keyboard navigation, high-DPI rendering, and error states.
- Check that window chrome, modal flow, and shortcut handling feel native on the target OS.

### Native bridge or background work

- Define the request and response contract first, including failure states.
- Validate serialization, permission checks, cancellation behavior, and recovery after app reload or relaunch.

### Persistence work

- Choose the lightest store that matches the data shape: config files, embedded database, or indexed document store.
- Add migrations, import and export paths, and corruption-aware recovery behavior when persistent state matters.

### Platform integration work

- Verify menus, tray icons, notifications, file dialogs, drag and drop, deep links, global shortcuts, and auto-start on the operating systems the user actually targets.
- Keep platform-specific behavior isolated so the rest of the app can remain portable.

### Packaging and release work

- Validate bundle identifiers, app icons, version metadata, installer configuration, signing inputs, and update feed wiring.
- Smoke test the packaged app, not just the development runner.

## Validate Before Finishing

- Run the lint, typecheck, build, and test commands that match the chosen stack.
- Launch the app in the desktop runtime when the change crosses the native boundary.
- Exercise the main user path plus any touched platform feature such as tray, menu, dialog, persistence, updater, or file access.
- For new scaffolds, verify a clean install, first launch, and a packaged build path before calling the app ready.
- State explicitly which validation steps were not run and why.

## Use References Selectively

- Load the smallest matching reference set for the current task instead of reading everything:
  - [references/framework-selection.md](references/framework-selection.md) for stack choice or migration questions
  - [references/desktop-architecture.md](references/desktop-architecture.md) for IPC, persistence, background work, or OS integration
  - [references/release-checklist.md](references/release-checklist.md) for packaging, signing, installers, or release smoke tests
  - exactly one implementation guide for the chosen stack:
    - [references/tauri.md](references/tauri.md)
    - [references/electron.md](references/electron.md)
    - [references/wails.md](references/wails.md)
    - [references/wails-v3.md](references/wails-v3.md)
    - [references/native-toolkits.md](references/native-toolkits.md)
