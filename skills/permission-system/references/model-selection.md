# Model Selection

Pick the model that matches the actual complexity. Over-modeling burns the same budget as under-modeling and is harder to walk back, because by then customers have configured against it.

## Contents

- [What a permission actually is](#what-a-permission-actually-is)
- [The models, in order of increasing power](#the-models-in-order-of-increasing-power)
- [Decision table](#decision-table)
- [Combining models](#combining-models)
- [Design traps](#design-traps)
- [When not to build a permission system](#when-not-to-build-a-permission-system)

## What A Permission Actually Is

Two families, and conflating them is the origin of a lot of confused schemas:

**Function permission (功能权限)** — may this subject perform this operation at all?
- Page / route access
- Menu visibility
- Button / operation access (create, edit, delete, export, approve, transfer)

**Data permission (数据权限)** — given that they may perform it, over *which* data?
- Which rows (their own, their department, a chosen set of departments, everything)
- Which columns (can they see the ID number, the phone, the deal amount)
- Which objects/tables at all

A useful sanity check on a design: every function permission answers "can I click it", every data permission answers "what do I see when I do". If a proposed permission answers neither cleanly, it is probably two permissions.

## The Models, In Order Of Increasing Power

### ACL — permissions bound directly to users

Each user carries their own permission list.

- **Fits:** a handful of users, permissions that essentially never change; per-object sharing ("share this document with Alice"), which is genuinely ACL-shaped even inside an RBAC system.
- **Costs:** onboarding is a manual config session. A policy change ("nobody in support may export") is a sweep across every user, and it will be done incompletely.
- **In code:** a `user_permission` table. Fine as a *supplement* for object sharing; a dead end as the primary model.

### RBAC0 — user → role → permission

Insert the role. Users get roles; roles carry permissions. This is the baseline and it is the right answer for the large majority of admin systems.

- **Fits:** basically every back-office system with recognizable job functions.
- **Costs:** almost none. Start here unless you have a specific reason not to.
- **In code:** `user_role` + `role_permission` join tables. Effective permission = union over the user's roles.

### RBAC1 — role inheritance

Roles form a hierarchy; a senior role inherits everything its junior roles have and adds specifics. *General inheritance* allows multiple parents (a DAG); *limited inheritance* restricts to a tree, which is much easier to reason about and to render in a UI.

- **Fits:** organizations with real job levels where "director = manager + these extras" is literally true.
- **Costs:** you must prevent cycles, decide how deep resolution goes, and accept that reading a role's permission list now requires walking ancestors. Deleting a mid-level role becomes a question, not an operation.
- **In code:** `role.parent_id` plus a resolver that unions up the chain — or precompute the closure into `role_permission_effective` and rebuild on change. Precomputing is usually worth it.
- **Cheaper alternative:** flat roles, and let users hold several. Two roles instead of an inheritance edge is often the better trade. Reach for RBAC1 only when the hierarchy is stable and deep enough that flat duplication is genuinely painful.

### RBAC2 — constraints

Rules about which roles may be held together or activated:

- **Static separation of duty (SSD):** mutually exclusive roles (a payment *maker* may not also be a *checker*), cardinality limits (at most two people hold "finance admin"), prerequisite roles (you cannot be "regional manager" without being "salesperson").
- **Dynamic separation of duty (DSD):** the user holds both roles but may only *activate* one per session or per transaction.

- **Fits:** finance, approval chains, audited and regulated processes — anywhere separation of duty is an actual compliance requirement.
- **Costs:** the constraints must be checked at *assignment* time, and re-checked when a role's contents change (adding a permission to role A can retroactively violate an exclusion with role B). DSD additionally requires session state and a role-switching UI, which is a real UX cost — do not adopt it casually.
- **In code:** a `role_mutex` table plus a validator on every assignment path (including bulk import, which is where the check gets skipped).

### RBAC3 — RBAC1 + RBAC2

Both hierarchy and constraints. Powerful, and correspondingly hard to explain to the people who will operate it. Adopt deliberately, not by drift.

### Groups — user groups and permission groups

Not a separate model so much as two more intermediaries you can insert into RBAC:

- **User group (用户组):** bundle users who share an attribute — most often the department — and assign roles to the group. Prevents the "assign this role to 400 people one at a time" problem. In most systems the department tree already *is* the user group; do not build a parallel grouping mechanism without a reason.
- **Permission group (权限组):** bundle related permissions so admins tick one box instead of nine. "Manage customers" granting view + create + edit + delete + export is far more usable than five checkboxes, and cuts mis-configuration.

Both exist to reduce mappings; both add a lookup hop. Permission groups are almost always worth it. User groups are worth it once user count outgrows manual assignment.

### ABAC — attribute-based

Access is computed at request time from attributes rather than looked up from grants: subject attributes (department, level, certification), resource attributes (owner, status, amount, classification), environment attributes (time, IP, device), and the action.

- **Fits:** rules that genuinely depend on runtime state — "approve only below your limit", "edit only while the record is in draft", "office IP only during business hours", "only the assigned case owner".
- **Costs:** there is no list to look at. "What can this user do?" stops being a query and becomes an evaluation over hypothetical resources, which makes support, audit, and UI (what do I even render in the menu?) all harder. Policy authoring becomes a specialist skill.
- **The right way to use it:** keep RBAC as the coarse gate and add attribute *conditions* on specific permissions. `order:approve` is granted by role; the amount limit is an attribute condition on top. Full-ABAC replacements of a working RBAC system rarely survive contact with the support team.

## Decision Table

| Situation | Model | Notes |
|---|---|---|
| < 10 users, fixed permissions, no admin UI planned | Hardcoded roles or ACL | Do not build a permission module. Revisit when it hurts. |
| Typical admin / back-office system | **RBAC0 + department as user group + permission groups** | The default answer. Covers most systems completely. |
| Above, plus users must see only their own department's data | RBAC0 + row-level data scope | The scope goes on the role, not the permission. |
| Real job levels where senior = junior + extras, deep and stable | RBAC1 | Precompute the effective grants. Consider flat multi-role first. |
| Finance, approvals, compliance, separation of duty | RBAC2 | Enforce at assignment time, and re-check when roles change. |
| Large enterprise with both | RBAC3 | Budget for the explainability work. |
| Rules depending on record state, amount, time, ownership | RBAC + ABAC conditions | Do not replace RBAC. Layer conditions on specific permissions. |
| SaaS with plans / editions / per-customer entitlements | RBAC + plan ceiling (∩) | See `saas-and-versioning.md`. Plans cap; they do not grant. |
| Users share individual objects with each other | RBAC + per-object ACL | Two mechanisms on purpose: roles for functions, ACL for shared objects. |

## Combining Models

Real systems layer these, and that is correct as long as each layer has one job:

```
tenant boundary   hard filter        never bypassable
plan / edition    ceiling  (∩)       what the customer bought
role grants       union    (∪)       what the admin assigned
attribute rules   condition          what the runtime state allows
data scope        row filter         which rows
field whitelist   projection         which columns
```

The failure mode is not layering — it is layering with overlapping jobs, e.g. plans that also grant, or departments that grant *and* filter *and* inherit. Assign each mechanism one job and the system stays explainable.

## Design Traps

**唯RBAC论 — cargo-culting RBAC.** Reaching for the full role machinery without checking whether the business has stable, recognizable roles at all. Some systems have five users and three permissions; some have permissions that are genuinely per-record. Assess complexity first, then choose.

**唯自由配置论 — configure-everything.** Exposing every knob because "the customer might want it". A screen with 300 checkboxes and no defaults produces mis-configured tenants and support tickets. Ship strong built-in roles that cover the common cases, and let custom roles handle the rest.

**权限越细越好 — finer is better.** Every permission code costs implementation, a checkbox, documentation, a test case, and a support conversation. Split a permission when two roles genuinely need different answers about it; otherwise merge. Note how mature products keep the count low: a CRM lead module ships six configurable permissions, not thirty — the rest are merged into those six or implied by them.

**Roles that are actually people.** `role_zhang_san` means the model failed. If a role has exactly one holder and a person's name, either the role decomposition is wrong or that user needs a per-object grant.

**Modeling the org chart as the permission model.** The org chart changes for reasons unrelated to permissions (reorgs, headcount, politics). Reference it, derive from it, but do not make every reorg a permission migration.

## When Not To Build A Permission System

Push back, briefly and once, if:

- There are fewer than ~10 users and no plan to grow. Two hardcoded roles in a config file is the honest answer, and it is trivially replaceable later.
- Nobody can name the roles. If product cannot list them, the design step has not happened, and a matrix built from guesses will be rebuilt.
- The request is really authentication ("add login"), or really audit ("who changed this"). Different systems; say so and build the right one.

If the user hears the concern and still wants the full system, build the full system — the concern is stated once, not relitigated.
