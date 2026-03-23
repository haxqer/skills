---
name: "bdd-skill"
description: "Write, refine, and review Behavior-Driven Development specifications in Gherkin. Use when Codex needs to convert product requirements, user stories, acceptance criteria, workflows, or QA intent into Given-When-Then scenarios; identify business rules, examples, boundaries, and failure paths; or align product, engineering, and QA on executable behavior specifications."
---

# BDD / Gherkin

## Overview

Turn ambiguous requirements into concise, testable behavior specifications.
Optimize for shared understanding across product, engineering, and QA, not
for implementation detail.

## Working Mode

- Reconstruct the user-visible behavior before writing scenarios.
- Prefer standard Gherkin keywords: `Feature`, `Rule`, `Background`,
  `Scenario`, `Scenario Outline`, `Examples`, `Given`, `When`, `Then`, `And`,
  `But`.
- Preserve the product domain vocabulary from the request. Keep keywords in
  English unless the user explicitly wants localized Gherkin keywords.
- Treat examples as executable acceptance criteria: specific actors, concrete
  data, observable outcomes, and named business rules.
- Make non-blocking assumptions explicit instead of leaving ambiguity hidden in
  the scenarios.

## Workflow

1. Define the behavior surface.
- Extract actor, goal, trigger, preconditions, business rule, observable
  result, and failure modes.
- If the request is incomplete or ambiguous, read
  `references/scenario-discovery.md` and build the smallest safe set of
  assumptions.

2. Discover the scenario set.
- Cover the happy path first.
- Add boundary, validation, authorization, exception, and state-transition
  scenarios that materially affect behavior.
- Group related scenarios under one `Feature`.
- Introduce a `Rule` when multiple scenarios are governed by the same policy.
- Use `Background` only for context repeated across most scenarios and unlikely
  to vary.

3. Write the Gherkin.
- Keep each `Scenario` focused on one behavior.
- Write `Given` as context or state, `When` as the trigger, and `Then` as an
  observable outcome.
- Use `And` or `But` only to extend the same semantic role.
- Use `Scenario Outline` only when the same behavior is exercised with a small
  table of meaningful example values.
- Prefer concrete example data when it clarifies the rule or boundary.

4. Review the result.
- Remove implementation details, UI micro-steps, and internal method names.
- Replace vague terms like `valid data` or `works correctly` with domain
  values and observable outcomes.
- Check that every `Then` can be verified by a user, tester, or system
  observer.
- Call out remaining open questions or coverage gaps after the scenarios.

## Output Contract

When drafting from raw requirements, produce output in this order:

1. `Assumptions / Open Questions`
- Include this section only when the source material is incomplete.
- Keep it short and concrete.

2. `Gherkin Spec`
- Return one or more fenced `gherkin` blocks.
- Use clear scenario names that describe the rule being demonstrated.

3. `Coverage Notes`
- Summarize omitted scenarios, unresolved business rules, or suggested next
  examples only when useful.

When reviewing existing BDD text, keep the original intent, tighten the
language, and list gaps separately instead of silently rewriting around
ambiguity.

## Quality Bar

- Express business behavior, not implementation.
- Keep one behavior per scenario.
- Make results observable: responses, messages, status changes, emitted
  events, notifications, or persisted state.
- Cover at least the happy path plus the most relevant negative or boundary
  paths.
- Prefer a small number of high-signal scenarios over exhaustive but
  repetitive cases.
- Use domain language consistently across steps.
- Avoid hidden preconditions. If a condition matters, state it.
- Avoid `Background` when it obscures what makes a scenario distinct.
- Avoid huge `Examples` tables that mix multiple rules at once.

## Example Shape

```gherkin
Feature: Apply a coupon during checkout

  Rule: A coupon can be used only when the order total meets the threshold

  Scenario: Apply a coupon when the threshold is met
    Given a signed-in customer has items worth 120 CNY in the cart
    And the customer owns a "Spend 100 Save 10" coupon
    When the customer applies the coupon at checkout
    Then the discount should be 10 CNY
    And the amount due should be 110 CNY

  Scenario: Reject a coupon when the threshold is not met
    Given a signed-in customer has items worth 99 CNY in the cart
    And the customer owns a "Spend 100 Save 10" coupon
    When the customer applies the coupon at checkout
    Then the coupon should be rejected
    And the customer should see "Order total does not meet the coupon threshold"
```

## References

- Read `references/gherkin-style-guide.md` when wording, scenario shape, or
  keyword choice needs tightening.
- Read `references/scenario-discovery.md` when the input is a PRD, user story,
  workflow note, or otherwise incomplete requirement and more example discovery
  is needed.
