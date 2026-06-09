# Visual fidelity: making output actually look like shadcn/ui

Read this when the result "doesn't look like shadcn," before applying any brand
color, when building a dashboard/sidebar/admin shell, or to run the comparison
check before finishing.

The skill can scaffold a technically-correct shadcn app that still looks wrong —
like a generic admin template instead of ui.shadcn.com. This file is about
closing that gap. The look is not decoration; it is the reason to use shadcn at
all.

## Contents

- [What "looks like shadcn" means](#what-looks-like-shadcn-means)
- [The three ways output drifts](#the-three-ways-output-drifts)
- [Use real components, not memory](#use-real-components-not-memory)
- [Palette discipline](#palette-discipline)
- [Use official blocks for app shells](#use-official-blocks-for-app-shells)
- [Brand color the right way](#brand-color-the-right-way)
- [The comparison check](#the-comparison-check)

## What "looks like shadcn" means

The shadcn aesthetic is specific and restrained. Concretely:

- **Neutral base color** (zinc / slate / stone / gray / neutral). Backgrounds are
  near-white in light mode, near-black in dark mode.
- **Near-black `primary`** in the `new-york` style. Primary buttons are dark, not
  a saturated brand color.
- **Subtle, low-contrast borders** (`border` via `--border`) and generous,
  consistent spacing. Cards are white with a hairline border, not heavy shadows.
- **Muted secondary text** via `text-muted-foreground`, not pure gray hex values.
- **Small, consistent radius** and `lucide` icons at `size-4`.
- **Sidebars use the `--sidebar*` tokens** and are light/neutral by default — not
  a dark navy slab.

If the page has a dark colored sidebar, bright primary buttons, heavy shadows, or
pure-hex grays, it has drifted away from shadcn.

## The three ways output drifts

Almost every "this doesn't look like shadcn" case is one of these:

1. **Approximation** — components were hand-written to *resemble* shadcn instead
   of being the real source. Spacing, radius, and color slowly diverge.
2. **Palette hijack** — the neutral theme was overwritten with brand colors (blue
   primary, dark sidebar), so even real components stop reading as shadcn.
3. **Hand-assembled shell** — a dashboard/sidebar layout was built from scratch
   instead of from an official block, missing the curated proportions.

Fixing the look means eliminating all three.

## Use real components, not memory

The registry is the source of truth. Do not reconstruct a `Button`, `Sidebar`,
`Card`, or `Table` from memory:

- Run `npx shadcn@latest add <component>` and use what it writes.
- If the CLI cannot run (no network/sandbox), copy the exact current source from
  the registry (`https://ui.shadcn.com/docs/components/<name>`) rather than
  inventing markup — or stop and tell the user shadcn isn't installed.
- A hand-written lookalike is never acceptable as a substitute for a registry
  primitive. It is the single most common reason output looks "off."

## Palette discipline

The neutral palette is load-bearing. Treat it as fixed unless the user explicitly
asks to rebrand:

- Do **not** set `bg-blue-600`, `bg-slate-900`, etc. directly on buttons,
  sidebars, or headers. Use the semantic tokens (`bg-primary`,
  `bg-background`, `bg-sidebar`, `bg-card`).
- Do **not** override `--primary` to a brand hue just to "add color." A shadcn
  dashboard is mostly neutral; color appears sparingly (a single accent, status
  badges, charts).
- The sidebar must use `--sidebar`, `--sidebar-foreground`, `--sidebar-accent`,
  etc. A dark sidebar is a deliberate theme, not a default — don't introduce it
  by hand.
- Status/category color belongs in small elements (`Badge` variants, chart
  series), not large surfaces.

## Use official blocks for app shells

For anything resembling an application — dashboards, admin consoles, settings,
sidebars — start from a shadcn **block**, not a blank layout:

- Sidebars / app shells: `npx shadcn@latest add sidebar-07` (or browse
  `https://ui.shadcn.com/blocks` and pick the closest one).
- Dashboards: `dashboard-01`.
- Login/auth: `login-03`, etc.

Add the block, then adapt its content to the domain. The block already encodes
the spacing, header, sidebar tokens, and responsive behavior that make it look
finished. Hand-assembling these is where homemade-looking layouts come from.

## Brand color the right way

When the user genuinely wants brand color, do it through the theme system so it
stays cohesive and dark-mode-correct — never by sprinkling Tailwind color classes:

1. Generate a full token set (all states, light + dark) from the shadcn theming
   docs / Themes page or a theme generator, keyed to the brand hue.
2. Set the values on `:root` / `.dark` and expose them (`@theme inline` in v4;
   `tailwind.config` in v3) — see [theming.md](theming.md).
3. Keep the brand color scoped: usually `primary` and maybe an `accent`, with the
   rest of the palette staying neutral. Resist coloring large surfaces.

This keeps the shadcn structure while letting the brand show through, instead of
producing a different-looking template.

## The comparison check

Before declaring a UI done, compare it to the real thing:

1. Run the dev server and screenshot the page.
2. Open the closest ui.shadcn.com example or block in another tab.
3. Check, side by side: base color neutral? primary near-black (or correctly
   themed)? borders subtle? spacing consistent? sidebar using sidebar tokens?
   icons `lucide` at the right size? Does it read as shadcn?
4. If it reads as "a generic admin template," identify which of the three drift
   modes happened and fix it — re-add the real component, restore the neutral
   tokens, or swap the hand-built shell for a block.

A green build and a working flow are not enough; the visual match is part of the
definition of done.
