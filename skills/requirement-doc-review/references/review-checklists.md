# Review Checklists

## Shared Rules

- Review the document, not the imagined system.
- Treat missing information as a gap to expose, not a blank to fill silently.
- Prefer actionable issues over broad commentary.
- Call out contradictions between sections, roles, states, or data definitions.
- Mark assumptions explicitly when proposing a solution.

## PM

Check these areas:

- Business objective: Is the business goal explicit and testable?
- Target user: Are personas, roles, or permission scopes clear?
- Scope: Are in-scope and out-of-scope boundaries defined?
- Core flow: Is the primary user journey complete and ordered?
- Exceptional flow: Are rejection, rollback, timeout, retry, cancel, and
  empty-state behaviors defined?
- Business rules: Are thresholds, limits, formulas, statuses, and transitions
  unambiguous?
- Dependency: Are upstream systems, manual operations, and organizational
  dependencies identified?
- Acceptance: Are completion criteria and launch criteria testable?
- Metrics: Are success metrics, monitoring indicators, or business KPIs
  defined?
- Rollout: Are migration, compatibility, pilot, or灰度 requirements defined?

Flag typical PM issues:

- Goal and feature do not line up.
- Roles or permissions are missing.
- State transitions are incomplete.
- Edge cases are omitted.
- Acceptance criteria are too vague to test.
- Release assumptions depend on external teams but are not stated.

## Architect

Check these areas:

- Domain boundary: Are modules, subsystems, and ownership boundaries clear?
- Data model: Are entities, keys, state fields, and relationships defined?
- Contract: Are API, event, batch, and callback contracts explicit?
- Consistency: Are write order, source of truth, and reconciliation rules clear?
- State machine: Are lifecycle states and transitions complete?
- Scalability: Are data volume, throughput, latency, and growth assumptions
  stated?
- Resilience: Are retry, idempotency, fallback, timeout, and compensation
  mechanisms defined?
- Security: Are authentication, authorization, audit, privacy, and sensitive
  data rules covered?
- Observability: Are logs, metrics, traces, alerts, and audit trails needed?
- Extensibility: Can the design survive likely near-term variants?

Flag typical architect issues:

- The source does not define the system of record.
- Cross-service updates lack consistency rules.
- API behavior is described without error contracts.
- State changes exist without transition ownership.
- Performance expectations exist without volume assumptions.
- Security constraints are implied but not written.

## Engineering

### Frontend

Check these areas:

- Screen set: Are all pages, drawers, modals, and embedded states covered?
- Interaction state: Are loading, empty, error, disabled, and success states
  defined?
- Validation: Are required fields, format rules, real-time checks, and message
  copy defined?
- Async flow: Are refresh, retry, debounce, optimistic update, and conflict
  behaviors described?
- Permission handling: Are visibility and action restrictions clear?
- UX consistency: Are labels, actions, and state names consistent across flows?
- Accessibility: Are keyboard flow, focus, readable feedback, and semantic
  constraints considered when relevant?
- Analytics: Are exposure, click, submit, and error tracking points required?

Flag typical frontend issues:

- The happy path exists but failure states are missing.
- The document defines backend status but not UI state mapping.
- Validation rules exist but message timing or copy is absent.
- Permission rules exist but page/component visibility is undefined.

### Backend

Check these areas:

- API contract: Are request fields, response fields, enums, errors, and
  versioning rules defined?
- Data schema: Are persistence fields, indexes, uniqueness, and soft-delete
  rules clear?
- Transaction boundary: Are atomic operations and eventual consistency rules
  defined?
- Idempotency: Are retries and duplicate submissions handled?
- Async processing: Are queue, delay, callback, and compensation rules covered?
- Access control: Are service-side authorization and tenancy rules explicit?
- Failure handling: Are timeout, partial success, rollback, and replay behaviors
  defined?
- Configuration: Are feature flags, environment differences, and dependency
  requirements stated?
- Testability: Can unit, integration, and contract tests be derived from the
  requirement?

Flag typical backend issues:

- Request and response contracts are incomplete.
- State changes depend on async jobs with no retry or compensation rule.
- Duplicate submission risk exists without idempotency design.
- Persistence changes are implied but schema impact is not described.
- External dependency failure is possible but fallback behavior is undefined.

## Recommended Finding Shape

Use a compact structure like this when the issue is important:

### High - Missing rollback rule after payment succeeds but fulfillment fails
- Problem: The document defines payment success and fulfillment success, but not
  the intermediate failure path.
- Impact: Delivery, finance, and customer support will make inconsistent
  decisions.
- Recommendation: Define the source of truth, compensation action, timeout
  limit, and user-facing status copy.
