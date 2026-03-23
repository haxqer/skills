# Desktop GUI Architecture

Use this reference when changing the boundary between UI code and privileged desktop behavior.

## Architecture Families

### Web-shell desktop apps

- Tauri, Electron, and Wails split the app into an unprivileged frontend and a privileged native layer.
- The key design problem is the bridge: typed requests, typed responses, permission boundaries, and predictable serialization.
- UI code should stay close to browser-style application concerns and avoid raw privileged calls.

### Native-toolkit desktop apps

- Qt, SwiftUI, WinUI, GTK, and similar stacks put the UI and native platform APIs in the same runtime.
- The key design problem is separation of concerns inside one codebase: views, view models or controllers, services, persistence, and background work.
- Do not imitate browser-process terminology when direct typed service calls are the better fit.

## Core Layers

- Presentation: windows, routes or screens, components, local interaction state, keyboard flow.
- Application state: shared client state, derived data, loading and error handling.
- Native bridge: typed wrappers for privileged actions such as filesystem access, dialogs, notifications, tray updates, and background jobs in web-shell apps.
- Persistence: config files, embedded database, caches, import and export flows, migrations.
- Platform integration: menus, tray, shortcuts, updater, protocol handlers, auto-start, permissions, and packaging metadata.

## Contract Rules

- Do not scatter raw IPC calls across the UI. Centralize them behind typed adapters in web-shell apps.
- In native-toolkit apps, centralize privileged or platform-sensitive operations behind services instead of calling them directly from every view.
- Define request, response, and error shapes explicitly before wiring the UI.
- Keep casing, naming, and serialization rules stable across the bridge when a bridge exists.
- Treat permission and capability declarations as part of the contract, not as follow-up cleanup.
- Prefer idempotent operations for settings and background toggles when possible.

## Windowing And Navigation

- Start with a single main window unless multi-window behavior is a clear product need.
- Keep modal and secondary-window creation explicit. Hidden window spawning creates debugging and lifecycle problems.
- Define ownership of shared state before adding multiple windows or background agents.
- Verify resize behavior, minimum sizes, focus restoration, and keyboard shortcuts on every touched window.

## Persistence Guidelines

- Use simple config files for lightweight preferences.
- Use an embedded database when the app stores searchable, relational, or timeline-like records.
- Add schema migrations before changing persisted models.
- Treat import, export, and backup strategy as part of the feature when user data matters.

## Background And Native Features

- Keep long-running work off the render thread or UI thread.
- Add cancellation or progress reporting for indexing, sync, export, or media-heavy tasks.
- For tray or auto-start features, make startup and shutdown behavior explicit and test relaunch flows.
- For notifications, deep links, and protocol handlers, verify both permission prompts and repeat-open behavior.

## Security And Safety

- Minimize privileged surface area. Expose only the native operations the UI actually needs.
- Validate file paths, command arguments, and external input before handing them to native code.
- Prefer allowlisted capabilities over broad filesystem or shell access.
- In Tauri, capability files and custom command exposure are separate controls. Keep both aligned; a narrow capability file does not automatically narrow `invoke_handler` command access.
- Never assume development-mode permissions are acceptable for packaged builds.

## Cross-Layer Checklist

- Contract changed:
  Update backend handlers, typed bridge wrappers or services, UI callers, tests, and this reference if the pattern changes.
- Persisted model changed:
  Update schema or file format, migrations, fixtures, import and export behavior, and any views that consume the data.
- Platform feature changed:
  Update the implementation, permissions, packaging metadata, and smoke-test plan together.
