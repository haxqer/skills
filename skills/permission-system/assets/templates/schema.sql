-- =============================================================================
-- Reference DDL for an RBAC permission system.
--
-- Written in portable SQL. Adapt types and identifier style to the project's
-- database and existing conventions -- matching the surrounding codebase beats
-- matching this file.
--
--   BIGINT     -> the project's id type (serial, uuid, snowflake)
--   VARCHAR(n) -> text / nvarchar
--   BOOLEAN    -> tinyint(1) / bit
--   TIMESTAMP  -> datetime / timestamptz
--
-- Sections are ordered by necessity. Start with CORE. Add the rest only when
-- the permission matrix actually requires it -- every extra table is either a
-- new grant path or a new filter, and both cost explainability.
-- =============================================================================


-- =============================================================================
-- 1. CORE -- RBAC0. The minimum viable set.
-- =============================================================================

-- The permission registry AND the menu tree. One table, not two: the menu the
-- frontend renders and the permissions the server checks are then provably the
-- same data.
CREATE TABLE permission (
    id           BIGINT       NOT NULL PRIMARY KEY,
    parent_id    BIGINT       NULL,                    -- NULL = top level
    code         VARCHAR(128) NOT NULL,                -- 'system:user:create' -- the contract; never renamed
    name         VARCHAR(64)  NOT NULL,                -- display label; free to rename
    type         VARCHAR(16)  NOT NULL,                -- dir | menu | button
    sort         INT          NOT NULL DEFAULT 0,
    icon         VARCHAR(64)  NULL,                    -- dir / menu only
    route_path   VARCHAR(255) NULL,                    -- required for menu; absent for button
    component    VARCHAR(255) NULL,                    -- frontend component path
    is_external  BOOLEAN      NOT NULL DEFAULT FALSE,  -- route_path must be http:// or https://
    visible      BOOLEAN      NOT NULL DEFAULT TRUE,   -- routable but hidden from the menu
    cacheable    BOOLEAN      NOT NULL DEFAULT FALSE,  -- frontend keep-alive hint
    status       VARCHAR(16)  NOT NULL DEFAULT 'enabled',  -- disabled denies everyone, holders included
    created_at   TIMESTAMP    NOT NULL,
    updated_at   TIMESTAMP    NOT NULL,
    CONSTRAINT uk_permission_code UNIQUE (code),
    CONSTRAINT fk_permission_parent FOREIGN KEY (parent_id) REFERENCES permission (id)
);
CREATE INDEX idx_permission_parent ON permission (parent_id);

CREATE TABLE role (
    id           BIGINT       NOT NULL PRIMARY KEY,
    tenant_id    BIGINT       NULL,                    -- NULL for system-wide built-ins
    code         VARCHAR(64)  NOT NULL,
    name         VARCHAR(64)  NOT NULL,
    is_builtin   BOOLEAN      NOT NULL DEFAULT FALSE,  -- seed-owned; tenants may not edit
    is_hidden    BOOLEAN      NOT NULL DEFAULT FALSE,  -- never listed in the tenant UI
    data_scope   VARCHAR(24)  NOT NULL DEFAULT 'SELF', -- ALL|CUSTOM|DEPT_AND_BELOW|DEPT|SELF (read)
    write_scope  VARCHAR(24)  NULL,                    -- NULL = same as data_scope. Visible != writable.
    status       VARCHAR(16)  NOT NULL DEFAULT 'enabled',
    sort         INT          NOT NULL DEFAULT 0,
    remark       VARCHAR(255) NULL,
    created_at   TIMESTAMP    NOT NULL,
    updated_at   TIMESTAMP    NOT NULL,
    CONSTRAINT uk_role_code UNIQUE (tenant_id, code)
);

CREATE TABLE user_role (
    user_id    BIGINT    NOT NULL,
    role_id    BIGINT    NOT NULL,
    granted_by BIGINT    NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, role_id)
);
CREATE INDEX idx_user_role_role ON user_role (role_id);   -- for "who holds this role" on invalidation

CREATE TABLE role_permission (
    role_id       BIGINT    NOT NULL,
    permission_id BIGINT    NOT NULL,
    created_at    TIMESTAMP NOT NULL,
    PRIMARY KEY (role_id, permission_id)
);
CREATE INDEX idx_role_permission_perm ON role_permission (permission_id);

-- Columns the permission system expects on the user table.
-- ALTER TABLE app_user ADD COLUMN tenant_id       BIGINT      NOT NULL;
-- ALTER TABLE app_user ADD COLUMN dept_id         BIGINT      NULL;
-- ALTER TABLE app_user ADD COLUMN position_id     BIGINT      NULL;
-- ALTER TABLE app_user ADD COLUMN is_super_admin  BOOLEAN     NOT NULL DEFAULT FALSE;
-- ALTER TABLE app_user ADD COLUMN status          VARCHAR(16) NOT NULL DEFAULT 'enabled';


-- =============================================================================
-- 2. ORGANIZATION -- add only if the matrix uses departments or positions.
-- =============================================================================

CREATE TABLE dept (
    id             BIGINT       NOT NULL PRIMARY KEY,
    tenant_id      BIGINT       NOT NULL,
    parent_id      BIGINT       NULL,
    -- Materialized path: '/1/4/9/'. Subtree resolution runs on nearly every
    -- request; without this it is a recursive walk per request.
    ancestors      VARCHAR(512) NOT NULL DEFAULT '/',
    name           VARCHAR(64)  NOT NULL,
    leader_user_id BIGINT       NULL,
    sort           INT          NOT NULL DEFAULT 0,
    status         VARCHAR(16)  NOT NULL DEFAULT 'enabled',
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL
);
CREATE INDEX idx_dept_ancestors ON dept (ancestors);      -- supports LIKE '/1/4/%'
CREATE INDEX idx_dept_parent    ON dept (tenant_id, parent_id);

CREATE TABLE position (
    id         BIGINT      NOT NULL PRIMARY KEY,
    tenant_id  BIGINT      NOT NULL,
    code       VARCHAR(64) NOT NULL,
    name       VARCHAR(64) NOT NULL,
    -- Seniority. DOCUMENT THE DIRECTION HERE: lower number = more senior.
    -- Getting this backwards is a silent privilege inversion.
    level      INT         NOT NULL DEFAULT 0,
    sort       INT         NOT NULL DEFAULT 0,
    status     VARCHAR(16) NOT NULL DEFAULT 'enabled',
    CONSTRAINT uk_position_code UNIQUE (tenant_id, code)
);

-- Extra grant paths. Each one is another place a permission can come from, so
-- add them only if the matrix needs them. Resolution stays a pure union.
CREATE TABLE dept_role (
    dept_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (dept_id, role_id)
);

CREATE TABLE position_role (
    position_id BIGINT NOT NULL,
    role_id     BIGINT NOT NULL,
    PRIMARY KEY (position_id, role_id)
);


-- =============================================================================
-- 3. DATA PERMISSIONS
-- =============================================================================

-- The explicit department set for roles whose data_scope = 'CUSTOM'.
CREATE TABLE role_dept (
    role_id BIGINT NOT NULL,
    dept_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, dept_id)
);

-- Column whitelist. Whitelist, never blacklist: with a blacklist every newly
-- added model field is exposed to every role by default, and that fails silently.
-- No rows for a resource means no field restriction on it.
CREATE TABLE role_field (
    role_id  BIGINT      NOT NULL,
    resource VARCHAR(128) NOT NULL,     -- 'candidate:student'
    field    VARCHAR(64)  NOT NULL,     -- as the API exposes it
    access   VARCHAR(16)  NOT NULL,     -- read | write | masked | none
    PRIMARY KEY (role_id, resource, field)
);

-- Per-object sharing. Genuinely ACL-shaped, so it gets its own table -- folding
-- it into role_permission is how role tables reach millions of rows.
CREATE TABLE resource_grant (
    id            BIGINT       NOT NULL PRIMARY KEY,
    tenant_id     BIGINT       NOT NULL,
    resource_type VARCHAR(64)  NOT NULL,
    resource_id   BIGINT       NOT NULL,
    grantee_type  VARCHAR(16)  NOT NULL,   -- user | role | dept
    grantee_id    BIGINT       NOT NULL,
    access        VARCHAR(16)  NOT NULL,   -- read | write
    granted_by    BIGINT       NOT NULL,
    expires_at    TIMESTAMP    NULL,       -- if set, something must sweep it AND the check must test it
    created_at    TIMESTAMP    NOT NULL,
    CONSTRAINT uk_resource_grant UNIQUE (resource_type, resource_id, grantee_type, grantee_id)
);
CREATE INDEX idx_resource_grant_grantee ON resource_grant (grantee_type, grantee_id);

-- Every scoped business table needs these two columns, added up front.
-- Retrofitting an ownership column onto live data is an expensive migration.
--   ALTER TABLE <business_table> ADD COLUMN tenant_id BIGINT NOT NULL;
--   ALTER TABLE <business_table> ADD COLUMN dept_id   BIGINT NOT NULL;
--   ALTER TABLE <business_table> ADD COLUMN owner_id  BIGINT NOT NULL;
--   CREATE INDEX idx_<t>_scope ON <business_table> (tenant_id, dept_id);
--   CREATE INDEX idx_<t>_owner ON <business_table> (tenant_id, owner_id);


-- =============================================================================
-- 4. CONSTRAINTS (RBAC2) -- only if separation of duty is a real requirement.
-- =============================================================================

-- Roles that may never be held by the same user. Enforced at every assignment
-- path -- including bulk import, and including role edits, since adding a
-- permission to one role can retroactively violate an exclusion.
CREATE TABLE role_mutex (
    role_id_a BIGINT       NOT NULL,
    role_id_b BIGINT       NOT NULL,
    reason    VARCHAR(255) NULL,
    PRIMARY KEY (role_id_a, role_id_b)
);


-- =============================================================================
-- 5. SAAS -- plans are a CEILING, never a grant. See saas-and-versioning.md.
-- =============================================================================

CREATE TABLE plan (
    code VARCHAR(32) NOT NULL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    sort INT         NOT NULL DEFAULT 0
);

CREATE TABLE plan_permission (
    plan_code       VARCHAR(32)  NOT NULL,
    permission_code VARCHAR(128) NOT NULL,   -- may be a wildcard such as 'report:*'
    PRIMARY KEY (plan_code, permission_code)
);

-- Per-customer exceptions on top of the plan. Require reason and granted_by:
-- an entitlement nobody can explain becomes untouchable.
CREATE TABLE tenant_entitlement (
    tenant_id       BIGINT       NOT NULL,
    permission_code VARCHAR(128) NOT NULL,
    allowed         BOOLEAN      NOT NULL,
    reason          VARCHAR(255) NOT NULL,
    granted_by      BIGINT       NOT NULL,
    expires_at      TIMESTAMP    NULL,
    PRIMARY KEY (tenant_id, permission_code)
);

CREATE TABLE tenant_quota (
    tenant_id    BIGINT      NOT NULL,
    quota_key    VARCHAR(64) NOT NULL,       -- 'export_per_month', 'admin_seats'
    limit_value  BIGINT      NOT NULL,
    used_value   BIGINT      NOT NULL DEFAULT 0,   -- increment atomically
    period_start TIMESTAMP   NULL,
    PRIMARY KEY (tenant_id, quota_key)
);

-- On the tenant table:
--   ALTER TABLE tenant ADD COLUMN plan_code       VARCHAR(32) NOT NULL;
--   ALTER TABLE tenant ADD COLUMN plan_expires_at TIMESTAMP   NULL;
--   -- Bumped inside the same transaction as ANY permission-affecting change.
--   -- One counter beats per-key invalidation: it cannot miss a transitive case.
--   ALTER TABLE tenant ADD COLUMN perm_version    BIGINT      NOT NULL DEFAULT 1;


-- =============================================================================
-- 6. AUDIT -- two logs, two different questions.
-- =============================================================================

-- "Who did what." Log denials too: a burst of 403s from one account is the
-- clearest available signal of enumeration or a broken role assignment.
CREATE TABLE operation_log (
    id              BIGINT       NOT NULL PRIMARY KEY,
    tenant_id       BIGINT       NOT NULL,
    user_id         BIGINT       NOT NULL,
    permission_code VARCHAR(128) NULL,
    action          VARCHAR(128) NOT NULL,
    resource_type   VARCHAR(64)  NULL,
    resource_id     BIGINT       NULL,
    result          VARCHAR(16)  NOT NULL,   -- allowed | denied
    denied_reason   VARCHAR(255) NULL,       -- missing code, out of scope, plan ceiling, quota
    ip              VARCHAR(64)  NULL,
    user_agent      VARCHAR(255) NULL,
    created_at      TIMESTAMP    NOT NULL
);
CREATE INDEX idx_operation_log_user ON operation_log (tenant_id, user_id, created_at);

-- "When did this user get this permission, and who gave it to them." An
-- operation log cannot answer this -- a grant looks like an ordinary admin
-- action -- and it is the question asked during an actual incident.
CREATE TABLE permission_change_log (
    id           BIGINT       NOT NULL PRIMARY KEY,
    tenant_id    BIGINT       NOT NULL,
    actor_id     BIGINT       NOT NULL,
    change_type  VARCHAR(32)  NOT NULL,   -- grant_role | revoke_role | edit_role | change_scope | edit_fields
    target_type  VARCHAR(32)  NOT NULL,   -- user | role | dept | position | tenant
    target_id    BIGINT       NOT NULL,
    before_value TEXT         NULL,
    after_value  TEXT         NULL,
    reason       VARCHAR(255) NULL,
    created_at   TIMESTAMP    NOT NULL
);
CREATE INDEX idx_perm_change_target ON permission_change_log (tenant_id, target_type, target_id, created_at);


-- =============================================================================
-- SEEDS
--
-- Permissions and built-in roles belong in migrations or seed files, never
-- created by hand in the admin UI -- otherwise dev, staging, and production
-- disagree, and the disagreement surfaces as "works on my machine" permission
-- bugs. The seed file is also the reviewable record of what shipped.
--
--   - Adding a code is additive and safe: existing roles simply lack it (deny).
--   - Renaming a code is a migration. Prefer add-new, dual-check, remove-old.
--   - When adding a permission to an existing module, decide EXPLICITLY whether
--     built-in roles receive it. Silence means built-in admin lacks the new
--     button, and it gets reported as a bug on release day.
--   - Never let a migration edit CUSTOM roles -- those belong to the customer.
-- =============================================================================
