# Data Permissions

Given that a user may perform an operation, which rows do they see and which columns. This is where over-privilege bugs actually happen — function permissions are easy to get right and hard to get wrong silently; data permissions are the opposite.

**Precondition:** data permission presupposes function permission. A role with a row scope but no page access sees nothing. Grant the function first, then narrow the data.

## Contents

- [Row-level: the data scope enum](#row-level-the-data-scope-enum)
- [Resolving a scope to a filter](#resolving-a-scope-to-a-filter)
- [Where the filter is applied](#where-the-filter-is-applied)
- [Read scope vs write scope](#read-scope-vs-write-scope)
- [Sharing data outward](#sharing-data-outward)
- [Column-level: field whitelists](#column-level-field-whitelists)
- [Over-privilege test checklist](#over-privilege-test-checklist)

## Row-Level: The Data Scope Enum

Attach the scope to the **role** (`role.data_scope`). A role is a job; the reach of a job is a property of the job.

| Value | Meaning | Typical holder |
|---|---|---|
| `ALL` | Every row in the tenant | Tenant admin |
| `CUSTOM` | An explicitly chosen set of departments (`role_dept`) | Cross-department roles: regional manager, auditor |
| `DEPT_AND_BELOW` | The user's own department and all descendants | Department head — 所在部门和下级部门 |
| `DEPT` | The user's own department only, no descendants | Team-level roles |
| `SELF` | Only rows the user owns | Ordinary member |

Five values cover the overwhelming majority of real requirements. Resist adding more until a matrix row genuinely cannot be expressed.

**Multiple roles: widest wins.** Union the filters, do not intersect them. A user holding both a `SELF` role and a `DEPT_AND_BELOW` role sees the whole subtree. Users hold extra roles precisely to gain reach, and intersecting produces the surprising result where adding a role *removes* access.

`ALL` short-circuits: once any role has it, stop resolving and skip the filter entirely.

### Position-based seniority within a department

A third case that appears in organizations with job levels: a team lead sees their subordinates' data but not the director's, while an assistant sees only their own. Modeled as an extra condition on top of the department scope:

```
dept_id ∈ subtree  AND  (owner.position.level >= me.position.level  OR  owner_id = me.id)
```

This requires denormalizing the owner's position level onto the business row, or accepting a join to `user` on every query. Denormalize if the table is hot, and refresh it when a user's position changes.

Adopt this only when the matrix actually calls for it. It is the point where "explain this user's data access" gets meaningfully harder, and it introduces a stale-denormalization failure mode.

### Per-permission scopes

Occasionally one role needs `DEPT_AND_BELOW` for orders and `SELF` for salary. Two clean options:

- **Split the role.** Usually correct: two jobs were being modeled as one.
- **Move the scope to `role_permission`**, i.e. a scope per (role, resource). More expressive, and now every scope question needs two lookups instead of one.

Start with role-level. Move to per-resource only when splitting roles has been tried and produces an unreasonable number of them.

## Resolving A Scope To A Filter

Resolve once per request into a small structure, then let the data layer apply it:

```
resolve_scope(user, resource) -> { all: bool, dept_ids: set, self_only: bool }

  scopes = [ r.data_scope for r in roles(user) if r grants any action on resource ]

  if ALL in scopes:              return { all: true }

  dept_ids = {}
  self_only = true
  for s in scopes:
      if s == CUSTOM:           dept_ids ∪= role_dept(r)                and self_only = false
      if s == DEPT_AND_BELOW:   dept_ids ∪= subtree(user.dept_id)       and self_only = false
      if s == DEPT:             dept_ids ∪= { user.dept_id }            and self_only = false
      if s == SELF:             (contributes only the owner clause)

  return { all: false, dept_ids, self_only }
```

Note the filter for `CUSTOM` covers the chosen departments; whether it also covers their descendants is a product decision — make it explicit, because "I picked the parent department and did not get the child" is a predictable support ticket. Including descendants is the more intuitive behavior for most users.

Applied as a predicate:

```sql
-- all: no predicate at all
-- otherwise:
AND ( t.dept_id IN (:dept_ids)  OR  t.owner_id = :user_id )
-- self_only (no departments contributed):
AND   t.owner_id = :user_id
```

The department subtree comes from the materialized `ancestors` path (`data-model.md`):

```sql
SELECT id FROM dept WHERE id = :d OR ancestors LIKE CONCAT('/', :d, '/%');
```

Two practical notes: `IN (:dept_ids)` with thousands of departments should become a join against a subtree query or a temp table; and an empty `dept_ids` with `self_only = false` must produce **no rows**, not an unconstrained query — `IN ()` behavior differs across databases and "empty means no filter" is exactly the bug class this whole document is about.

Every filterable business table therefore needs `dept_id` and `owner_id` (or `created_by`) columns. Add them up front — retrofitting an ownership column onto a table with production data is an expensive migration.

## Where The Filter Is Applied

**In the data-access layer, once.** Not in each query, not in each service method, not in each controller.

Whatever the stack offers — a query interceptor, a global scope, a repository base class, a plugin that rewrites SQL, a middleware that injects criteria — attach the predicate to every query against a scoped resource by default, and require an **explicit, greppable opt-out** for the queries that legitimately need to bypass it (statistics jobs, internal reconciliation, the admin export that is itself permission-gated).

Why this is non-negotiable: hand-written per-query filtering guarantees the forgotten path. In practice the forgotten one is almost always the detail endpoint. The list is filtered, `GET /order/{id}` fetches by primary key, and any authenticated user reads any order by incrementing an ID. That is the single most common real over-privilege bug in permission systems.

Paths that must all go through the filter:

- List and paginated queries — including the total count, or the pagination reveals hidden row counts
- **Detail / get-by-id** — the classic hole
- Aggregates: sum, count, group-by, dashboard tiles, chart endpoints
- Export and report generation
- Search, autocomplete, and typeahead — these frequently bypass the repository layer for speed
- Batch operations by ID list — validate *every* ID in the list, not just the first
- Update and delete targeting a specific row
- Nested/expanded resources: `GET /customer/{id}/orders` must filter the orders too
- Anything reachable by RPC, message consumer, or scheduled job on behalf of a user

## Read Scope vs Write Scope

Seeing is not editing. A department head who sees the entire subtree may only be allowed to edit their direct reports; a member who sees their team's orders may only edit their own.

Model it as either a second scope column (`read_scope` / `write_scope` on the role) or a rule that write operations always narrow one level (e.g. writes fall back to `SELF` unless a specific write permission says otherwise). Either works; what fails is having one scope and assuming it means both.

Enforcement for writes is a two-step check, in this order:

1. Does the user hold the function permission (`order:order:edit`)?
2. Does the target row fall inside their **write** scope?

Step 2 must run against the row as it exists in the database, not against IDs supplied in the request body. And re-check after the update if the update can move the row out of scope — a user reassigning a record to another department may be handing away their own access, which is sometimes intended and sometimes an exfiltration path.

## Sharing Data Outward

The two directions are different mechanisms, and both are legitimate:

- **Assign data to subjects** (the default above): the role's scope determines what it reaches. Configured on the role, by an admin, in bulk.
- **Assign subjects to data**: the owner of a specific record shares it with a user, role, or department — the document-sharing model. Configured per object, by the owner, ad hoc.

The second is ACL-shaped and belongs in its own table (`resource_grant` in `data-model.md`), not in `role_permission`. When both exist, the effective row set is their union, and the shared-with-me rows need their own predicate branch:

```sql
AND ( <scope predicate>  OR  EXISTS (SELECT 1 FROM resource_grant g
        WHERE g.resource_type = 'order' AND g.resource_id = t.id
          AND g.grantee_id IN (:user_and_role_and_dept_ids)
          AND (g.expires_at IS NULL OR g.expires_at > now())) )
```

If grants can expire, something must sweep them, and the check must test the expiry — an `expires_at` nobody reads is a field that lies.

## Column-Level: Field Whitelists

Which fields of a record a role may see or write. Ban the ID number for support staff; show the deal amount only to finance.

**Whitelist, never blacklist.** With a blacklist, every field added to a model is exposed to every role by default, and the failure is silent. With a whitelist, a newly added field is invisible until granted — a visible bug, not a leak.

### Apply in three places

Missing any one makes the whole feature decorative:

1. **On read (serialization).** Strip or mask before the response leaves the server. Never send the value with a "hidden" flag — the payload is in the browser's network tab.
2. **On write (deserialization).** Drop or reject unauthorized fields in the request body. Otherwise a user who cannot *see* the credit limit can still *set* it by adding it to the JSON — mass assignment, straight through the permission layer.
3. **On export, import, and API/report output.** The export endpoint that dumps the raw model is where field permissions most often leak, because it usually skips the normal serializer.

### Mask or omit

- **Omit** (field absent) is safer and simpler; the client renders nothing.
- **Mask** (`138****8000`) is friendlier when users need to know the field exists and to recognize the record.

Pick per field, not globally, and note the choice in the matrix. If masking, mask **server-side** — a full value sent with display truncation is not a permission.

### Configuration UI

The shape that works: pick a resource, list its fields, tick which are visible per role. Reachable from role creation, from a standalone role action, from a batch screen (all roles × one resource), or from the page itself. A batch matrix screen scales better once there are more than a handful of roles.

Only store rows for resources that actually have restrictions; no rows means no restriction, which keeps both the table and the resolution cheap.

## Over-Privilege Test Checklist

Generate the positive cases from the permission matrix; write these negatives by hand. A permission system with only happy-path tests is untested.

**Vertical (privilege escalation) — a lower-privileged user reaching a higher-privileged function:**

- [ ] Every admin endpoint called with an ordinary user's token → 403
- [ ] Every endpoint called with no token and with an expired token → 401
- [ ] Every registered route is either permission-marked or explicitly public (enumerate routes in a test)
- [ ] Revoking a role takes effect on the **next request**, not the next login
- [ ] Disabling a permission node denies existing holders
- [ ] A disabled user's token stops working immediately

**Horizontal (peer access) — a user reaching another user's data at the same privilege level:**

- [ ] Detail endpoint with another department's record ID → 404 or 403 (**the most common real bug**)
- [ ] Update and delete with another user's record ID → denied
- [ ] Batch endpoints with a mixed ID list (one permitted, one not) → the whole request rejected, not partially applied
- [ ] Aggregate and dashboard numbers match the filtered row set, not the global one
- [ ] Export contains exactly the rows the list shows
- [ ] Search and autocomplete respect the scope
- [ ] Nested resources (`/customer/{id}/orders`) filter the nested collection
- [ ] Total count in pagination does not reveal hidden rows

**Field level:**

- [ ] A restricted field is absent from the read response, including in exports and nested payloads
- [ ] Sending a restricted field in a write body does not change it (mass assignment)
- [ ] Masked values are masked server-side (check the raw response, not the UI)

**Tenant boundary (multi-tenant only):**

- [ ] Every cross-tenant ID → not found, for every endpoint, including detail, update, delete, and export
- [ ] A tenant super admin cannot reach another tenant by any path
- [ ] A tenant ID supplied in the request body or a header is ignored in favor of the session's

Build a reusable harness: a table of (role, endpoint, expected status) driven from the matrix CSV, plus a fixture set with two departments, a parent/child department pair, and two tenants. Once that fixture exists, each new negative case is one line.
