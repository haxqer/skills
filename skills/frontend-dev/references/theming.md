# Theming: CSS variables, design tokens, dark mode

Read this when working with the base color, CSS variables, design tokens, or
dark mode.

## Contents

- [How shadcn theming works](#how-shadcn-theming-works)
- [Tailwind v4 token layout](#tailwind-v4-token-layout)
- [Tailwind v3 token layout](#tailwind-v3-token-layout)
- [Customizing the theme](#customizing-the-theme)
- [Dark mode](#dark-mode)

## How shadcn theming works

When `cssVariables` is enabled in `components.json`, shadcn defines a set of
semantic color tokens as CSS custom properties (e.g. `--background`,
`--foreground`, `--primary`, `--muted`, `--border`, `--ring`, `--card`,
`--destructive`). Components reference these via Tailwind utilities like
`bg-background`, `text-foreground`, `border-border`. Theming therefore means
editing the CSS variables — not editing every component.

Light values live on `:root`; dark values live under a `.dark` selector. Switch
themes by toggling the `dark` class on `<html>`.

## Tailwind v4 token layout

In v4 the tokens live in your main CSS file alongside `@import "tailwindcss";`.
The shadcn variables are defined on `:root` / `.dark` and exposed to Tailwind via
`@theme inline`:

```css
@import "tailwindcss";

:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  /* … */
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  /* … */
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  /* … */
}
```

v4 uses `oklch()` colors by default. Keep that format when editing so the palette
stays consistent.

## Tailwind v3 token layout

In v3 the variables go in the `@layer base` block of your CSS (HSL channel
triples), and `tailwind.config` maps them under `theme.extend.colors`:

```css
@layer base {
  :root { --background: 0 0% 100%; --foreground: 0 0% 3.9%; /* … */ }
  .dark { --background: 0 0% 3.9%; --foreground: 0 0% 98%; /* … */ }
}
```

```ts
// tailwind.config: colors: { background: "hsl(var(--background))", … }
```

## Customizing the theme

- Change the **base color** by editing the variable values (or re-init only if
  nothing is customized yet).
- Add **new semantic tokens** by defining the variable on `:root` and `.dark`
  and exposing it (v4: add to `@theme inline`; v3: add to `tailwind.config`).
- Prefer semantic tokens (`--primary`, `--muted`) over hard-coded colors in
  components so dark mode and rebranding stay centralized.
- Generate cohesive palettes from the shadcn theming docs / the "Themes" page
  rather than picking values ad hoc.

## Dark mode

The mechanism is the `.dark` class on the `<html>` element; the implementation
depends on the framework.

**Vite SPA** — there is no `next-themes`. Either:
- Add a small theme provider that reads `localStorage`, respects
  `prefers-color-scheme`, and toggles the `dark` class on
  `document.documentElement`; or
- Use a community library, but a tiny hand-rolled provider is usually enough.

Avoid a flash of the wrong theme by applying the stored/system theme before first
paint (an inline script in `index.html` or setting the class synchronously on
load).

**Next.js** — use `next-themes`:
- Wrap the app in `ThemeProvider` with `attribute="class"`.
- Add `suppressHydrationWarning` to `<html>`.
- Build a theme toggle that calls `setTheme("light" | "dark" | "system")`.

In both cases, verify the toggle actually re-themes shadcn components and that
contrast remains accessible in both modes.
