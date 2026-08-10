# Data Model

Tables, field by field, with the reasoning. Runnable reference DDL is in `assets/templates/schema.sql`; this file explains the choices behind it so you can adapt rather than copy.

Column types are written generically (`id`, `string`, `int`, `bool`, `timestamp`). Map them to the project's database and naming conventions — snake_case tables, an ORM's conventions, whatever is already there. Consistency with the existing codebase beats consistency with this document.

## Contents

- [Minimum viable set](#minimum-viable-set)
- [Core tables](#core-tables)
- [Organization tables](#organization-tables)
- [Data permission tables](#data-permission-tables)
- [SaaS tables](#saas-tables)
- [Audit](#audit)
- [Indexes and hot queries](#indexes-and-hot-queries)
- [Seeds and migrations](#seeds-and-migrations)
- [What to leave out](#what-to-leave-out)

## Minimum Viable Set

Five tables cover RBAC0 and are enough for a great many systems:

```
user, role, permission, user_role, role_permission
```

Add the rest only when the matrix demands it. Each additional table is another grant path or another filter, and both cost explainability.

## Core Tables

### `permission`

The single most important table. It is simultaneously the permission registry **and** the menu tree — one table with a `type` column, not two tables that drift apart.

| Field | Type | Notes |
|---|---|---|
| `id` | id | |
| `parent_id` | id, nullable | Tree structure. `NULL` = top level. |
| `code` | string, **unique** | The contract: `system:user:create`. Never renamed after release. |
| `name` | string | Display label. Renaming this is free — that is the point of separating it from `code`. |
| `type` | enum | `dir` \| `menu` \| `button` |
| `sort` | int | Display order among siblings |
| `icon` | string, nullable | `dir` / `menu` only |
| `route_path` | string, nullable | Browser route. `menu` requires it; `button` must not have one. |
| `component` | string, nullable | Frontend component path for the router to resolve |
| `is_external` | bool | If true, `route_path` must start with `http://` or `https://` |
| `visible` | bool | Hidden from the menu but still route-accessible (detail pages, tabs) |
| `status` | enum | `enabled` \| `disabled` — a disabled node denies access for everyone, including holders |
| `cacheable` | bool, nullable | Frontend keep-alive hint. Pure UI metadata; harmless to include. |
| `created_at` / `updated_at` | timestamp | |

The three types, and why the distinction matters:

- **`dir` (目录)** — a grouping node with no page of its own. Renders as an expandable menu group. May be an external link.
- **`menu` (菜单)** — an actual page with a route and a component. Granting it is what makes the page reachable.
- **`button` (按钮)** — an operation inside a page. No route, no component; only a `code`. This is what the server checks on write endpoints.

Keeping menu and permission in one table means the menu tree the frontend renders and the permission set the server checks are provably the same data. Two tables joined by a nullable `permission_code` column is the setup where a button exists in the menu with no matching permission, and the check silently passes.

**Why `code` and not `id` in grants:** codes are readable in logs, portable across environments, greppable in the codebase, and stable across a database rebuild. Store `permission_id` in join tables for referential integrity if you like, but make `code` what the application checks.

### `role`

| Field | Type | Notes |
|---|---|---|
| `id` | id | |
| `code` | string, unique per tenant | `admin`, `dept_head` — checked by nothing in business logic, used for seeds and mutex rules |
| `name` | string | Display name |
| `is_builtin` | bool | Built-in roles are seed-owned and not editable by tenants |
| `is_hidden` | bool | Never appears in the tenant's role list (super admin, support) |
| `data_scope` | enum | `ALL` \| `CUSTOM` \| `DEPT_AND_BELOW` \| `DEPT` \| `SELF` — see `data-permissions.md` |
| `status` | enum | `enabled` \| `disabled` |
| `sort`, `remark` | int, string | |
| `tenant_id` | id, nullable | `NULL` for system-wide built-ins |
| `parent_id` | id, nullable | **Only if you adopted RBAC1.** Omit otherwise. |

`data_scope` lives on the role, not on the permission. A role is "what job this person does", and the reach of a job is a property of the job. Per-permission scopes are occasionally needed (see `data-permissions.md`) but should not be the default shape.

### `user_role`, `role_permission`

Plain join tables: `(user_id, role_id)` and `(role_id, permission_id)`, each with a unique composite index and a `created_at`. Add `granted_by` if grants need auditing at the row level, which regulated environments usually want.

## Organization Tables

Add these only if the matrix uses them.

### `dept`

| Field | Type | Notes |
|---|---|---|
| `id`, `parent_id`, `name`, `sort`, `status` | | Standard tree |
| `ancestors` | string | **Materialized path**: `/1/4/9/`. |
| `leader_user_id` | id, nullable | |
| `tenant_id` | id | |

**Materialize the path.** Row-level scope resolution needs "this department and all descendants" on nearly every request. With `ancestors` it is `WHERE ancestors LIKE '/1/4/%' OR id = 4` — one index-assisted scan. Without it, it is a recursive CTE or an application-side tree walk per request, which is how permission checks end up on the slow-query log.

Maintenance cost: moving a subtree rewrites `ancestors` for its descendants. Departments move rarely; requests happen constantly. Take the trade. Rebuild the paths inside the same transaction as the move, and keep a repair script for drift.

### `position`

| Field | Type | Notes |
|---|---|---|
| `id`, `name`, `code`, `sort`, `status` | | |
| `level` | int | Lower = more senior, or the reverse; **write down which** |

Positions have two possible jobs, and you must pick:

1. **An employee attribute only** — job title on the profile, no permission effect. The common and safe case.
2. **A grant path** (`position_role`) and/or the basis for same-department seniority in data scope. Powerful, and a second place permissions come from.

If positions grant, the `level` semantics must be documented next to the column. "Higher level number means more senior" being wrong by one is a silent privilege inversion.

### `user_dept`, `dept_role`, `position_role`

- `user.dept_id` (single department) is enough for most systems. A `user_dept` join table is for genuine matrix organizations — do not add it speculatively.
- `dept_role` and `position_role` are the grant paths. **Each one you add is a place permissions come from.** If you add them, the resolution rule is a pure union (`role grants ∪ dept-role grants ∪ position-role grants`) with no deny, so the answer to "why does this user have this" stays a single readable list.

Child-department behavior when departments grant needs an explicit decision — pick one and document it:

- *Identical to parent* — simplest, least flexible.
- *Inherit and extend* — child starts from the parent's set and may add; cannot remove.
- *Fully independent* — most flexible, most configuration work.

## Data Permission Tables

### `role_dept` — the custom department set

`(role_id, dept_id)`. Only meaningful when `role.data_scope = CUSTOM`. This is how cross-department reach is expressed: a role whose scope is a hand-picked list of departments.

### `role_field` — column whitelist

| Field | Type | Notes |
|---|---|---|
| `role_id` | id | |
| `resource` | string | Which resource the rule applies to: `system:user`, `order:order` |
| `field` | string | Field name as the API exposes it |
| `access` | enum | `read` \| `write` \| `none` (or two booleans) |

Whitelist, not blacklist. A blacklist means every new field added to a model is exposed to every role by default, and that default fails silently. With a whitelist, a forgotten new field is invisible until someone grants it — a visible bug rather than a leak.

Only store rows for resources that actually have field restrictions. Resources with no rows mean "no field restriction", which keeps the table small.

### Per-object sharing (optional)

For "share this document with that person or role", roles are the wrong tool — that is genuinely ACL-shaped:

```
resource_grant(resource_type, resource_id, grantee_type, grantee_id, access, granted_by, expires_at)
```

`grantee_type` covers user / role / department. Keep this mechanism strictly separate from `role_permission`; blending object sharing into role grants is how role tables reach millions of rows.

## SaaS Tables

Only for multi-tenant products. Details in `saas-and-versioning.md`.

- `tenant(id, name, status, plan_code, ...)`
- `plan(code, name, sort)` and `plan_permission(plan_code, permission_code)` — the **ceiling**
- `tenant_entitlement(tenant_id, permission_code, allowed)` — per-customer overrides on top of the plan
- `tenant_quota(tenant_id, quota_key, limit_value, used_value, period_start)` — usage caps

`tenant_id` belongs on every business table and is enforced below the permission layer. It is not a permission and must not be expressible as one.

## Audit

Two logs, different purposes, both worth having:

- **`operation_log`** — who called what, when, from where, with what result. Answers "who deleted this".
- **`permission_change_log`** — every grant, revoke, role edit, and scope change, with before/after. Answers "when did this user get this permission and who gave it to them", which is the question that actually gets asked during an incident, and the one an ordinary operation log cannot answer.

Log every super-admin action unconditionally. A bypass without a trail is indistinguishable from a compromise.

## Indexes And Hot Queries

The three queries on the request path:

```sql
-- 1. user's roles
SELECT role_id FROM user_role WHERE user_id = ?;                    -- idx(user_id)

-- 2. permission codes for those roles
SELECT DISTINCT p.code FROM role_permission rp
  JOIN permission p ON p.id = rp.permission_id
 WHERE rp.role_id IN (?) AND p.status = 'enabled';                  -- idx(role_id), unique(code)

-- 3. department subtree for the data scope
SELECT id FROM dept WHERE id = ? OR ancestors LIKE CONCAT('/', ?, '/%');  -- idx(ancestors)
```

All three should be cached per user rather than run per request; see `runtime-and-hardening.md`. Even cached, index them — cold starts and cache stampedes happen when they are least convenient.

Composite unique indexes on every join table (`user_role(user_id, role_id)`, `role_permission(role_id, permission_id)`, `role_dept(role_id, dept_id)`) prevent duplicate grants, which otherwise show up as duplicated rows in the admin UI.

## Seeds And Migrations

**Permissions and built-in roles belong in migrations or seed files, not in the admin UI.** Creating them by hand means dev, staging, and production disagree, and the disagreement surfaces as "works on my machine" permission bugs. The seed file is also the reviewable record of what shipped.

Rules that avoid pain later:

- Adding a permission code is additive and safe. Existing roles simply do not have it — which is the correct default (deny), not a regression.
- **Renaming a code is a migration**: update `permission`, update every `role_permission` reference by code, update the source, and ship them together. Prefer adding the new code, dual-checking both for a release, then removing the old one.
- Deleting a permission means deleting its grants. Do it in one transaction, and log what was removed.
- **When adding a permission to an existing module, decide explicitly whether built-in roles get it.** Silence means built-in "admin" does not have the new button, and someone will report it as a bug on release day.
- Never let a migration hand permissions to *custom* roles. Those belong to the customer; a migration that edits them is you editing their configuration.

## What To Leave Out

Do not add these without a concrete requirement in the matrix:

- `role.parent_id` unless RBAC1 was chosen deliberately
- `user_dept` unless the organization is genuinely a matrix
- `user_permission` (direct user grants) — it reintroduces ACL and defeats the role layer. If one user needs one extra thing, that is a role with one holder, or object-level sharing.
- Deny rules — see the algebra note in SKILL.md
- A separate `menu` table alongside `permission`
- Time-bounded grants, unless someone asked. `expires_at` on a grant needs a sweeper, or it does not expire.
