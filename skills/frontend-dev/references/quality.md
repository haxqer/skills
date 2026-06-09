# Quality: accessibility, responsiveness, performance, debugging

Read this when checking accessibility, responsiveness, or performance, or when
debugging a blank screen, unstyled components, hydration errors, or other browser
runtime issues.

## Contents

- [Accessibility](#accessibility)
- [Responsive design](#responsive-design)
- [Performance](#performance)
- [Browser validation loop](#browser-validation-loop)
- [Debugging checklist](#debugging-checklist)

## Accessibility

shadcn components are accessible by default because they wrap Radix primitives.
Your job is to not break that and to keep the surrounding markup accessible:

- Preserve `aria-*` attributes, roles, focus management, and keyboard
  interactions when you customize a primitive.
- Use semantic HTML (`button`, `nav`, `main`, `label`, headings in order). Don't
  replace a `button` with a clickable `div`.
- Every input has an associated label (the shadcn `Form`/`Label` pattern wires
  this up — keep `FormLabel`/`FormMessage` in the tree).
- Icon-only buttons need an accessible name (`aria-label` or visually-hidden
  text).
- Maintain visible focus styles (shadcn's `--ring` token) — don't remove focus
  outlines.
- Check color contrast in both light and dark themes.
- Verify keyboard flows for interactive primitives (dialogs trap focus and close
  on Escape, menus arrow-navigate, etc.).

## Responsive design

- Mobile-first: base styles for small screens, layer `sm:`/`md:`/`lg:` overrides.
- Test at narrow and wide viewports; check that dialogs, tables, and sidebars
  adapt (tables often need horizontal scroll or a stacked layout on mobile).
- Use the shadcn `Sidebar`/`Sheet` patterns for responsive navigation rather
  than hand-rolling breakpoints.

## Performance

- Code-split routes (`React.lazy` + `Suspense`, or the framework's lazy routes).
- Let TanStack Query handle caching; avoid redundant fetches and over-broad
  invalidation.
- Memoize expensive renders deliberately, not reflexively.
- Optimize images (Next.js `next/image`; for Vite, appropriately sized assets
  and lazy loading).
- Watch bundle size; treat large-chunk warnings as a prompt to check whether a
  real lazy-load boundary exists, not an automatic failure.

## Browser validation loop

A green build is not done. After non-trivial changes:

1. Run the dev server (`npm run dev` or the project's script).
2. Open the changed flow in a browser.
3. Check the console for errors/warnings and the network tab for failed requests.
4. Exercise interactions with the keyboard, not just the mouse.
5. Resize to a mobile width and re-check layout.
6. Toggle dark mode and confirm theming/contrast.

## Debugging checklist

**Components render unstyled / no Tailwind:**
- Tailwind not wired: missing `@import "tailwindcss";` (v4) or the
  `@tailwind` directives (v3); CSS file not imported in `main.tsx`.
- v4: the `@tailwindcss/vite` (or PostCSS) plugin isn't configured.
- `content` globs (v3) don't include the component paths.

**Imports fail / `@/...` not found:**
- The `@/*` path alias is missing or inconsistent across `tsconfig*.json` and
  `vite.config.ts`. Align all of them (see setup.md). `components.json` aliases
  must match.

**`shadcn add` puts files in the wrong place or errors:**
- `components.json` aliases or the path alias are misconfigured. Fix the alias,
  then re-run.

**Next.js: "useState/useEffect in a Server Component":**
- The file needs `"use client"` at the top. Add it to the interactive component;
  push the boundary down rather than marking the whole page client.

**Hydration mismatch (Next.js):**
- Server and client rendered different markup — often a theme/`localStorage`
  read at render time or a non-deterministic value. Gate browser-only reads
  behind an effect, and use `next-themes` with `suppressHydrationWarning` for
  theme.

**Dialog/menu won't open or close, focus stuck:**
- A required Radix part is missing (e.g. `Trigger`/`Portal`/`Content`), or a
  customization removed `aria`/focus wiring. Compare against the freshly
  generated primitive.

**Blank screen:**
- Check the console first. Common causes: an uncaught error in a top-level
  component, a failed dynamic import, or a router with no matching route and no
  fallback.
