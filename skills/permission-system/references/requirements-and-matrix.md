# Requirements Analysis And The Permission Matrix

The output of this phase is one artifact: a features × roles matrix with a data-scope column. It is the contract between product, backend, frontend, and QA, and it is where the test cases come from. Do not start writing tables before it exists — schema written ahead of the matrix gets rewritten.

## Contents

- [Step 1: Enumerate roles](#step-1-enumerate-roles)
- [Step 2: Enumerate function permissions](#step-2-enumerate-function-permissions)
- [Step 3: Enumerate data permissions](#step-3-enumerate-data-permissions)
- [Step 4: Connect roles to permissions](#step-4-connect-roles-to-permissions)
- [Step 5: Consolidate](#step-5-consolidate)
- [Handoff checklist](#handoff-checklist)

## Step 1: Enumerate Roles

### Find them

Two sources, depending on the system:

- **Internal / enterprise systems:** start from the org chart. Departments and job titles map to roles with reasonable fidelity, and the chart already exists.
- **Everything else (platforms, marketplaces, tools):** derive from the business process. Walk each end-to-end flow and name every party that touches it — submitter, reviewer, approver, operator, auditor, viewer, external partner. Roles that appear in no flow are imaginary; roles that appear in a flow but not the list are the ones you would otherwise discover in QA.

### Find the relationships between them

This is the step that gets skipped, and it determines whether you need RBAC1/RBAC2 at all:

- **Hierarchy / inheritance:** is role B literally "role A plus extras"? If yes throughout, consider inheritance. If it is true for only two of nine roles, use flat roles and accept the small duplication.
- **Mutual exclusion:** which roles must never be held by the same person? Usually finance, approval, and audit pairs. Each one you find is an RBAC2 constraint that has to be enforced at assignment time.
- **Co-holdable:** which roles are routinely stacked? If "salesperson + team lead" is normal, the union must produce something sensible — check it, do not assume.
- **Sequential / parallel:** in a process, does role B only act after role A? Sequence usually belongs to workflow state, not to permissions, but it often reveals a needed status-based attribute condition ("approve only while pending").

### Classify each role

| Kind | Who owns it | Editable by user | Typical use |
|---|---|---|---|
| **Built-in (内置)** | The system, via seed data | No — view only | Common, stable roles shipped with the product: admin, department head, ordinary member |
| **Custom (自定义)** | The customer's admin | Yes — name, permissions, all of it | The long tail of customer-specific needs |
| **Hidden (隐藏)** | The system | Not shown in the UI at all | Super admin, support/impersonation, internal service accounts |

Built-in roles are how you avoid 唯自由配置论: most tenants never create a custom role because the built-ins already fit. Hidden roles must be granted through a controlled path (seed, ops tool with audit) and never appear in the tenant's role list.

Record for each role: code, display name, kind, one-line purpose, expected holder count. Roles with an expected count of one and a person's name are a modeling error — see `model-selection.md`.

## Step 2: Enumerate Function Permissions

Use a **feature list**: walk the product surface page by page and write one row per operation. Structure it as module → page → operation, because that is exactly the shape the permission code and the menu tree will take.

| Module | Page | Operation | Kind | Notes |
|---|---|---|---|---|
| System | User management | View list | read | The page-access permission |
| System | User management | Create | write | |
| System | User management | Edit | write | |
| System | User management | Delete | write | Soft delete |
| System | User management | Reset password | write | Sensitive — separate from Edit |
| System | User management | Export | read | Sensitive — always separate from View |

Judgment calls worth making consciously:

- **Export and import are their own permissions**, always. "Can view 50 rows on screen" and "can walk out with the whole table" are different risks, and auditors treat them differently.
- **Sensitive single actions get their own code** — reset password, refund, transfer ownership, publish, impersonate. Everything else can usually live under create/edit/delete.
- **Page access is a permission.** Without it there is no menu entry to hang the buttons on, and no way to say "read-only access to this page".
- **Do not create a permission per field.** Field-level control is a *data* permission (column whitelist), not a function permission. Mixing them explodes the code list.

## Step 3: Enumerate Data Permissions

Four kinds, by how the restriction cuts the data:

| Kind | Restriction | Example | Where it lives |
|---|---|---|---|
| **System-wide** | None; all tables, all rows | Super admin | A bypass flag, not a rule |
| **Per-object** | Which tables/resources at all | Exam admin manages candidates but not questions | Effectively the function permission on that module |
| **Per-row** | Which records within a table | Department head sees their department and below | `role.data_scope` + filter injection |
| **Per-column** | Which fields within a record | Support sees the name; only finance sees the ID number | `role_field` whitelist + projection |

For each module in the feature list, write the row rule as one plain sentence per role — "sees their own department and all descendants", "sees only records they own", "sees the departments explicitly assigned to this role". Plain sentences here become the `data_scope` enum in `data-permissions.md`; do not invent scope names yet.

Note the ordering constraint: **data permission presupposes function permission.** A role with a row scope but no page access sees nothing at all. When reviewing the matrix, any row with a data rule and no function grant is a bug in the matrix.

## Step 4: Connect Roles To Permissions

Extend the feature list with one column per role, plus a data-rule column. Template: `assets/templates/permission-matrix.csv`.

| Module | Page | Operation | permission_code | Admin | Dept head | Member | Data scope rule |
|---|---|---|---|---|---|---|---|
| System | User mgmt | View list | `system:user:list` | ✓ | ✓ | — | Admin: all. Dept head: own dept + descendants. |
| System | User mgmt | Create | `system:user:create` | ✓ | ✓ | — | Dept head: may only create within own dept subtree |
| System | User mgmt | Delete | `system:user:delete` | ✓ | — | — | |
| System | User mgmt | Export | `system:user:export` | ✓ | — | — | |
| Order | Order list | View list | `order:order:list` | ✓ | ✓ | ✓ | Member: only orders they own |
| Order | Order list | Refund | `order:order:refund` | ✓ | — | — | |

Assign the permission code here, in the matrix, not later in the code. This is the moment the naming convention gets applied consistently; see `function-permissions.md` for the rules.

Fill rules that keep the matrix honest:

- **Mark `—`, never blank.** A blank cell is ambiguous between "denied" and "not decided yet", and the ambiguity is always resolved wrongly.
- **Write scopes for write operations separately.** "Dept head sees the whole subtree" does not answer whether they may *edit* the whole subtree. State both.
- **A row with a write grant but no read grant is a defect.** Flag it. The validator script checks this automatically.
- **Every built-in role gets a column.** Custom roles do not — they are configured by customers at runtime. But do include one representative custom role to confirm the model can express it.

## Step 5: Consolidate

The first draft is always too granular. Two passes:

**Merge permissions that no role distinguishes.** If create, edit, and delete carry identical ✓/— patterns across every role and nobody has asked to separate them, ship one `manage` permission bound to all three buttons. This is the permission-group idea applied at design time, and it is why mature products expose six configurable permissions for a module rather than thirty. You can always split later — splitting one code into three is a clean migration; merging three into one after customers have configured them is not.

**Decide what is user-configurable at all.** Three buckets:

- *Fixed:* the system decides, no UI. Super admin, tenant boundary, internal service permissions.
- *Built-in preset:* shipped as built-in roles the customer picks from. Covers most tenants.
- *Configurable:* exposed in the custom-role screen.

Keeping the configurable bucket small is a feature. Every code in it is a checkbox someone can get wrong.

## Handoff Checklist

The matrix is ready to implement against when:

- [ ] Every role has a code, a kind (built-in / custom / hidden), and a stated purpose.
- [ ] Every operation in the product has a row, including export, import, and every sensitive single action.
- [ ] Every cell is `✓` or `—`; none are blank.
- [ ] Every row has a `permission_code` following the naming convention.
- [ ] Read and write data scopes are stated separately wherever they differ.
- [ ] No role has a write grant without the matching read grant.
- [ ] Mutually exclusive role pairs are listed explicitly.
- [ ] For SaaS: every permission is mapped to the lowest plan that includes it.
- [ ] `validate_permission_model.py` passes with no errors on the machine-readable version.

Convert the matrix to `permission-model.json` (see `assets/templates/permission-model.example.json`) and run the validator. It catches the large-matrix mistakes reliably: orphan permissions, buttons without their parent menu, write-without-read, grants above the plan ceiling, and malformed codes.
