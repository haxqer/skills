# SaaS Plans, Versions, And Quotas

For multi-tenant products where different customers bought different things. Skip this file for single-tenant internal systems.

## Contents

- [The ceiling rule](#the-ceiling-rule)
- [Modeling plans](#modeling-plans)
- [Per-customer entitlements](#per-customer-entitlements)
- [Usage quotas](#usage-quotas)
- [Upgrade and downgrade](#upgrade-and-downgrade)
- [Presenting the ceiling in the UI](#presenting-the-ceiling-in-the-ui)
- [Tenant isolation](#tenant-isolation)

## The Ceiling Rule

**A plan is an upper bound, not a grant.**

```
effective(user) = ( ⋃ role grants )  ∩  plan_ceiling(tenant)  ∩  entitlement_overrides(tenant)
```

A tenant admin on the Basic plan holding a role with `report:*` still cannot open the advanced report, because the plan does not include it. The role grant is real and stored; it is simply capped at evaluation time.

Modeling plans as grants instead is the most common SaaS permission bug, and it is destructive rather than merely wrong:

- *As a grant:* a downgrade must strip permissions from roles, which destroys customer configuration. The subsequent upgrade cannot restore it — the information is gone. Support then rebuilds it by hand from a screenshot.
- *As a ceiling:* a downgrade changes one field on the tenant. Roles keep their grants, capped and inert. The upgrade restores everything instantly, because nothing was ever deleted.

The same reasoning applies to trials, add-on modules, feature flags sold as SKUs, and region-restricted features. All of them are ceilings.

## Modeling Plans

```
plan(code, name, sort)                      basic | pro | enterprise
plan_permission(plan_code, permission_code) which codes each plan includes
tenant(id, ..., plan_code, plan_expires_at)
```

- Wildcards work well here: `enterprise` holds `**`, `pro` holds `report:*`, and so on. Keep it readable.
- Store the ceiling by **code**, not id, for the same reasons grants use codes.
- Cache the resolved ceiling per tenant, not per user — it changes rarely and is shared by everyone in the tenant.
- Every permission should belong to the lowest plan that includes it, and the matrix handoff checklist asks for exactly that mapping. Codes in no plan are unreachable by every tenant; the validator flags them.

**Expiry is part of the ceiling.** A lapsed `plan_expires_at` should degrade to a defined state — read-only, or a free tier — not to "whatever the roles say". Decide which, and make it explicit in the resolver rather than implicit in a cron job that may not have run.

## Per-Customer Entitlements

Sales will promise one customer one extra feature. Plan for it rather than being surprised:

```
tenant_entitlement(tenant_id, permission_code, allowed, reason, expires_at, granted_by)
```

Applied after the plan ceiling: `allowed = true` adds to the ceiling, `allowed = false` removes from it. Keep the table small and require `reason` and `granted_by` — an entitlement table nobody can explain becomes untouchable, and then every plan change needs manual review.

Two rules worth holding:

- **Entitlements adjust the ceiling, never the grants.** The tenant's roles stay the tenant's business.
- **Give them an expiry when they came from a negotiation.** A permanent exception granted during a sales cycle outlives the deal, the account manager, and the pricing model.

## Usage Quotas

Some limits are not boolean but numeric: 3 admin seats, 100 exports per month, 10 custom roles, 50k API calls per day.

```
tenant_quota(tenant_id, quota_key, limit_value, used_value, period, period_start)
```

Distinct from permissions and handled separately:

- **Permission answers "may you at all"; quota answers "how many more".** Check the permission first, then the quota, and return different errors — 403 for the former, 429 or a domain-specific error for the latter. A user who has hit an export quota should be told exactly that, not "access denied".
- **Counters need atomic increments** (a conditional update or an atomic counter). Read-then-write under concurrency lets a tenant exceed the limit, and someone will notice.
- **Resource-count quotas are better computed than counted.** For "at most 3 admins", count the rows at assignment time rather than maintaining a counter that can drift. Reserve stored counters for event-style quotas (exports performed, API calls made) where counting the history is expensive.
- **Period rollover** needs a defined boundary — calendar month, billing anniversary, rolling 30 days — and a rollover that is idempotent, since it will run twice at least once.

## Upgrade And Downgrade

**Upgrade** is trivial by construction: change `plan_code`, bump the tenant's `perm_version`, done. Previously capped grants come back to life immediately, which is the behavior customers expect after paying.

**Downgrade** needs product decisions, not code decisions. Get answers before implementing:

- Roles holding now-capped permissions: **keep them stored and inert.** Never strip. This is the whole point of the ceiling model.
- Data created under the higher plan (extra custom roles, advanced reports, records beyond a row limit): read-only, hidden, or deleted after a grace period? Deleting customer data on downgrade needs explicit product sign-off and a warning before the change, not after.
- Over-limit resources (5 admins on a plan allowing 3): who gets demoted, and who chooses? Blocking the downgrade until the customer resolves it is usually kinder than picking for them.
- Users currently signed in: bump `perm_version` so the new ceiling applies on the next request, not the next login.

Write these down in the matrix alongside the plan mapping. They are product rules, and discovering them during implementation means guessing.

## Presenting The Ceiling In The UI

A permission the tenant *could* grant but their plan caps should not simply vanish. Three options, in descending preference:

1. **Show it, disabled, with an upgrade prompt.** Honest, and it converts.
2. **Hide it entirely.** Cleaner, and correct for features the customer segment should not know about.
3. Show it enabled and fail at runtime. Never — the admin configures a role, tells their team the feature is available, and the team hits a 403.

Whichever you choose, the API must distinguish the two denial reasons. "You lack the permission" (talk to your admin) and "your plan does not include this" (talk to sales) send the user to different places, and collapsing them into one 403 generates support tickets that bounce between teams.

## Tenant Isolation

**Not a permission.** It sits below the entire permission layer and is never bypassable:

- Bind `tenant_id` from the authenticated session. Ignore any value in the request body, query string, or headers — accepting a client-supplied tenant id is the whole vulnerability.
- Apply the tenant predicate in the data-access layer, ahead of and independent from the data-scope predicate.
- A tenant super admin is omnipotent **within** their tenant and invisible outside it.
- Platform-level operators who genuinely need cross-tenant access are a separate mechanism with a separate audit trail, mandatory reason capture, and ideally time-boxed sessions. Never a role inside the tenant model.
- Cross-tenant access returns *not found*, not *forbidden*. A 403 confirms the record exists.

If the product may ever need per-tenant databases or schemas, keep the tenant resolution behind one interface from day one. Retrofitting that boundary after it is assumed to be a column everywhere is a rewrite.
