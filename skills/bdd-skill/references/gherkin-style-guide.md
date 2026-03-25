# Gherkin Style Guide

## Contents

- `Structure`
- `Step Semantics`
- `Writing Rules`
- `Prefer`
- `Avoid`
- `Background Guidance`
- `Scenario Outline Guidance`
- `Example`

## Structure

- `Feature`: describe one user-visible capability or outcome.
- `Rule`: capture one business rule that governs multiple scenarios.
- `Background`: hold stable shared context used by most scenarios in a feature.
- `Scenario`: show one example of one behavior.
- `Scenario Outline`: reuse one behavior shape across a small table of
  meaningful example values.
- `Examples`: hold only the columns needed to demonstrate the rule.

## Step Semantics

- `Given`: state, context, data preconditions, permissions, or prior events.
- `When`: the trigger or action that changes behavior.
- `Then`: observable outcome.
- `And` or `But`: extend the current semantic group without changing its role.

Keep the semantic transition clean:

- `Given ...`
- `When ...`
- `Then ...`

Avoid mixing roles, such as turning `Then` into another action or using `When`
to smuggle setup.

## Writing Rules

- Name `Feature` and `Scenario` entries after the business behavior, not the
  screen widget or API method.
- Use concrete domain values when they clarify thresholds, permissions, or
  boundaries.
- Keep each scenario short enough to scan quickly. Four to eight steps is a
  good default.
- Prefer one primary trigger in each scenario.
- Express outcomes in terms of state, response, message, notification,
  generated record, or emitted event.
- Reuse product vocabulary consistently. If the product says `member`, do not
  switch to `user` mid-feature unless the distinction matters.

## Prefer

- `Given the account balance is 99 CNY`
- `When the customer confirms the transfer`
- `Then the transfer should be rejected`

- `Scenario: Reject a refund request after the settlement window closes`
- `Rule: Users can redeem only one welcome coupon`

## Avoid

- `Given valid data exists`
- `When the user clicks the blue button in the top-right corner`
- `Then call createOrder()`
- `Scenario: Test checkout`

These examples are vague, UI-fragile, or implementation-focused.

## Background Guidance

Use `Background` only when all of the following are true:

- The context appears in most scenarios in the feature.
- The shared context is stable and not the main point of comparison.
- Pulling it up reduces noise more than it hides meaning.

If a scenario becomes harder to understand because key setup moved into
`Background`, inline the setup instead.

## Scenario Outline Guidance

Use `Scenario Outline` when:

- The same rule is being exercised with a few important values.
- The behavior wording stays the same across rows.
- The table helps expose boundaries or equivalence classes.

Do not use `Scenario Outline` to compress unrelated behaviors into one table.
If the expected outcome changes because a different rule is being tested, split
the scenarios.

## Example

```gherkin
Feature: Password reset

  Rule: A reset link can be used only before it expires

  Scenario Outline: Validate reset link expiry
    Given a user has a password reset link issued <minutes> minutes ago
    When the user opens the reset link
    Then the link should be <status>

    Examples:
      | minutes | status   |
      | 29      | accepted |
      | 30      | accepted |
      | 31      | expired  |
```
