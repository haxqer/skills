# Delegation Templates

Use these templates as starting points. Keep prompts short, concrete, and scoped.

## Contents

- `Tool Mapping`
- `Default Inheritance`
- `Explorer Prompt`
- `Worker Prompt`
- `Review Prompt`
- `Assignment Checklist`

## Tool Mapping

- Start a new subagent with `spawn_agent`.
- Send follow-up instructions with `send_input`.
- Wait only when the next critical step needs the result by using `wait_agent`.
- Retire finished agents with `close_agent`.

## Default Inheritance

- Prefer `spawn_agent` without `model` or `reasoning_effort`.
- Let the subagent inherit the lead agent's model and configuration.
- Prefer `fork_context: false` unless the full thread is required.

## Explorer Prompt

Use for read-only discovery, inventories, or codebase questions.

```text
Use $subagents at <skill-path> to handle this subtask.

Role: Explorer
Goal: <question to answer>
Why this matters: <one sentence>
Scope: Read-only in <paths>
Constraints:
- do not modify files
- cite concrete file paths and lines when possible
- call out uncertainty instead of guessing

Deliverable:
- concise answer
- supporting file references
- risks, gaps, or follow-up suggestions

You are not alone in the codebase. Stay within the assigned scope.
```

## Worker Prompt

Use for bounded implementation or test work with a disjoint write scope.

```text
Use $subagents at <skill-path> to handle this subtask.

Role: Worker
Goal: <implementation goal>
Why this matters: <one sentence>
Branch: <branch-name>
Owned files: <paths>
Non-goals: <what not to touch>
Constraints:
- create and stay on the assigned branch
- keep changes scoped to the owned files
- do not revert edits made by others
- report blockers early
- run the required checks before handing work back

Deliverable:
- summary of changes
- branch name and commit hashes
- files changed
- tests or checks run
- remaining risks or blockers

You are not alone in the codebase. Adjust to existing edits instead of overwriting them.
```

## Review Prompt

Use for an independent pass on risk, regressions, or missing validation.

```text
Use $subagents at <skill-path> to handle this subtask.

Role: Reviewer
Goal: Review <change or area> for bugs, regressions, and missing validation
Scope: Read-only in <paths>
Focus:
- correctness
- behavioral regressions
- missing tests

Deliverable:
- findings ordered by severity
- file references
- open questions or assumptions

You are not alone in the codebase. Do not modify files unless explicitly asked.
```

## Assignment Checklist

Before spawning a subagent, confirm:

- the task is actually parallelizable
- the lead agent keeps the next blocking step
- each coding worker has a unique branch name
- the write scope is disjoint from other workers
- the expected output is specific enough to evaluate quickly
- the lead agent has useful local work to do while the subagent runs
