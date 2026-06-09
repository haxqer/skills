---
name: frontend-dev
description: Build, debug, and review modern React frontends with shadcn/ui as the default component system. Use when Codex needs to scaffold or extend a Vite + React + TypeScript (or Next.js) web app, install and compose shadcn/ui components, configure Tailwind and theming, wire forms, data tables, server/client state, dark mode, routing, or accessibility, or diagnose component, build, and browser runtime issues in a shadcn-based frontend.
---

# Frontend Dev

## Overview

Use this skill to build, extend, debug, and review professional React web
frontends where **shadcn/ui** (https://github.com/shadcn-ui/ui) is the default
component system.

The single most important thing to internalize: **shadcn/ui is not a runtime
dependency.** It is a CLI that copies accessible, Radix-based component *source*
into the project (typically `components/ui/` or `src/components/ui/`). Once
copied, those files belong to the project and are meant to be read and edited.
Treating shadcn/ui like a normal npm component library — installing a `shadcn-ui`
package, never touching the generated files, or reinstalling to "upgrade" — is
the most common and most damaging mistake. Build on the copied source; do not
fight it.

This skill covers shadcn/ui specifically. For non-shadcn UI, native desktop
toolkits, or game UIs, see the boundaries in "When Not To Use".

## Start Here

Before editing anything, detect what already exists. Read source over stale
docs or memory.

- Determine intent: new app, feature addition, bug fix, refactor, theming, or
  review.
- Inspect `package.json` and the lockfile for: framework (Vite, Next.js, Remix,
  Astro, TanStack Start), React version, the package manager (npm, pnpm, yarn,
  bun), and whether this is a monorepo/workspace.
- Look for `components.json` (the shadcn config) and the existing
  `components/ui/` directory. If they exist, the project already uses shadcn —
  match its style, base color, aliases, and conventions instead of re-running
  init.
- Detect the **Tailwind version**: v4 uses CSS-first config (`@import "tailwindcss"`
  and `@theme` in a CSS file, usually no `tailwind.config.js`); v3 uses
  `tailwind.config.{js,ts}`. The setup steps differ — see
  [references/setup.md](references/setup.md).
- Prefer the repository's existing stack. Apply the defaults below only for
  greenfield work or when the repo leaves a choice open.

## Default Stack When Unspecified

Treat this as the greenfield baseline. Only diverge when the user, repo, or
target requirements clearly justify it.

- Framework: **Vite + React + TypeScript** (single-page app). Next.js (App
  Router) is the documented alternative when SSR/RSC, SEO, or full-stack routes
  are needed — see [references/architecture.md](references/architecture.md).
- Components: **shadcn/ui**, `new-york` style, on **Tailwind CSS v4**.
- Routing: **React Router** for the Vite SPA (Next.js App Router handles its own).
- Icons: **lucide-react** (shadcn's default icon set).
- Forms: **react-hook-form + zod**, via the shadcn `Form` component.
- Server state: **TanStack Query**. Client/UI state: **Zustand**.
- Tables: **TanStack Table**, via the shadcn data-table pattern.

## Core Rules for shadcn/ui

These encode the things that most often go wrong. Read
[references/components.md](references/components.md) for the worked examples.

- **Use the CLI, not a package.** Initialize with `npx shadcn@latest init` and
  add components with `npx shadcn@latest add <name>`. The old `shadcn-ui` npm
  package is deprecated — do not install or import it.
- **You own the generated source.** Components land in your repo and are yours
  to edit. Do not treat `components/ui/` as untouchable vendor code, and never
  hand-write a primitive (button, dialog, input, …) that the registry already
  provides — add it and adapt it.
- **Reuse before reinventing.** Check the existing `components/ui/` and the
  shadcn registry/blocks first. Compose feature components from primitives
  rather than restyling raw HTML.
- **Compose className with `cn()`.** Use the generated `cn()` helper
  (clsx + tailwind-merge) so conditional and overriding classes merge correctly.
  Keep component variants in `cva` definitions rather than ad-hoc conditionals.
- **Preserve accessibility.** shadcn components wrap Radix primitives that are
  keyboard- and screen-reader-accessible by default. When you customize, keep
  the `aria-*` attributes, focus management, and keyboard interactions intact.
- **Tailwind version matters.** Confirm v4 vs v3 before changing config or
  theme tokens; the file layout and theming syntax differ.
- **Vite path-alias gotcha.** For a Vite project, configure the `@/*` path alias
  in `tsconfig.json`, `tsconfig.app.json`, and `vite.config.ts` (and the Tailwind
  setup) *before* running `npx shadcn@latest init`, or init will fail to resolve
  aliases. See [references/setup.md](references/setup.md).
- **Blocks and third-party registries.** Add prebuilt blocks and components from
  external registries with `npx shadcn@latest add <url>`.

## Implementation Path

1. **Detect** the framework, package manager, Tailwind version, and existing
   shadcn config (see "Start Here").
2. **Init or align config.** For greenfield, scaffold Vite + React + TS, set up
   Tailwind and the path alias, then `npx shadcn@latest init`. For an existing
   project, reuse its `components.json` and conventions.
3. **Add components from the registry** before writing UI by hand. Pull only what
   the feature needs.
4. **Compose feature UI** from the primitives, merging classes with `cn()` and
   keeping accessibility intact.
5. **Wire behavior:** forms with react-hook-form + zod, tables with TanStack
   Table, server state with TanStack Query, local UI state with Zustand.
6. **Theme** with CSS variables and wire dark mode — see
   [references/theming.md](references/theming.md).
7. **Validate in a real browser:** run the dev server, exercise the changed flow,
   check the console, responsiveness, and keyboard accessibility.

## Reference Routing

- Read [references/setup.md](references/setup.md) when scaffolding a new app,
  running `shadcn init`, configuring `components.json`, handling Tailwind v3 vs
  v4, the Vite path alias, or package-manager/monorepo detection.
- Read [references/components.md](references/components.md) when adding or
  customizing components, using `cn()` and `cva`, building forms (react-hook-form
  + zod), data tables (TanStack Table), icons (lucide), or pulling blocks and
  third-party registries.
- Read [references/theming.md](references/theming.md) when working with CSS
  variables, design tokens, base color, or dark mode (`next-themes` /
  `.dark` class).
- Read [references/architecture.md](references/architecture.md) when deciding
  folder structure, routing, state/data layering, or when the project is Next.js
  and you must reason about RSC vs `"use client"` boundaries.
- Read [references/quality.md](references/quality.md) when checking accessibility,
  responsiveness, performance, or debugging a blank screen, unstyled components,
  hydration errors, or other browser runtime issues.

## Trigger Examples

- "Scaffold a Vite + React dashboard using shadcn/ui with a sidebar and data table."
- "Add a settings form with validation to this shadcn app."
- "Wire dark mode and a theme switcher into this project."
- "This shadcn dialog isn't accessible / closes on the wrong key — fix it."
- "Components render unstyled after I added shadcn to my Vite app — what's wrong?"
- "Add a TanStack Query data table with sorting and pagination using shadcn."
- "Review this React + shadcn frontend before we ship."

## When Not To Use

- Phaser or other browser **games** → use the `phaser` skill.
- **Native desktop** apps (Tauri, Qt, SwiftUI) → use `desktop-gui-dev`.
- Pure **visual/design exploration** (palettes, style systems, mockups) with no
  shadcn implementation → leave to a design-focused skill.
- Frontends that deliberately **do not use shadcn/ui** (e.g. a different
  component library or hand-rolled design system) — apply general React judgment
  rather than this skill's shadcn-specific rules.

## Check Before You Finish

- Components come from the registry/`components/ui/`, not duplicated by hand.
- Accessibility is intact: keyboard navigation, focus, and `aria-*` still work.
- Dark mode and theming render correctly in both light and dark.
- The layout is responsive at small and large viewports.
- The dev server runs and the browser console is free of relevant errors.
- The changed flow was exercised in a real browser, not just a green build.
