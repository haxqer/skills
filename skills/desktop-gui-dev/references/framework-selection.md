# Desktop GUI Framework Selection

Use this reference when the user has not fixed the stack yet or is considering a migration.

## Quick Choice Heuristic

- Choose Tauri for a web UI plus a small native shell, especially when Rust is acceptable and bundle size matters.
- Choose Electron for the broadest Chromium and Node ecosystem support, especially when bundle size is secondary.
- Choose Wails for a Go backend with a web UI.
- Choose a native toolkit such as Qt, SwiftUI, WinUI, GTK, or .NET MAUI when native widgets, platform fidelity, or accessibility behavior matter more than web-stack reuse.

## Decision Questions

- Which operating systems must ship first?
- Does the app need deep filesystem access, background services, global shortcuts, auto-start, or tray behavior?
- Is offline support or local persistence central to the product?
- Does the team prefer Rust, TypeScript and Node, Go, C++, or native platform languages?
- Is bundle size a hard constraint?
- Does the UI need browser-style rendering freedom or native control fidelity?
- How much packaging, signing, and updater complexity is acceptable?

## Tradeoff Summary

### Tauri

- Strengths: small bundles, strong Rust integration, good security posture, web UI flexibility.
- Costs: native extension work usually means Rust; ecosystem is smaller than Electron.
- Good fit: cross-platform desktop utilities, productivity apps, internal tools, local-first products.

### Electron

- Strengths: mature ecosystem, predictable browser environment, strong Node integration, many existing examples.
- Costs: larger bundles, higher memory footprint, more care needed around security boundaries.
- Good fit: teams already strong in JavaScript and products that depend on Chromium or Node libraries.

### Wails

- Strengths: Go backend, straightforward desktop shell, web UI reuse.
- Costs: smaller ecosystem and fewer examples than Electron or Tauri; confirm whether the repo is on stable v2 or the v3 alpha line before reusing commands or runtime assumptions.
- Good fit: Go-heavy teams building practical desktop tools.

### Native toolkits

- Strengths: native controls, platform fidelity, deep OS integration, mature accessibility support.
- Costs: less code sharing across platforms unless the toolkit is explicitly cross-platform.
- Good fit: polished end-user desktop software where native behavior is part of the value.

## Official Docs Hubs

- Tauri: <https://v2.tauri.app/start/create-project/>
- Electron Forge: <https://www.electronforge.io/>
- Electron core docs: <https://www.electronjs.org/docs/latest/>
- Wails: <https://wails.io/docs/gettingstarted/installation/>
- Wails v3 alpha: <https://v3alpha.wails.io/>
- Qt: <https://doc.qt.io/>
- SwiftUI: <https://developer.apple.com/swiftui/>
- AppKit: <https://developer.apple.com/documentation/AppKit>
- WinUI: <https://learn.microsoft.com/en-us/windows/apps/winui/winui3/>
- WPF: <https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview/>
- GTK: <https://docs.gtk.org/gtk4/getting_started.html>
- .NET MAUI: <https://learn.microsoft.com/en-us/dotnet/maui/>

## Default Recommendation Pattern

- If the repo already uses a stack, keep it.
- If the user wants a modern cross-platform app with a web UI and no strong Node dependency, start with Tauri.
- If the user needs maximum web-package compatibility or a browser-like runtime, start with Electron.
- If the team prefers Go or already has Go services or domain logic to reuse, start with Wails and confirm the v2 or v3 boundary immediately.
- If the user needs a truly native UI, avoid forcing a web shell.

## After Choosing

- Read `references/tauri.md` for Tauri scaffolding, capabilities, and packaging flow.
- Read `references/electron.md` for Electron Forge bootstrap, preload boundaries, and packaging.
- Read `references/wails.md` for Wails v2 CLI setup, template selection, and build flow.
- Read `references/wails-v3.md` for Wails v3 `wails3` setup, bindings, frontend runtime, and build flow.
- Read `references/native-toolkits.md` for native toolkit structure, selection heuristics, and validation focus.
