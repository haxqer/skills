# Components: adding, composing, forms, tables, icons

Read this when adding or customizing shadcn components, using `cn()` and `cva`,
building forms, data tables, or pulling blocks and third-party registries.

## Contents

- [Adding components](#adding-components)
- [The you-own-the-source model](#the-you-own-the-source-model)
- [Composing with cn() and cva](#composing-with-cn-and-cva)
- [Forms: react-hook-form + zod](#forms-react-hook-form--zod)
- [Data tables: TanStack Table](#data-tables-tanstack-table)
- [Icons](#icons)
- [Blocks and third-party registries](#blocks-and-third-party-registries)
- [Upgrading components](#upgrading-components)

## Adding components

Add only what the feature needs, by name:

```bash
npx shadcn@latest add button card input label dialog
```

Each command copies the component source into `components/ui/` (per the
`aliases.ui` path in `components.json`) and installs any Radix dependency it
needs. Before hand-writing any common UI primitive, check whether the registry
already has it — it almost always does. Reinventing a button or dialog instead
of adding it is wasted effort and loses the built-in accessibility.

Browse available components at https://ui.shadcn.com/docs/components.

## The you-own-the-source model

After `add`, the files are part of your codebase. This is intentional and is the
whole point of shadcn:

- **Edit them freely** to fit the design — change variants, spacing, defaults.
- **Do not** look for a config prop that the upstream library "should" expose;
  you change the source instead.
- **Do not** reinstall to "update" and expect to keep your edits — see
  [Upgrading components](#upgrading-components).
- Keep edits to the primitive minimal and reusable; put feature-specific markup
  in your own composed components that *use* the primitive.

## Composing with cn() and cva

The generated `cn()` helper (`lib/utils.ts`) merges class names with `clsx` and
resolves Tailwind conflicts with `tailwind-merge`. Always merge through it so a
caller's overriding class wins:

```tsx
import { cn } from "@/lib/utils";

function Panel({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("rounded-lg border bg-card p-4", className)} {...props} />;
}
```

For multi-variant components, define variants with `class-variance-authority`
(`cva`) the way shadcn primitives do, rather than chaining ternaries. This keeps
variant logic declarative and type-safe.

## Forms: react-hook-form + zod

shadcn's `Form` is a thin, accessible wrapper over react-hook-form. Standard
pattern:

1. `npx shadcn@latest add form input button` (form pulls in label/etc).
2. Define a zod schema; infer the type.
3. `useForm({ resolver: zodResolver(schema) })`.
4. Build the UI with `Form`, `FormField`, `FormItem`, `FormLabel`,
   `FormControl`, `FormMessage`.

```tsx
const schema = z.object({ email: z.string().email() });
type Values = z.infer<typeof schema>;

const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { email: "" } });

<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField control={form.control} name="email" render={({ field }) => (
      <FormItem>
        <FormLabel>Email</FormLabel>
        <FormControl><Input {...field} /></FormControl>
        <FormMessage />
      </FormItem>
    )} />
  </form>
</Form>
```

`FormMessage` surfaces validation errors and is wired to the field's `aria-*`
automatically — keep it in the tree for accessibility.

## Data tables: TanStack Table

shadcn ships a `table` primitive plus a documented data-table pattern built on
**@tanstack/react-table**. There is no single magic component — you compose:

1. `npx shadcn@latest add table` and install `@tanstack/react-table`.
2. Define `columns` as `ColumnDef[]` (including a header, accessor, and optional
   cell renderer; use shadcn `Button`/`Checkbox`/`DropdownMenu` inside cells for
   sorting, selection, and row actions).
3. Build a reusable `DataTable` component that wires `useReactTable` with the
   row model(s) you need (core, sorting, filtering, pagination) and renders the
   shadcn `Table` primitives.

For server-driven data, fetch with TanStack Query (see
[architecture.md](architecture.md)) and feed the result into the table; use
manual pagination/sorting when the server owns those.

## Icons

`lucide-react` is the default icon set. Import named icons and size them with
Tailwind classes:

```tsx
import { Check, ChevronRight } from "lucide-react";
<Check className="size-4" />;
```

If the project's `components.json` sets a different `iconLibrary` (e.g. Radix
Icons), follow that instead so generated components match.

## Blocks and third-party registries

- **Blocks** are larger prebuilt sections (auth screens, dashboards, sidebars).
  Add them like components: `npx shadcn@latest add sidebar-01` or via URL.
- **Third-party / custom registries** are supported by passing a URL to `add`:
  ```bash
  npx shadcn@latest add https://example.com/r/some-component.json
  ```
  Registries can be configured in `components.json` under `registries`. Only pull
  from registries the user trusts — added code runs in their app.

## Upgrading components

Because you own the source, there is no blanket "upgrade" command that preserves
your edits. To pick up upstream improvements: re-run `add` for the specific
component into a clean location (or a diff tool), compare against your edited
version, and merge intentional changes by hand. Never blindly overwrite edited
primitives.
