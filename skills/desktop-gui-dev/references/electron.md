# Electron

Use this reference when the chosen stack is Electron or when the app depends on Chromium and Node ecosystem compatibility.

## Official Docs

- Electron Forge getting started: <https://www.electronforge.io/>
- Electron Forge import existing project: <https://www.electronforge.io/import-existing-project>
- Electron security guidance: <https://www.electronjs.org/docs/latest/tutorial/security>
- Electron Forge makers: <https://www.electronforge.io/config/makers>
- Electron Forge publishers: <https://www.electronforge.io/config/publishers>
- Electron Forge code signing: <https://www.electronforge.io/guides/code-signing>
- Electron Forge macOS signing: <https://www.electronforge.io/guides/code-signing/code-signing-macos>
- Electron Forge Windows signing: <https://www.electronforge.io/guides/code-signing/code-signing-windows>

If bootstrap commands, template choices, or security defaults differ from this reference, prefer the official docs.

## When To Use

- The app needs maximum web-package compatibility or browser-like runtime behavior.
- Node-based integrations are central to the product.
- The team wants a mature packaging workflow and accepts a larger desktop runtime.

## Project Creation

- Start new Forge-based apps with `npx create-electron-app@latest my-app`.
- Electron Forge documents first-party templates for `webpack`, `webpack-typescript`, `vite`, and `vite-typescript`.
- If no existing constraint exists, prefer a first-party template over a hand-rolled setup.
- If the project already exists, import it into Forge with:
  - `npm install --save-dev @electron-forge/cli`
  - `npm exec --package=@electron-forge/cli -c "electron-forge import"`

## Tooling Notes From The Official Docs

- If the project uses pnpm, set `node-linker=hoisted` in `.npmrc`.
- If the project uses Yarn 2 or newer, use `nodeLinker: node-modules`.
- These settings matter because Forge packaging expects a traditional `node_modules` layout.

## Default Working Pattern

- Keep the main process responsible for lifecycle, native APIs, menus, windows, tray, and packaging.
- Keep renderer code focused on UI and application state.
- Expose native features through preload APIs and typed wrappers instead of enabling broad renderer access.

## Important Files

- `package.json`: scripts and Forge config entry points.
- `forge.config.js` or Forge config in `package.json`: makers, publishers, packager settings, signing, and build plugins.
- `main` process entry: window creation, menus, tray, protocol handling, updater, app lifecycle.
- `preload` script: approved bridge from renderer to privileged functionality.

## Security Notes

- Keep `nodeIntegration: false` unless the task explicitly requires otherwise and the risk is understood.
- Keep `contextIsolation: true`; disabling it weakens preload isolation and also disables renderer sandboxing.
- Keep `sandbox: true` for windows that load remote or otherwise untrusted content, and expose only narrow preload APIs through `contextBridge`.
- Load local bundled content by default. If remote content is unavoidable, keep it on HTTPS or WSS and treat every navigation as untrusted until validated.
- Set a strict `Content-Security-Policy` for app HTML and any remote-content surface. Do not rely on permissive defaults in development builds.
- Keep renderer access narrow through preload and typed APIs.
- Avoid broad Node exposure in renderer code.
- Treat navigation and untrusted content as security boundaries.
- Keep Electron current and validate IPC senders for privileged operations.

## Common Feature Docs

- BrowserWindow: <https://www.electronjs.org/docs/latest/api/browser-window>
- Tray: <https://www.electronjs.org/docs/latest/api/tray>
- Menu: <https://www.electronjs.org/docs/latest/api/menu>
- globalShortcut: <https://www.electronjs.org/docs/latest/api/global-shortcut>
- Notification: <https://www.electronjs.org/docs/latest/api/notification>
- protocol: <https://www.electronjs.org/docs/latest/api/protocol>
- autoUpdater: <https://www.electronjs.org/docs/latest/api/auto-updater>
- contextBridge: <https://www.electronjs.org/docs/latest/api/context-bridge>
- ipcMain: <https://www.electronjs.org/docs/latest/api/ipc-main>

## Development And Packaging

- Run locally with `npm start` or the repo's Forge start script.
- Build distributables with `npm run make`.
- Use `npm run publish` only after makers, publishers, and signing are configured.
- Prefer Forge makers and publishers over ad hoc shell packaging when the project already uses Forge.

## Validation Checklist

- Main, preload, and renderer boundaries still match after every native feature change.
- Packaging runs through Forge, not only plain Electron execution.
- Any installer, auto-update, or code-signing change is tested in the packaged app path.
