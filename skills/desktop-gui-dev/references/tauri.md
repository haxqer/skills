# Tauri

Use this reference when the chosen stack is Tauri or when the app needs Tauri's desktop shell, native capabilities, and official starter templates.

## Official Docs

- Create a project: <https://v2.tauri.app/start/create-project/>
- Prerequisites: <https://v2.tauri.app/start/prerequisites/>
- Capabilities: <https://v2.tauri.app/security/capabilities/>
- Features and plugins hub: <https://v2.tauri.app/plugin/>

If scaffold commands, templates, or permission details differ from this reference, prefer the official docs.

## When To Use

- The app needs a web UI with a smaller native shell than Electron.
- The team is comfortable with Rust for native logic, plugins, or performance-sensitive code.
- Bundle size, startup cost, and capability-based access control matter.

## Project Creation

- Fastest path for a brand-new app:
  - `npm create tauri-app@latest`
  - `yarn create tauri-app`
  - `pnpm create tauri-app`
  - `bun create tauri-app`
- `create-tauri-app` uses officially maintained templates and supports multiple frontend flavors.
- If the frontend already exists, use the manual setup flow from the official docs:
  - create the frontend app first
  - install the CLI, for example `pnpm add -D @tauri-apps/cli@latest`
  - run `pnpm tauri init`
- The manual flow creates the `src-tauri` directory and prompts for the app name, window title, frontend location, dev server URL, and frontend dev and build commands.

## Default Working Pattern

- Keep the frontend in its own app structure and keep Rust code inside `src-tauri`.
- Centralize frontend-to-native calls behind typed wrappers instead of calling Tauri APIs ad hoc from many components.
- Keep command names, payload shape, and error handling aligned across Rust handlers and frontend callers.

## Important Files

- `src-tauri/tauri.conf.json`: app identity, bundling, windows, updater, and platform configuration.
- `src-tauri/src/`: Rust commands, services, plugins, and app startup.
- `src-tauri/capabilities/`: capability files for window and plugin permissions.
- `src-tauri/build.rs` when present: app-manifest customization, including custom command exposure.

## Capability And Permission Notes

- Tauri v2 uses capability files inside `src-tauri/capabilities`.
- Capabilities define which permissions are granted to which windows or webviews.
- Commands registered through `tauri::Builder::invoke_handler` are allowed for all windows and webviews unless the app manifest explicitly scopes them with `tauri_build::AppManifest::commands`.
- Treat capability files and command exposure as separate security controls. Review both when adding a privileged feature.
- Keep capabilities narrow. Do not add broad filesystem, shell, or plugin access when a smaller permission set will do.
- Update capability declarations in the same change as the code that needs them.

## Common Feature Docs

- System tray: <https://v2.tauri.app/learn/system-tray/>
- Window menu: <https://v2.tauri.app/learn/window-menu/>
- Autostart: <https://v2.tauri.app/plugin/autostart/>
- Deep linking: <https://v2.tauri.app/plugin/deep-linking/>
- Single instance: <https://v2.tauri.app/plugin/single-instance/>
- Dialog: <https://v2.tauri.app/plugin/dialog/>
- File system: <https://v2.tauri.app/plugin/file-system/>
- Global shortcut: <https://v2.tauri.app/plugin/global-shortcut/>
- Notifications: <https://v2.tauri.app/plugin/notification/>
- Updater: <https://v2.tauri.app/plugin/updater/>
- Official plugin pages also document supported platforms, minimum Rust version, setup commands, and capability permissions. Check the plugin page before adding any new capability.

## Development And Packaging

- Run the app locally with `pnpm tauri dev` or the equivalent package-manager command.
- Package with `tauri build` through the project scripts or CLI integration used by the repo.
- Keep icons, bundle identifier, and platform-specific configuration aligned before packaging.

## Validation Checklist

- Frontend lint and typecheck pass.
- Rust validation passes.
- The app runs in the desktop shell, not only in a browser tab.
- Every changed command or plugin permission is exercised once end to end.
