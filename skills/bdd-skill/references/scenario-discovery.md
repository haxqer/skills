# Scenario Discovery

Use this file when the input is a PRD, a user story, a QA note, or a partial
workflow and the concrete scenarios have not been spelled out yet.

## Extract the Behavior Model

For each feature, identify:

- Actor: who triggers the behavior.
- Goal: what outcome the actor wants.
- Trigger: what event starts the flow.
- Preconditions: what must already be true.
- Rule: what policy or constraint governs the decision.
- Result: what the actor or system can observe afterward.
- Failure modes: what should happen when the rule is not satisfied.

If one of these is missing, do not hide the gap inside the Gherkin. State a
short assumption or open question before the scenarios.

## Discover the Minimum Useful Scenario Set

Start with the smallest set that still defines the behavior:

1. Happy path.
2. Most important rejection or validation path.
3. Boundary condition at the edge of a rule.
4. Permission or state conflict if it changes user-visible behavior.
5. Side effect or notification if it matters to acceptance.

Do not try to encode every technical edge case unless the user asks for
exhaustive coverage.

## Scenario Prompts for Three Amigos Discussions

Use prompts like these to surface hidden rules:

- What business outcome is this feature supposed to protect or enable?
- What makes the request valid or invalid?
- What happens exactly at the threshold value?
- What can the user or operator observe after the action?
- Which states block the action entirely?
- Are there retries, duplicates, or time windows that matter?
- Does authorization change the behavior?
- Are there downstream side effects that must be visible in acceptance?

## Common Coverage Buckets

Consider these buckets when the domain is complex:

- Success path
- Input validation
- Boundary values
- Permission or role differences
- State transition conflicts
- Time-based rules
- External dependency failure
- Idempotency or duplicate submission
- Notification or audit trail

Use only the buckets that materially affect business behavior.

## Example Transformation

Raw requirement:

`As a customer, I can cancel an order before it ships.`

Derived scenario candidates:

- Cancel a paid order before shipment.
- Reject cancellation after shipment.
- Reject cancellation when the order is already cancelled.
- Show the refund state if payment was already captured.

Possible assumptions or open questions:

- Whether partial shipment counts as shipped.
- Whether cancellation triggers an immediate refund or a pending refund.

## Review Before Finalizing

- Check that each scenario proves a rule, not just a click path.
- Check that every `Then` is observable.
- Check that scenario names distinguish the rule being demonstrated.
- Check that omitted cases are either intentionally out of scope or called out.
- Check that the same term is used consistently for the same concept.
