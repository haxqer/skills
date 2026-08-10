# Runtime And Hardening

The per-request pipeline, caching, invalidation, audit, and the failure modes that reach production.

## Contents

- [The request pipeline](#the-request-pipeline)
- [Caching the permission set](#caching-the-permission-set)
- [Invalidation](#invalidation)
- [Audit logging](#audit-logging)
- [Failure modes](#failure-modes)
- [Performance notes](#performance-notes)
- [Rollout](#rollout)

## The Request Pipeline

Fixed order. Each stage assumes the previous one held.

```
1. authenticate        →  user identity (not this skill's concern, but must be trustworthy)
2. tenant boundary     →  bind tenant_id from the session; ignore any client-supplied value
3. load permission set →  from cache, or resolve and cache
4. function check      →  does the set contain the endpoint's required code?      → 403
5. resolve data scope  →  { all, dept_ids, self_only } for this resource
6. execute             →  data layer injects the row predicate automatically
7. row-level write     →  for writes, verify the target row is inside the write scope → 403
8. field projection    →  strip/mask unreadable fields; drop unwritable ones from input
9. audit               →  log the action, the subject, the target, the outcome
```

Stage 2 before stage 3 is deliberate: the tenant boundary must hold even if the permission layer is misconfigured. A bug in role resolution should leak within a tenant at worst, never across tenants.

Stage 7 is separate from stage 4 on purpose. Holding `order:edit` says the user may edit orders in general; it says nothing about *this* order.

### Failing closed

- An unknown permission code → deny. Never treat "code not found in the registry" as permissive.
- A cache miss → resolve from the database. Never treat a miss as "no restrictions".
- An error resolving the scope → deny, log, alert. Do not fall back to an unfiltered query.
- An endpoint with no permission marker → deny, unless explicitly marked public. See `function-permissions.md`.

Every one of these is the same principle: the absence of information is not permission.

## Caching The Permission Set

Resolving roles → permissions → department subtree on every request is three or more queries per call. Cache it.

**What to cache, per user:**

```
{
  permissions: Set<string>,        # after plan-ceiling intersection
  data_scope:  { all, dept_ids, self_only },
  field_rules: { resource -> {read: Set, write: Set} },
  is_super:    bool,
  version:     int
}
```

**Where:** a distributed cache (Redis or equivalent) keyed `perm:{tenant}:{user}`, with a short in-process cache in front of it if request volume warrants. A purely in-process cache in a multi-instance deployment is a correctness problem, not just an efficiency one — a revocation invalidates one instance and the other instances keep serving.

**TTL:** 5–30 minutes as a backstop, with explicit invalidation as the primary mechanism. TTL alone means a revocation takes up to the TTL to apply, which is usually unacceptable for a permission revocation and always unacceptable for a termination.

**Never put the permission set in the JWT.** It is tempting — zero lookups — but a token cannot be un-issued. Revoking a role would require either a very short token lifetime or a revocation list, at which point you have rebuilt the cache with worse properties. Keep the token to identity; keep permissions server-side. (Short-lived tokens plus a version claim, described below, is the acceptable middle ground.)

## Invalidation

The hard part, because permission changes are transitive.

**Direct — invalidate the affected users:**

| Change | Invalidate |
|---|---|
| Assign/remove a user's role | that user |
| Enable/disable a user | that user |
| Change a user's department or position | that user |

**Transitive — invalidate everyone downstream:**

| Change | Invalidate |
|---|---|
| Edit a role's permissions | every holder of that role |
| Change a role's data scope or `role_dept` | every holder |
| Disable or delete a role | every holder |
| Edit a permission node (disable, delete) | everyone holding it — in practice, everyone |
| Move a department in the tree | every user in the subtree, plus holders of roles scoped to it |
| Change a tenant's plan | every user in the tenant |
| Change field rules | every holder of the role |

The transitive cases are where bespoke per-key invalidation breaks down. **Use a version counter instead:**

- Keep a `perm_version` integer per tenant (and optionally per user).
- Any permission-affecting change increments it, inside the same transaction as the change.
- Cache entries store the version they were built at; a request whose cached version is stale rebuilds.

One counter turns "figure out every affected user" into "increment and move on", and it cannot miss a case. The cost is that a role edit invalidates the whole tenant — which for a back-office system is a few hundred cheap rebuilds, and is the right trade.

If tokens carry a version claim, bump it on user-level changes so an in-flight token is forced to re-resolve. That gives near-immediate revocation without giving up stateless tokens entirely.

**Test the invalidation path explicitly.** "Revoke a role, then immediately call the endpoint with the same token" belongs in the automated suite, not in someone's manual checklist. Cache-without-invalidation is one of the most common production permission bugs, and it is silent — nothing errors, the user just keeps working.

## Audit Logging

Two logs, different questions:

**`operation_log`** — who did what: user, tenant, action, permission code checked, target type and id, timestamp, IP, user agent, result (allowed/denied), and for denials the code that was missing.

Log denials too. A burst of 403s from one account is the clearest available signal of either an enumeration attempt or a broken role assignment, and you cannot distinguish them after the fact without the records.

**`permission_change_log`** — every grant, revoke, role edit, scope change, and field-rule change, with before/after and the actor. This answers "when did this user get this permission and who gave it to them", which is the question asked during an actual incident. An operation log cannot answer it, because the grant looks like an ordinary admin action.

Non-negotiable entries: every super-admin bypass, every impersonation session (start and end), every export of restricted fields, every cross-tenant operation by a platform operator.

Retention follows whatever compliance regime applies; where none does, a year of permission-change history is cheap and repeatedly useful.

## Failure Modes

Roughly ordered by how often they reach production:

1. **Frontend-only enforcement.** The menu hides the button; the endpoint serves anyone who knows the URL. Every endpoint checks independently.
2. **The unfiltered detail endpoint.** Lists are filtered, get-by-id is not. Filter in the data layer, not per query.
3. **Role-name checks in business logic.** `if role == "admin"` makes the permission screens cosmetic and every new role a code change.
4. **Cache without invalidation.** Revocation takes effect at next login, which may be never. Version counter.
5. **Read scope reused for writes.** Visible ≠ writable.
6. **Field permission on read only.** Mass assignment writes it; the export dumps it.
7. **Codes renamed in a refactor.** Customer role configs silently lose permissions. Codes are a contract.
8. **A new endpoint with no marker.** Default deny plus a route-coverage test.
9. **Plans modeled as grants instead of a ceiling.** Downgrade destroys configuration; upgrade does not restore it.
10. **Empty department set treated as "no filter".** An empty scope must return zero rows.
11. **Tenant id taken from the request.** Bind it from the session, always.
12. **Batch endpoints validating only the first ID.** Validate every element.
13. **Permissions so granular nobody configures them right.** A mis-configured 300-checkbox screen is less secure than a well-chosen 30.

## Performance Notes

- Cache the resolved set (above). This is the whole game; everything else is minor.
- Materialize `dept.ancestors` so subtree resolution is one indexed scan, never a recursive walk per request.
- If RBAC1 inheritance is in play, precompute the closure into an effective-grants table and rebuild it on role change. Walking the hierarchy per request is a needless join chain.
- Row predicates must land on indexed columns: `(tenant_id, dept_id)` and `(tenant_id, owner_id)` composites on hot business tables. A correct filter on an unindexed column turns every list query into a scan.
- Watch for the cache stampede when a version bump invalidates a whole tenant at peak. Jitter the TTL and single-flight the rebuild.

## Rollout

Adding a permission system to a system that had none:

1. **Ship in observe mode first.** Evaluate every check and log what *would* have been denied, without denying. Run it for a release cycle against real traffic.
2. **Read the denial log.** It will be full of legitimate access nobody documented — the matrix is always incomplete on the first pass. Fix the matrix, not the code, and re-run.
3. **Enforce per module,** starting with the least critical, so the blast radius of a wrong rule is small.
4. **Keep a kill switch** — a config flag that returns to observe mode without a deploy. Use it, then fix forward.
5. **Migrate existing users to roles deliberately.** Never default everyone to admin "temporarily"; temporary defaults become permanent, and now the audit shows every user as an administrator.
