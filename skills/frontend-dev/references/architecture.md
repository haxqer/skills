# Architecture: structure, routing, state, data

Read this when deciding folder structure, routing, or state/data layering, or
when the project is Next.js and you must reason about RSC vs `"use client"`.

## Contents

- [Folder structure](#folder-structure)
- [Routing](#routing)
- [State: client vs server](#state-client-vs-server)
- [Data fetching with TanStack Query](#data-fetching-with-tanstack-query)
- [Next.js: RSC vs client components](#nextjs-rsc-vs-client-components)
- [Respect existing conventions](#respect-existing-conventions)

## Folder structure

A clear default for the Vite SPA (adapt to the repo's existing layout):

```
src/
  components/
    ui/          # shadcn primitives (generated, owned)
    <feature>/   # composed feature components
  features/      # or feature-first: colocate components + hooks + api per feature
  hooks/
  lib/           # utils.ts (cn), api clients, helpers
  routes/ | pages/
  stores/        # Zustand stores
  App.tsx
  main.tsx
```

Keep shadcn primitives in `components/ui/` separate from feature components.
Colocate feature-specific hooks, queries, and components so a feature is easy to
find and delete. Don't over-engineer a small app into deep folders.

## Routing

- **Vite SPA** → **React Router**. Define routes centrally, lazy-load route
  components with `React.lazy` + `Suspense` for code-splitting, and keep layout
  routes for shared chrome (sidebar, header). TanStack Router is a typed
  alternative if the user prefers end-to-end type-safe routes.
- **Next.js** → the framework's App Router (file-system routing under `app/`);
  do not add a separate router.

## State: client vs server

Separate the two kinds of state — conflating them is a common source of bugs:

- **Server state** (data fetched from an API) → **TanStack Query**. It owns
  caching, refetching, loading/error states, and invalidation. Do not copy
  server data into a global store.
- **Client/UI state** (modals, selected tab, theme, ephemeral form-adjacent UI)
  → **Zustand**, or plain React state when it's local to a component. Keep stores
  small and scoped.

## Data fetching with TanStack Query

- Wrap the app in a `QueryClientProvider`.
- Encapsulate fetches in `useQuery` / `useMutation` hooks per feature; key
  queries consistently so invalidation is predictable.
- After mutations, invalidate the affected query keys rather than manually
  patching cache unless you have a reason to.
- Surface loading and error states in the UI using shadcn primitives
  (`Skeleton`, `Alert`, toasts via `sonner`).

## Next.js: RSC vs client components

Only relevant when the project is Next.js App Router. Files under `app/` are
**React Server Components by default**:

- Server components can fetch data directly and render on the server; they
  **cannot** use hooks, state, effects, browser APIs, or event handlers.
- A component becomes a **client component** by adding `"use client"` at the top
  of the file. Anything interactive — most shadcn components that use Radix
  state, plus your forms, toggles, and stores — must be in a client component.
- Push the `"use client"` boundary **down** the tree: keep pages as server
  components that fetch data, and isolate interactivity into small client
  components, rather than marking the whole page client.
- shadcn's `rsc: true` makes generated primitives include `"use client"` where
  needed; your composed interactive components must add it themselves.
- Mismatched boundaries cause "you're importing a component that needs
  useState … but it's a Server Component" errors — fix by adding `"use client"`
  to the offending file, not by removing the hook.

## Respect existing conventions

Before introducing any of the above, check what the repo already does — its
router, state library, data layer, and folder shape. Match it. Only apply these
defaults for greenfield work or where the project leaves the choice open.
Introducing a second router or a second data-fetching library is almost always
the wrong move.
