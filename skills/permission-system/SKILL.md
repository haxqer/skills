---
name: permission-system
description: "Design and implement a complete authorization system: RBAC roles, menu/page/button-level function permissions, and row-level and column-level data permissions, from model selection through database schema, runtime enforcement, caching, and over-privilege testing. Use for 权限系统, 权限设计, 权限管理, RBAC, 角色管理, 菜单权限, 按钮权限, 数据权限, 数据范围, 字段权限, 组织架构, 部门与职位继承, 多租户, 套餐版本权限, 越权. Trigger whenever the user wants to add authorization to an admin system or backend, design permission tables, choose between ACL / RBAC0-3 / user groups / ABAC, build a role-permission matrix, control which rows or columns a role can see, wire dynamic menu trees and button-level guards, model SaaS plan limits, or debug over-privilege bugs — even when they only say 给后台加个权限 without naming RBAC. Not for authentication (login, password, OAuth, SSO, token issuance): that is identity, not authorization."
---

# Permission System

Own the whole chain from "who should be able to do what" to code that enforces it: model selection, role and permission analysis, the permission matrix, schema, runtime enforcement, caching, and the tests that prove a normal user cannot reach an admin endpoint.

This skill is language- and framework-agnostic. It describes the model, the algebra, the tables, and the enforcement points; translate them into whatever stack the project already uses.

**Authorization only.** Authentication — login, passwords, OAuth/SSO, token issuance and refresh — is a separate problem. Assume the request already carries a trusted, verified user identity.

## The One Idea Everything Follows From

Permission design is the art of **reducing the number of mappings you maintain**. Binding permissions directly to users (ACL) means N users × M permissions of hand-maintained edges; every new hire is a config session and every policy change is a sweep. So you insert an intermediary — role, department, position, permission group — and one unmaintainable many-to-many collapses into two small ones.

Every intermediary you add cuts maintenance cost **and** adds one more place a permission can come from. Add enough of them and nobody — including you, at 2am, with an angry customer on the phone — can answer *"why does this user have this button?"*

Keeping that question answerable by one query is the constraint that settles most of the design arguments you are about to have. When in doubt, choose the design whose answer is shorter.

## Non-Negotiable Rules

- **The server decides.** Menu trees, hidden buttons, and greyed-out fields are UX. Every endpoint re-checks on its own. A permission enforced only in the frontend is not a permission — it is a suggestion shipped to the attacker's machine.
- **Check permission codes, never role names.** `if (user.role == "admin")` sprinkled through the code collapses RBAC back into ACL: every new role becomes a code change, and no config screen can ever fix a mis-grant. Check `can("order:refund")`.
- **Permission codes are a public contract.** Once shipped they live in seed data, role grants, source code, customer configs, and integration scripts. Renaming one is a migration, not an edit. Settle the naming convention before writing the first code.
- **Prefer one grant path; if there are several, write down the precedence.** Bind function permissions to a single entity where you can (单一绑定原则) — a system where departments, positions, roles, and users can all grant permissions produces results nobody can explain. If the business truly needs several, make them all pure unions (no deny) so the answer stays "the union of these three grants".
- **Row and column filters live in the data-access layer, applied once.** Re-implementing them per query guarantees the one forgotten detail endpoint that returns another tenant's record.
- **Tenant isolation is not a permission.** It sits below the permission layer and is never bypassable — not by a super admin, not by a wildcard grant, not by a support tool.
- **Visible ≠ writable.** Read scope and write scope are separate decisions. Users routinely need to see their whole department and edit only their own rows.

## The Permission Algebra

Four operations in a fixed order. Choosing the right operator for each is most of the design work:

```
0. tenant boundary   hard filter, applied first, never bypassable
1. allowed_actions   ( ⋃ grants from roles, dept-roles, position-roles )  ∩  plan_ceiling(tenant)
2. visible_rows      widest data scope among the roles granting that action  (∪ of filters)
3. visible_fields    ⋃ field whitelists of those roles
```

Read it as: **grants add up, plans cap, scopes widen, fields project.**

- **Grant is union (∪).** Multiple roles, a role from the user's department, a role from their position — all add. This is why RBAC stays explainable: more roles can only ever mean more access.
- **Ceiling is intersection (∩).** SaaS plan/edition/version and per-customer entitlements are an upper bound, not a grant. A Pro-plan tenant admin with a wildcard role still cannot use an Enterprise feature. Modeling the plan as another grant instead of a ceiling is the most common SaaS permission bug.
- **Row scope is widest-wins.** If one role sees their own department and another sees all departments, the user sees all departments. Do not intersect scopes — users hold roles precisely to gain reach.
- **Field access is a projection**, applied on read, on write, and on export. All three, or the field permission is decorative.

**On explicit deny:** pure RBAC has none, and that is a feature — union is associative, order-free, and explainable. Adding deny rules forces you to define precedence, breaks the one-query explanation, and creates rules that fire only for users holding an unlucky role pair. Reach for mutually exclusive roles (RBAC2 SSD) or narrower roles first. If you must have deny, make deny always win and log which rule fired.

## Workflow

Work in this order. Steps 1–4 are design and produce the artifact that unblocks coding; 5–7 are implementation.

**1. Choose the model before creating a single table.** Match the model to the actual complexity — over-modeling costs as much as under-modeling. See [references/model-selection.md](references/model-selection.md) for the decision table and the three classic design traps (唯RBAC论 / 唯自由配置论 / 权限越细越好).

**2. Enumerate roles.** From the org chart for internal systems, from the business process for everything else. Then find the relationships between them: hierarchy, mutual exclusion, co-holdable, sequential. Decide which are built-in (system-owned, not editable), which are user-definable, and which are hidden (super admin).

**3. Enumerate permissions.** Function permissions via a feature list — page by page, operation by operation. Data permissions in four kinds: system-wide, per-object (table), per-row, per-column.

**4. Build the permission matrix.** Features × roles, with a data-scope rule column. This single artifact is the contract between product, backend, frontend, and QA, and it is also where the test cases come from. Template: [assets/templates/permission-matrix.csv](assets/templates/permission-matrix.csv). Method: [references/requirements-and-matrix.md](references/requirements-and-matrix.md).

**5. Write the schema.** Core tables, the org tables you actually need, data-scope and field-permission tables, seeds. See [references/data-model.md](references/data-model.md) and the reference DDL in [assets/templates/schema.sql](assets/templates/schema.sql).

**6. Enforce.** Permission codes, the menu tree, server-side checks, the data-access filter, cache and invalidation. See [references/function-permissions.md](references/function-permissions.md), [references/data-permissions.md](references/data-permissions.md), [references/runtime-and-hardening.md](references/runtime-and-hardening.md).

**7. Test the negative cases.** A permission system with only happy-path tests is untested. Generate an allow/deny matrix test from step 4, then add horizontal and vertical over-privilege cases. Checklist in [references/runtime-and-hardening.md](references/runtime-and-hardening.md).

Validate the design artifact before implementing it:

```bash
python skills/permission-system/scripts/validate_permission_model.py path/to/permission-model.json
```

The validator catches what humans miss in a large matrix: buttons granted without their parent menu, write permissions granted without the matching read, permissions no role can reach, grants above the plan ceiling, malformed codes, and broken menu-tree parentage. Input format: [assets/templates/permission-model.example.json](assets/templates/permission-model.example.json).

## Core Data Model At A Glance

```
user ──< user_role >── role ──< role_permission >── permission (dir | menu | button)
 │                      │                                └── code: "system:user:create"  ← the contract
 │                      ├── data_scope: ALL | CUSTOM | DEPT_AND_BELOW | DEPT | SELF
 │                      ├──< role_dept >── dept            (only when scope = CUSTOM)
 │                      └──< role_field >── per-resource field whitelist
 ├── dept_id ── dept (ancestors path "/1/4/9/") ──< dept_role >    ← only if depts grant
 └── position_id ── position (level) ──< position_role >           ← only if positions grant
```

Design choices worth making deliberately, all covered in [references/data-model.md](references/data-model.md):

- **One `permission` table with a `type` column** (directory / menu / button), not separate menu and permission tables. The menu tree *is* the permission tree; splitting them guarantees they drift.
- **Materialize the department `ancestors` path.** Recursive subtree queries on every request are how permission checks end up on the slow-query log.
- **Store the plan ceiling separately** from role grants so a downgrade does not destroy the customer's role configuration.

## Route To The References

Read the ones relevant to the task rather than all of them.

- [references/model-selection.md](references/model-selection.md) — ACL, RBAC0/1/2/3, user and permission groups, ABAC; when each pays for itself; the decision table; design traps; when *not* to build RBAC.
- [references/requirements-and-matrix.md](references/requirements-and-matrix.md) — how to enumerate roles and permissions, role relationships, built-in vs custom vs hidden, permission merging, and how to fill in the matrix so engineers can implement from it directly.
- [references/data-model.md](references/data-model.md) — every table, field by field, with the reasoning; indexes; seed and migration strategy; what to leave out.
- [references/function-permissions.md](references/function-permissions.md) — the permission-code naming contract, directory/menu/button semantics and their fields, dynamic menu trees, server-side check placement, frontend guards, permission groups, super admin, and enforcing role mutual exclusion.
- [references/data-permissions.md](references/data-permissions.md) — row scope (management range, department subtree, ownership, custom sets), sharing data outward, applying filters in the data layer, column whitelists on read/write/export, and the over-privilege test checklist.
- [references/runtime-and-hardening.md](references/runtime-and-hardening.md) — the per-request resolution pipeline, caching and invalidation, propagating permission changes, audit logging, and the failure modes that reach production.
- [references/saas-and-versioning.md](references/saas-and-versioning.md) — plan/edition ceilings, usage quotas, per-customer entitlements, upgrade and downgrade behavior.
- [references/worked-example.md](references/worked-example.md) — one system carried end to end: matrix → DDL → resolution pseudocode → tests. Read this first if the abstractions feel thin.

## Failure Modes To Watch For

These are what actually goes wrong, in rough order of how often:

1. **Frontend-only enforcement.** The menu hides it; the endpoint serves it to anyone with the URL.
2. **Role-name checks in business logic.** Makes the permission screens cosmetic.
3. **The forgotten detail endpoint.** List queries get the row filter; `GET /order/{id}` does not. Horizontal over-privilege ships.
4. **Read scope reused as write scope.** A user who can see the whole department can edit the whole department.
5. **Permissions cached without invalidation.** Revoking a role takes effect at next login, which may be never.
6. **Grants from four places.** Nobody can explain an effective permission set, so nobody dares change it.
7. **Codes renamed during a refactor.** Existing customer role configs silently lose permissions.
8. **Column permission applied on read only.** The export endpoint and the update endpoint leak or accept the field anyway.
9. **Plans modeled as grants.** Upgrading a plan does not restore what a downgrade deleted.
10. **Permissions split so finely that no one configures them correctly.** 权限越细越好 is false: 30 well-chosen codes beat 300 that admins tick at random.
