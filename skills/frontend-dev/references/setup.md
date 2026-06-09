# Setup: scaffolding, shadcn init, Tailwind, detection

Read this when creating a new app, running `shadcn init`, configuring
`components.json`, handling Tailwind v3 vs v4, the Vite path alias, or detecting
the package manager and project shape.

## Contents

- [Detect before you build](#detect-before-you-build)
- [Package manager](#package-manager)
- [Tailwind v4 vs v3](#tailwind-v4-vs-v3)
- [Greenfield: Vite + React + TypeScript](#greenfield-vite--react--typescript)
- [The Vite path-alias gotcha](#the-vite-path-alias-gotcha)
- [Running shadcn init](#running-shadcn-init)
- [components.json](#componentsjson)
- [Next.js setup](#nextjs-setup)
- [Monorepos](#monorepos)

## Detect before you build

Always inspect the project before scaffolding or editing:

- `package.json` + lockfile → framework, React version, package manager,
  workspace/monorepo layout.
- `components.json` present → shadcn is already initialized; reuse its `style`,
  `baseColor`, `aliases`, and `iconLibrary` instead of re-running init.
- `components/ui/` (or `src/components/ui/`) → components already added; extend
  them, do not regenerate.
- Tailwind config files vs a CSS-first setup → determines v3 vs v4 handling.

When the project already exists, prefer its conventions. The defaults below are
for greenfield work only.

## Package manager

Detect from the lockfile and use it consistently:

- `package-lock.json` → npm
- `pnpm-lock.yaml` → pnpm
- `yarn.lock` → yarn
- `bun.lockb` / `bun.lock` → bun

The shadcn CLI auto-detects the package manager. Invoke it with the matching
runner (`npx shadcn@latest …`, `pnpm dlx shadcn@latest …`,
`bunx --bunx shadcn@latest …`). Do not introduce a second package manager.

## Tailwind v4 vs v3

This changes the entire setup and theming model — confirm it first.

**Tailwind v4** (current default for new shadcn projects):
- CSS-first config. The main CSS file has `@import "tailwindcss";` and theme
  tokens live in `@theme { … }` blocks — usually **no `tailwind.config.js`**.
- Uses the `@tailwindcss/vite` plugin (Vite) or `@tailwindcss/postcss`.
- shadcn theme variables are defined as CSS custom properties and mapped via
  `@theme inline`.

**Tailwind v3** (older / existing projects):
- `tailwind.config.{js,ts}` with `content`, `theme.extend`, and the
  `tailwindcss-animate` plugin.
- `postcss.config.js` with `tailwindcss` + `autoprefixer`.
- Directives `@tailwind base; @tailwind components; @tailwind utilities;` in CSS.

Match whatever the project already uses. Do not migrate v3 → v4 unless asked.

## Greenfield: Vite + React + TypeScript

The default greenfield stack. High-level sequence (consult the current official
shadcn "Vite" install guide for exact commands, since flags change):

1. Create the app: `npm create vite@latest <app> -- --template react-ts`.
2. Install and configure Tailwind (v4: `tailwind` + `@tailwindcss/vite`; add the
   plugin to `vite.config.ts` and `@import "tailwindcss";` to the main CSS).
3. **Configure the `@/*` path alias first** (see next section).
4. Run `npx shadcn@latest init`.
5. Add components as needed: `npx shadcn@latest add button card input …`.

## The Vite path-alias gotcha

shadcn resolves imports through the `@/*` alias. In a Vite project this alias is
**not** configured out of the box, and `shadcn init` will error or place files
incorrectly if it is missing. Configure it *before* init in all three places:

- `tsconfig.json` (and `tsconfig.app.json` for the Vite split-config template):
  ```jsonc
  {
    "compilerOptions": {
      "baseUrl": ".",
      "paths": { "@/*": ["./src/*"] }
    }
  }
  ```
- `vite.config.ts`:
  ```ts
  import path from "node:path";
  // resolve: { alias: { "@": path.resolve(__dirname, "./src") } }
  ```
  Install `@types/node` so `path` and `__dirname` type-check.

Only after the alias resolves should you run `npx shadcn@latest init`.

## Running shadcn init

`npx shadcn@latest init` prompts for (and writes `components.json` with):

- **style** — `new-york` (default recommendation) or `default`.
- **base color** — neutral / gray / zinc / stone / slate.
- **CSS variables** — yes (recommended; enables theming via custom properties).

It also installs base dependencies (`tailwind-merge`, `clsx`, `class-variance-
authority`, the icon library) and creates the `cn()` util at `lib/utils.ts`.

Run init **once**. To add more components later, use `add`, not another `init`.

## components.json

The shadcn config that downstream `add` commands read. Key fields:

- `style` — component style preset (`new-york` / `default`).
- `tailwind.baseColor` — neutral palette used for generated tokens.
- `tailwind.cssVariables` — `true` to theme via CSS custom properties.
- `tailwind.config` — path to the Tailwind config (empty string for v4).
- `rsc` — `true` for React Server Components (Next.js App Router); `false` for a
  Vite SPA, so generated components omit the `"use client"` directive.
- `tsx` — TypeScript components.
- `aliases` — import aliases (`components`, `utils`, `ui`, `lib`, `hooks`). These
  must line up with the `@/*` path alias.
- `iconLibrary` — `lucide` by default.

Keep `components.json` consistent with the actual alias and framework, or
generated components will import from the wrong paths or include/omit
`"use client"` incorrectly.

## Next.js setup

When the project is (or should be) Next.js App Router:

- `npx shadcn@latest init` detects Next.js and sets `rsc: true`.
- Interactive components (anything using hooks, state, or Radix client behavior)
  need `"use client"` at the top of the file that uses them. shadcn handles this
  for generated primitives; your composed components must add it when they become
  client components.
- See [architecture.md](architecture.md) for the RSC vs client boundary.

## Monorepos

In a workspace (pnpm/turbo/nx), shadcn supports a monorepo setup where the UI
package and the consuming app each have a `components.json`. Detect the workspace
layout, place components in the shared UI package when that is the convention,
and keep aliases consistent across packages. Consult the official shadcn
"Monorepo" guide for the current layout.
