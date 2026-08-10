# Function Permissions

Can this user perform this operation at all. Covers the permission-code contract, the menu tree, where checks go on the server, how the frontend consumes them, and enforcing role constraints.

## Contents

- [The permission code contract](#the-permission-code-contract)
- [The menu tree](#the-menu-tree)
- [Server-side enforcement](#server-side-enforcement)
- [Frontend consumption](#frontend-consumption)
- [Permission groups](#permission-groups)
- [Super admin and built-in roles](#super-admin-and-built-in-roles)
- [Enforcing role constraints](#enforcing-role-constraints)
- [Multiple grant paths](#multiple-grant-paths)

## The Permission Code Contract

The code is the single string that ties the matrix, the database, the server check, the menu tree, and the frontend guard together. Everything else in the system is renameable; this is not.

**Format: `module:resource:action`**

```
system:user:list        system:user:create      system:user:reset-password
order:order:list        order:order:refund      order:order:export
report:sales:view
```

Rules:

- Lowercase, `:`-separated, `[a-z0-9-]` within a segment. Consistency matters more than the specific choice, but pick this one unless the codebase already has another.
- **Three segments** for buttons/operations. Two for the menu page itself (`system:user`), one for the directory (`system`). This makes the code a prefix path through the tree, so `system:user:*` naturally means "everything in user management".
- **A child's code must start with its parent's code plus `:`.** Enforced by the validator script. Break it and the tree and the codes describe different structures.
- **Actions come from a fixed vocabulary.** Pick one and hold to it, e.g. `list, view, create, edit, delete, export, import, audit, assign`. Systems where one module says `add` and another says `create` produce checks against codes that do not exist — a check against a nonexistent code fails closed, so it looks like a permission bug rather than a typo.
- **Never rename after release.** Codes live in seed data, customer role configs, integration scripts, logs, and source. See the migration path in `data-model.md`.

**Wildcards on the grant side only.** `system:*` as a stored grant is fine and useful for built-in admin roles. `can("system:*")` as a *check* is meaningless — a check names one specific operation. Also note that a wildcard grant silently absorbs every future permission under that prefix: correct for built-in admins, risky for customer-created roles, which is why the validator warns about it.

## The Menu Tree

The API returns the current user's tree — the intersection of the full `permission` tree with their granted codes, with the ancestors of any granted node kept so the tree stays connected.

```
GET /api/menus/mine
→ [ { code, name, type, icon, path, component, sort, external, visible, children: [...] } ]
```

Two rules that matter:

- **Prune, do not flag.** Return only what the user has, rather than the full tree with `hasPermission: false`. The flagged version leaks the product surface — an ordinary user can enumerate every admin feature by reading one JSON response.
- **This response is UX, not security.** It decides what renders. It decides nothing about what the server will accept. Every endpoint behind those menus checks independently.

Whether to include buttons in the tree or ship a flat `permissions: ["order:order:refund", ...]` array alongside it is a judgment call. The flat array is simpler for the frontend to check against and is the more common choice; nesting buttons under menus is better when the UI is generated from the tree.

### Field notes by type

| Type | route_path | component | code | Notes |
|---|---|---|---|---|
| `dir` | only if external | — | required | External links must start with `http://` or `https://` |
| `menu` | required | required | required | The page-access permission |
| `button` | must be absent | must be absent | required | Only a code; this is what write endpoints check |

`visible = false` means "routable but not shown in the menu" — detail pages, tabs, and wizard steps. It is a display flag, not a permission: a hidden node the user does not hold is still denied.

`status = disabled` on a node denies it to *everyone*, including current holders. It is the kill switch for a feature being rolled back, and it must be honored in the server check, not only in menu assembly.

## Server-Side Enforcement

### Where the check goes

One layer, consistently. Two common placements, both fine:

- **At the route/handler boundary** — a declarative marker per endpoint (annotation, decorator, middleware config, route metadata). Easy to audit: you can list every endpoint and its required code with a grep or reflection pass.
- **At the service-method boundary** — better when the same operation is reachable from HTTP, a job, and a message consumer, since all three paths get the check.

What matters more than the choice: **it must be impossible to add an endpoint without deciding.** Make the framework's default deny — an unmarked route is rejected — and add an explicit `@public` / `@no-auth` marker for the handful of genuinely open endpoints. A default of "unmarked means open" produces one unprotected endpoint per release, forever.

```
# declarative
@requires("order:order:refund")
POST /api/orders/{id}/refund

# imperative, where the required code depends on runtime state
if (!ctx.can("order:order:refund")) deny()
```

### Auditing coverage

Write a test that enumerates every registered route and asserts each one is either marked with a permission code or explicitly marked public. This single test catches the most common real-world hole and costs an afternoon.

Cross-check the codes referenced in source against the codes in the seed data, in both directions: a check against a nonexistent code fails closed forever (nobody can use the feature), and a seeded code nobody checks is a checkbox that does nothing.

### The gateway trap

Checking permissions only at an API gateway breaks the moment a service is reachable another way — internal RPC, a scheduled job, an event consumer, a second gateway, someone's debug port. Gateway checks are a good fast-fail layer; they are not the enforcement point. The service that owns the data enforces.

## Frontend Consumption

Three consumers of the same permission set, all of them UX:

1. **Dynamic routes** — build the router from the menu tree; register only routes the user holds. Unregistered routes 404 rather than flashing a page before redirecting.
2. **Button guards** — a directive/component/hook that checks a code and removes (not disables) the element. `v-permission="'order:order:refund'"`, `<Can code="...">`, `usePermission()`. Removing beats disabling: a disabled button invites a support ticket about a feature they cannot have.
3. **Column trimming** — hide table columns and form fields the user has no field permission for. See `data-permissions.md`.

Guidance worth passing to whoever writes the frontend:

- Load the permission set once after login, cache it in the app store, and **re-fetch on 403** — a 403 usually means the server's view and the client's cached view have diverged.
- Never derive UI from role names on the client either. Same reason as the server: it hardcodes policy in the wrong layer.
- Route guards must handle the token-valid-but-permission-revoked case: the user is logged in and the route no longer exists in their tree. Redirect to a "no access" page, not to login.

## Permission Groups

Grant one thing, bind several buttons — a "view and operate" (查看与操作) permission that covers create, edit, and delete.

Two ways to model it — pick deliberately:

- **Merge at design time (preferred).** One code, `system:user:manage`, bound to all three buttons. Simple, no resolution logic, nothing to explain. The cost is that splitting later is a migration.
- **Group as a container.** Keep the three fine-grained codes and add a group node that expands to them at grant time. More flexible, but now "what does this role have" requires expansion, and the admin UI must show both levels without confusing anyone.

Default to merging. Keep the fine-grained codes only where a real role in the matrix distinguishes them. This is the concrete application of "权限越细越好 is false": mature products expose a handful of configurable permissions per module rather than one per button.

Keep the underlying `permission` table at button granularity regardless. The grouping is a layer *above* the atomic permissions, never a replacement for them — otherwise you cannot split later at all.

## Super Admin And Built-in Roles

**Super admin is a bypass, in exactly one place:**

```
function can(user, code) {
    if (user.isSuperAdmin) return true     // one line, one location
    return effectivePermissions(user).has(code)
}
```

- Determined by a stable property (a flag on the user, membership in a hidden reserved role), never by a grantable permission. If it is grantable it is revocable, and the day someone revokes it from the last holder you are editing the database by hand.
- **Never crosses the tenant boundary.** A tenant super admin is omnipotent within their tenant and invisible outside it. Platform-level operators are a separate concept with a separate audit trail.
- Log every action taken under the bypass, unconditionally.

**Built-in roles** are seeded, not editable by tenants, and get new permissions through migrations with an explicit decision each time (see `data-model.md`). Let tenants *copy* a built-in role into a custom one — it is the most common way customers get what they want without you exposing more configuration.

## Enforcing Role Constraints

If the matrix listed mutually exclusive roles (RBAC2), the constraint needs enforcing at every assignment path:

- Assigning a role to a user
- Bulk import / batch assignment  ← the path where the check is usually missing
- Assigning roles via department or position, if those grant
- **Editing a role's contents.** Adding a permission to role A can retroactively violate its exclusion with role B. Re-validate every user holding either role, and either block the edit or report the violations.

Cardinality limits ("at most two finance admins") and prerequisite roles ("regional manager requires salesperson") follow the same rule: check on assignment, re-check on role edit, and check on *removal* for prerequisites — removing the prerequisite must either cascade or be refused.

Dynamic separation of duty (activate one role per session) additionally needs session state and a role-switching UI. It is a significant UX cost; adopt it only where compliance genuinely requires it, not as a nicer-sounding version of SSD.

## Multiple Grant Paths

When departments or positions also grant roles, the effective set is a plain union:

```
roles(user) = user_role(user)
            ∪ dept_role(user.dept)            [+ ancestors, if inheritance was chosen]
            ∪ position_role(user.position)    [+ subordinate levels, if RBAC1]

permissions(user) = ⋃ role_permission(r) for r in roles(user), r.status = enabled
                  ∩ plan_ceiling(user.tenant)
```

Because it is a pure union, "why does this user have `order:order:refund`?" is answerable by listing the roles that contain it and where each role came from. **Build that as an actual feature** — an "explain permissions" view in the admin UI showing each effective code and its source path. It takes a day, and it pays for itself the first time a customer disputes an access decision. It is also the best possible test of whether the model stayed explainable: if the explain view is hard to write, the model has too many grant paths.
