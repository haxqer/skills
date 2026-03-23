# Desktop GUI Release Checklist

Use this reference before calling a desktop GUI app ready for external testing or release.

## Scope

- This is a cross-stack release backstop, not a substitute for the chosen stack's official packaging, signing, notarization, or store-submission docs.
- Before changing signing, notarization, installers, updater feeds, or release CI, read the matching stack reference and the official vendor docs first.
- If a command, entitlement, certificate input, or store requirement is ambiguous, stop and verify it in the official docs instead of inferring it from another stack.

## Stack-Specific Release Docs

- For Tauri packaging, updater, and plugin-related release work, read `references/tauri.md`.
- For Electron Forge makers, publishers, and code-signing work, read `references/electron.md`.
- For Wails v2 build and packaging details, read `references/wails.md`.
- For Wails v3 build and packaging details, read `references/wails-v3.md` and the current official `v3alpha.wails.io` docs.
- For native toolkit release work, read `references/native-toolkits.md` plus the official toolkit docs linked there.

## Build Readiness

- Version metadata is updated in every required manifest.
- App name, bundle identifier, icons, and installer metadata are aligned.
- Production environment configuration is separated from local development defaults.
- Update, analytics, crash reporting, and logging endpoints are pointed at the correct environment.

## Packaging And Signing

- Build the packaged app for each target OS, not just the development runner.
- Verify signing inputs, certificates, notarization prerequisites, or store packaging requirements as appropriate for the platform.
- Confirm installer behavior, uninstall behavior, upgrade behavior, and data-directory preservation.
- On macOS, verify bundle identifier, entitlements, hardened runtime, notarization, stapling, and first-launch behavior on a clean user profile or machine.
- On Windows, verify signing inputs, installer technology, upgrade path, and any unsigned or SmartScreen-sensitive failure mode.
- On Linux, verify package targets, desktop-file metadata, icon integration, and runtime dependency expectations for the chosen distribution path.

## Security Release Gate

- For Electron, verify the packaged app still keeps `nodeIntegration: false`, `contextIsolation: true`, the intended sandbox posture, a strict `Content-Security-Policy`, and explicit navigation handling for any remote content.
- For Tauri, verify capability files and custom command exposure are both still scoped as intended. Do not assume a narrow capability file also narrows `invoke_handler` command access.
- For any stack that touches filesystem, shell, updater, deep-link, or auto-start features, re-check the privileged surface in the packaged app path, not only in development mode.

## Functional Smoke Test

- Clean install works.
- First launch works.
- Main user flow works.
- Settings persist across relaunch.
- File dialogs, tray, menus, shortcuts, notifications, and deep links work when those features exist.
- The app exits, relaunches, and updates cleanly.

## Data Safety

- Migration path from the previous released version is tested.
- Export, import, backup, or recovery paths are tested when the app stores meaningful user data.
- Failure cases such as missing files, denied permissions, and corrupted local state produce recoverable errors.

## Platform Matrix

- Verify behavior on the operating systems the user claims to support.
- Check high-DPI rendering, system theme integration, keyboard shortcuts, focus behavior, and file path handling on each target OS.
- Confirm any platform-specific fallbacks or unsupported states are explicit rather than silent.

## Release Note Hygiene

- Document notable user-visible changes, migration notes, and known limitations.
- Call out any skipped verification so release risk is visible.
