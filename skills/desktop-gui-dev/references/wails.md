# Wails v2

Use this reference when the chosen stack is Wails v2 or when the repo imports `github.com/wailsapp/wails/v2` and uses the `wails` CLI.

## Version Boundary

- This reference targets Wails v2 and the `wails` CLI.
- If the repo uses `wails3`, imports `github.com/wailsapp/wails/v3`, or points at `v3alpha.wails.io`, stop and switch to [wails-v3.md](wails-v3.md) before changing commands, bindings, or runtime assumptions.
- Wails v3 currently lives under `v3alpha.wails.io` and has a different frontend runtime surface, including JavaScript-accessible dialogs and menus.
- Wails v3 quick start: <https://v3alpha.wails.io/quick-start/installation/>
- Wails v3 frontend runtime: <https://v3alpha.wails.io/reference/frontend-runtime/>

## Official Docs

- Installation: <https://wails.io/docs/gettingstarted/installation/>
- Creating a project: <https://wails.io/docs/gettingstarted/firstproject>
- Building: <https://wails.io/docs/gettingstarted/building/>
- Project config: <https://wails.io/docs/reference/project-config/>
- Runtime introduction: <https://wails.io/docs/reference/runtime/intro/>
- Runtime window API: <https://wails.io/docs/reference/runtime/window/>
- Runtime menu API: <https://wails.io/docs/reference/runtime/menu/>
- Runtime dialog API: <https://wails.io/docs/reference/runtime/dialog/>

If CLI flags, templates, or generated layout details differ from this reference, prefer the official docs.

## Prerequisites

- Go 1.21+ is required.
- macOS 15+ requires Go 1.23.3+.
- NPM with Node 15+ is required.
- Run `wails doctor` after installation to verify platform-specific dependencies.

## When To Use

- The team prefers Go for backend logic.
- The app still benefits from a web frontend and desktop shell.
- The project needs a lighter path than Electron but does not want Rust as the native layer, and it is staying on the stable v2 line.

## CLI Setup

- Install the Wails CLI with `go install github.com/wailsapp/wails/v2/cmd/wails@latest`.
- Run `wails doctor` after installation to verify platform dependencies.

## Project Creation

- Create a project with `wails init -n myproject -t <template>`.
- Official templates include `svelte`, `react`, `vue`, `preact`, `lit`, and `vanilla`, each with `-ts` variants.
- Match the template to the frontend the user actually wants instead of forcing a framework.

## Important Files

- `main.go`: app entry point.
- `frontend/`: frontend project files.
- `wails.json`: project configuration.
- `build/`: generated build assets plus platform-specific packaging material.

## Default Working Pattern

- Keep Go application logic and desktop integrations out of the frontend.
- Use generated or centralized wrappers for Go-to-frontend bindings instead of spreading direct bridge calls through the UI.
- Keep frontend tooling idiomatic to the chosen template inside `frontend/`.
- In Wails v2, runtime calls at startup should prefer `OnDomReady`; `OnStartup` is too early for some window operations.
- In Wails v2, menu and dialog APIs are not supported in the JavaScript runtime, so implement those flows on the Go side.
- Do not carry those JavaScript-runtime limitations over to Wails v3 without re-checking the alpha docs.

## Common Feature Docs

- Runtime introduction: <https://wails.io/docs/reference/runtime/intro/>
- Window API: <https://wails.io/docs/reference/runtime/window/>
- Menu API: <https://wails.io/docs/reference/runtime/menu/>
- Dialog API: <https://wails.io/docs/reference/runtime/dialog/>

## Development And Packaging

- Use the repo's dev workflow or `wails dev` during local iteration.
- Build production binaries with `wails build`.
- On Linux systems missing `webkit2gtk-4.0`, Wails documents using `-tags webkit2_41`.

## Validation Checklist

- `wails doctor` is clean or any reported gaps are explicitly understood.
- The app runs in the desktop shell, not only in the frontend dev server.
- Build output works from `build/bin`, and any platform-specific packaging assets are aligned with the current app identity.
