# Wails v3

Use this reference when the repo uses `wails3`, imports `github.com/wailsapp/wails/v3`, or points at `v3alpha.wails.io`.

## Version Boundary

- This reference targets the current public Wails v3 alpha line and the `wails3` CLI.
- If the repo imports `github.com/wailsapp/wails/v2` or uses the `wails` CLI, switch to [wails.md](wails.md).
- Because v3 is still alpha, treat the official docs as authoritative whenever CLI flags, runtime APIs, generated layout, or packaging behavior differ from this reference.

## Official Docs

- Home and quickstart: <https://v3alpha.wails.io/>
- Installation: <https://v3alpha.wails.io/quick-start/installation/>
- First app and generated layout: <https://v3alpha.wails.io/getting-started/your-first-app/>
- Frontend runtime: <https://v3alpha.wails.io/reference/frontend-runtime/>
- Build and packaging guide: <https://v3alpha.wails.io/guides/build/building/>
- CLI reference: <https://v3alpha.wails.io/guides/cli/>
- Bindings: <https://v3alpha.wails.io/features/bindings/methods>
- Windows basics: <https://v3alpha.wails.io/features/windows/basics>

## Prerequisites

- Wails v3 currently requires Go 1.25 or later.
- Install the CLI with `go install github.com/wailsapp/wails/v3/cmd/wails3@latest`.
- Run `wails3 doctor` after installation to verify platform-specific dependencies before scaffolding or debugging.
- Because v3 is still alpha, prefer the current installation guide if local repo notes disagree.

## When To Use

- The repo is already on Wails v3 or explicitly wants the v3 runtime and `wails3` workflow.
- The team wants Go services plus generated frontend bindings and is comfortable tracking alpha-era changes.
- Frontend access to runtime features such as dialogs, menus, or window APIs is part of the design.

## CLI Setup

- Use `wails3 init -l` to inspect available templates before scaffolding.
- Create a project with `wails3 init -n myapp -t <template>`.

## Important Files

- `main.go`: application options, service registration, and window lifecycle.
- `frontend/`: frontend source plus generated `bindings/`.
- `build/`: build configuration and platform packaging material.
- `Taskfile.yml` when present: task shortcuts shipped by the template or the repo.

## Default Working Pattern

- Register Go services in the application config and consume them through generated bindings instead of ad hoc bridge code.
- Treat generated files in `frontend/bindings/` as build output. Regenerate them instead of editing them manually.
- Import `@wailsio/runtime` from the frontend when using runtime features, and keep runtime calls behind thin typed wrappers in app code.
- Confirm whether the repo uses JavaScript or TypeScript bindings and preserve that choice.

## Development And Packaging

- Use the repo's dev workflow or `wails3 dev` during local iteration.
- Build production artifacts with `wails3 build`.
- Use `wails3 package` when release work needs platform packages or app bundles instead of raw build output.
- `wails3 build` and `wails3 package` are wrappers over the project `Taskfile.yml`; preserve repo-specific task customizations when present.
- Regenerate bindings with `wails3 generate bindings` when the repo workflow requires it or generated output drifts.

## Validation Checklist

- `wails3 doctor` is clean or any reported gaps are explicitly understood.
- The app runs in the desktop shell, not only in the frontend dev server.
- Service registrations, generated bindings, and frontend imports stay aligned.
- Any runtime feature touched from the frontend is exercised once end to end.
- Any packaging or installer change is re-checked against the current v3 docs before release work lands.
