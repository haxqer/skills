# Worked Example: An Online Exam Platform

One system carried end to end — roles, matrix, schema, resolution, enforcement, tests — so the abstractions in the other files have something concrete to attach to. Read this first if they feel thin.

**The system:** a multi-tenant online exam platform. Schools are tenants. Inside a school there are departments (teaching groups), teachers who author questions and manage candidates, group leaders who oversee their group, and a school admin. Sold in Basic and Pro editions.

## Step 1: Model Selection

Walking the decision table in `model-selection.md`:

- Recognizable job functions across many tenants → RBAC0, not ACL.
- Teaching groups with a head who must see the whole group → departments as a user group, plus row-level data scope.
- "Group leader = teacher + extras" is true for one role out of four → **flat roles, no RBAC1.** Leaders hold both roles.
- No separation-of-duty requirement → no RBAC2.
- Question bank sharing between teachers is per-object → a small `resource_grant` table alongside RBAC.
- Two editions → a plan ceiling.

**Chosen: RBAC0 + department user groups + row scope + column whitelist + plan ceiling + object sharing.** Written down in one line so the next person does not re-litigate it.

## Step 2: Roles

| Code | Name | Kind | Purpose | Expected holders |
|---|---|---|---|---|
| `super_admin` | 超级管理员 | Hidden | Platform operations | Platform staff only |
| `school_admin` | 学校管理员 | Built-in | Everything within the school | 1–2 per tenant |
| `group_leader` | 教研组长 | Built-in | Oversees their teaching group | ~10 per tenant |
| `teacher` | 教师 | Built-in | Authors questions, manages own candidates | ~100 per tenant |
| `exam_proctor` | 监考员 | Custom (example) | Runs exam sessions, no authoring | varies |

Relationships: no exclusions, no hierarchy. `group_leader` is held **in addition to** `teacher`, which is why the union rule matters — the leader's effective reach is the wider of the two scopes.

## Step 3–4: The Permission Matrix

Abridged; the full shape is in `assets/templates/permission-matrix.csv`.

| Module | Page | Operation | permission_code | school_admin | group_leader | teacher | proctor | Data scope rule |
|---|---|---|---|---|---|---|---|---|
| Question | Question bank | View list | `question:bank:list` | ✓ | ✓ | ✓ | — | admin: all; leader: own dept + below; teacher: self + shared |
| Question | Question bank | Create | `question:bank:create` | ✓ | ✓ | ✓ | — | writes are owned by the creator |
| Question | Question bank | Edit | `question:bank:edit` | ✓ | ✓ | ✓ | — | **write scope = SELF** for teacher and leader |
| Question | Question bank | Delete | `question:bank:delete` | ✓ | ✓ | — | — | leader: own dept + below |
| Question | Question bank | Export | `question:bank:export` | ✓ | — | — | — | Pro plan only |
| Question | Question bank | Share | `question:bank:share` | ✓ | ✓ | ✓ | — | owner only |
| Candidate | Candidates | View list | `candidate:student:list` | ✓ | ✓ | ✓ | ✓ | admin: all; leader: dept+below; teacher/proctor: self |
| Candidate | Candidates | Edit | `candidate:student:edit` | ✓ | ✓ | — | — | |
| Candidate | Candidates | Export | `candidate:student:export` | ✓ | — | — | — | Pro plan only |
| Exam | Exam sessions | View list | `exam:session:list` | ✓ | ✓ | ✓ | ✓ | |
| Exam | Exam sessions | Start/stop | `exam:session:operate` | ✓ | — | — | ✓ | proctor: assigned sessions only |
| System | Users | View list | `system:user:list` | ✓ | — | — | — | |
| System | Roles | Manage | `system:role:manage` | ✓ | — | — | — | |

Data scopes on the roles:

| Role | read scope | write scope |
|---|---|---|
| `school_admin` | `ALL` | `ALL` |
| `group_leader` | `DEPT_AND_BELOW` | `DEPT_AND_BELOW` for candidates, `SELF` for questions |
| `teacher` | `SELF` (+ shared) | `SELF` |
| `exam_proctor` | `SELF` | `SELF` |

Field rules: `candidate:student.id_card_no` readable by `school_admin` only. `candidate:student.phone` masked for `teacher` and `exam_proctor`.

Plan ceiling: Basic excludes `question:bank:export` and `candidate:student:export`. Pro holds `**`.

Note the two things the matrix made visible that a schema-first approach would have missed: the leader's write scope on questions differs from their read scope, and export is plan-gated rather than role-gated.

## Step 5: Schema

Only the parts specific to this system; the standard tables come from `assets/templates/schema.sql`.

```sql
-- business tables carry the two filter columns from day one
CREATE TABLE question_bank (
  id          BIGINT PRIMARY KEY,
  tenant_id   BIGINT      NOT NULL,
  dept_id     BIGINT      NOT NULL,   -- row scope: department
  owner_id    BIGINT      NOT NULL,   -- row scope: ownership
  title       VARCHAR(255) NOT NULL,
  -- ...
  INDEX idx_scope (tenant_id, dept_id),
  INDEX idx_owner (tenant_id, owner_id)
);

-- object sharing, separate from role grants
CREATE TABLE resource_grant (
  id            BIGINT PRIMARY KEY,
  tenant_id     BIGINT      NOT NULL,
  resource_type VARCHAR(64) NOT NULL,      -- 'question_bank'
  resource_id   BIGINT      NOT NULL,
  grantee_type  VARCHAR(16) NOT NULL,      -- user | role | dept
  grantee_id    BIGINT      NOT NULL,
  access        VARCHAR(16) NOT NULL,      -- read | write
  granted_by    BIGINT      NOT NULL,
  expires_at    TIMESTAMP   NULL,
  UNIQUE KEY uk_grant (resource_type, resource_id, grantee_type, grantee_id)
);
```

Seed data defines the four built-in roles, their grants, their scopes, the permission tree, and the two plans — in a migration, not by hand in the UI, so every environment matches.

## Step 6: Resolution

```
resolve(user):
    if user.is_super_admin: return SUPER          # one bypass, one place

    roles   = user_role(user) ∪ dept_role(user.dept)
    granted = ⋃ role_permission(r) for r in roles where r.status = enabled
    ceiling = plan_permission(tenant.plan) ± tenant_entitlement(tenant)

    return {
        permissions: granted ∩ ceiling,
        read_scope:  widest(r.read_scope  for r in roles),
        write_scope: widest(r.write_scope for r in roles),
        fields:      ⋃ role_field(r) for r in roles,
        version:     tenant.perm_version,
    }
```

Cached at `perm:{tenant}:{user}`, rebuilt when the stored `version` differs from the tenant's current `perm_version`.

A concrete case — 张老师 holds both `teacher` and `group_leader`:

- `permissions` = teacher's ∪ leader's, then capped by the plan. On Basic, `question:bank:export` is dropped even though `school_admin`-style wildcards would have included it.
- `read_scope` = widest(`SELF`, `DEPT_AND_BELOW`) = **`DEPT_AND_BELOW`**. Adding the leader role widened reach, as expected.
- `write_scope` on questions = `SELF`. They see the group's questions and may edit only their own.

## Step 7: Enforcement

```
@requires("question:bank:edit")
PUT /api/question-banks/{id}
    row = repo.findById(id)                  # data layer injects tenant + read scope
    if row is null: return 404
    assertInWriteScope(row)                  # separate check, against the stored row
    body = stripUnwritableFields(body)       # field whitelist on input
    repo.update(row, body)
    audit(...)
```

The data layer attaches the predicate to every query against a scoped resource:

```sql
-- teacher + group_leader, read path
WHERE t.tenant_id = :tenant
  AND ( t.dept_id IN (:subtree_of_own_dept)
        OR t.owner_id = :user_id
        OR EXISTS (SELECT 1 FROM resource_grant g
                    WHERE g.resource_type = 'question_bank'
                      AND g.resource_id   = t.id
                      AND g.grantee_id IN (:user_and_role_and_dept_ids)
                      AND (g.expires_at IS NULL OR g.expires_at > now())) )
```

The subtree comes from `dept.ancestors LIKE '/1/4/%'`, not a recursive walk.

Frontend: the menu tree is pruned server-side; buttons are guarded by code; the `id_card_no` column is omitted from the response for everyone but `school_admin`, so there is nothing for the client to hide.

## Step 8: Tests

Positive cases generate from the matrix — one assertion per filled cell. The hand-written negatives are the ones that catch real bugs:

```
teacher   GET  /api/question-banks/{other_teacher_id}      → 404   # horizontal, detail endpoint
teacher   PUT  /api/question-banks/{group_peer_id}         → 403   # visible but not writable
leader    GET  /api/question-banks?export=true             → 403   # plan ceiling, Basic
teacher   GET  /api/candidates → response has no id_card_no        # field whitelist, read
teacher   PUT  /api/candidates/{own} {"id_card_no": "x"}   → unchanged   # mass assignment
proctor   POST /api/exam-sessions/{unassigned}/start       → 403
admin_A   GET  /api/question-banks/{tenant_B_id}           → 404   # tenant boundary
teacher   GET  /api/question-banks (count)                 → matches filtered rows, not global
any       revoke group_leader, then immediate request      → narrowed scope applies now
```

Fixtures: two tenants, two departments in a parent/child relationship inside tenant A, two teachers in different departments, one leader, one shared question bank, one Basic and one Pro tenant. Everything above is one line each once that fixture exists.

## What This Example Demonstrates

- The matrix surfaced the read/write scope split before any code existed — the split is nearly invisible from the schema.
- Flat roles beat inheritance: 张老师 holding two roles produced the right answer through plain union, with nothing to configure.
- The plan is a ceiling: a Basic tenant's `school_admin` keeps their export grant, inert, and gets it back the moment they upgrade.
- Object sharing stayed out of `role_permission`, so the role tables remained small and readable.
- Every business table carried `dept_id` and `owner_id` from day one, which is what made the single data-layer predicate possible.
