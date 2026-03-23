---
name: orchestrate-subagents
description: Plan and execute multi-agent collaboration in Codex. Use when the user explicitly asks for subagents, delegation, or parallel agent work, and the environment exposes `spawn_agent`, `send_input`, `wait_agent`, and `close_agent`; or when an already-authorized task is large enough to benefit from splitting into independent explorer or worker subtasks. Coordinate one lead agent that keeps ownership of user communication, planning, integration, validation, and final decisions, while subagents take tightly scoped assignments under the same inherited model and configuration.
---

# Orchestrate Subagents

## Overview

Use one lead agent and zero or more subagents.

- Keep the lead agent responsible for the task end to end.
- Treat subagents as scoped execution units, not alternate product owners.
- Prefer the smallest number of agents that materially improves throughput.

## Hard Rules

- Spawn subagents only when the user explicitly requested multi-agent or delegation work, or the current thread already authorizes it.
- Keep the lead agent on the critical path. Do the next blocking task locally before delegating sidecar work.
- Keep the same model and configuration across lead and subagents by default. Do not set `model` or `reasoning_effort` on `spawn_agent` unless the user explicitly asks for a different setup.
- Use minimal context by default. Set `fork_context: true` only when the subagent truly needs the full thread state.
- Give every subagent a bounded outcome, an owner role, a branch name, a write scope, and a return contract.
- Do not assign the same writable files to multiple subagents at the same time.
- For coding work, require each subagent to create and use its own branch in its isolated workspace. The lead agent owns integration back to the main branch.
- Tell every worker that it is not alone in the codebase and must not revert edits made by others.
- Keep user communication, plan updates, integration, validation, and the final answer in the lead agent.

## Role Split

### Lead Agent

- Read the repository and form the high-level plan.
- Decide which immediate task to do locally right now.
- Split only independent sidecar work into subagents.
- Define ownership for each subagent: goal, branch, files, constraints, acceptance checks, and expected output.
- Keep working locally after delegation instead of blocking on `wait_agent`.
- Review returned diffs or findings, merge or cherry-pick the approved branch work, and resolve conflicts.
- Run final validation and present the final answer to the user.

### Subagents

- Follow the assigned scope exactly.
- Prefer concrete artifacts over discussion: patches, findings, test results, file lists, blockers.
- Do not widen scope without a clear reason.
- Report assumptions and risks instead of silently inventing policy.
- For coding work, create the assigned branch in the subagent workspace before editing and stay on that branch for the whole task.
- When editing, touch only the owned files or clearly call out why a broader change is required.
- Return the branch name, commit hashes if created, and the exact files changed.
- Stop after delivering the requested artifact; the lead agent decides integration.

## When To Stay Single-Agent

- Stay local for urgent, tightly coupled, or small tasks that are faster to finish in one thread.
- Stay local when the next action is completely blocked on context you have not gathered yet.
- Stay local when multiple subtasks would fight over the same files or the same architectural decision.

## Choose The Split

- Use one `explorer` when you need a codebase answer or inventory that does not block your next local step.
- Use one `worker` when a bounded implementation can proceed in parallel with your own work.
- Use multiple workers only when the write scopes are disjoint and the integration cost is clearly worth it.
- Prefer read-only exploration before parallel code edits when the codebase is unfamiliar.

## Delegation Workflow

1. Stabilize the task boundary.
- Rephrase the user goal, constraints, and success criteria.
- Identify the next blocking local task and keep it with the lead agent.

2. Design the split.
- Separate critical-path work from sidecar work.
- Create independent subtasks with clear ownership and a single deliverable.
- Assign one branch per coding subagent and keep branch ownership one-to-one.
- Avoid duplicate investigation across agents.

3. Launch subagents.
- Use `spawn_agent` with inherited defaults so model and configuration stay aligned.
- Pick `agent_type: explorer` for codebase questions and `agent_type: worker` for execution.
- Pass only the context the subagent needs. Use `fork_context: true` only for tightly coupled tasks.
- For coding tasks, tell the subagent which branch to create, which files it owns, and what validation it must run before handing work back.

4. Keep momentum locally.
- Continue lead-agent work immediately after delegation.
- Use `send_input` for clarifications or mid-course corrections without restarting the whole task.

5. Collect only when needed.
- Use `wait_agent` sparingly, mainly when the next critical step depends on the result or when you are ready to integrate.
- Review finished work promptly once it becomes useful to the critical path.

6. Close the loop.
- Integrate returned work carefully.
- Run tests or validation in the main thread.
- Use `close_agent` when a subagent is no longer needed.

## Prompt Contract

Every subagent assignment should include:

- the exact goal
- why the subtask matters
- the branch name for coding work
- the owned files or read-only scope
- explicit constraints and non-goals
- the required acceptance checks
- the expected output format
- a reminder that the agent is not alone in the codebase
- for workers, a reminder not to revert others' edits

## Same Model And Config

- Do not override `model`.
- Do not override `reasoning_effort`.
- Prefer inheriting the thread defaults so lead and subagents behave consistently.
- If the user explicitly asks for a different model or effort, state the deviation and apply it intentionally.

## Wait Strategy

- Do not call `wait_agent` immediately after `spawn_agent` unless the result blocks the next action.
- Batch waiting near integration points.
- Reuse an existing agent with `send_input` when the follow-up depends on its prior context.
- Close idle agents once their result is consumed.

## Conflict Management

- If two subtasks start to overlap, stop parallel editing, freeze one branch, and consolidate ownership under the lead agent or a single worker.
- If a worker reports an unexpected repo change, treat it as live state and do not revert it blindly.
- If the task cannot be decomposed cleanly, fall back to single-agent execution.

## Branch Workflow

- The lead agent assigns a unique branch name to every coding subagent before work starts.
- The subagent creates that branch inside its own workspace and keeps all commits scoped to the assigned task.
- The subagent reports the branch name, commit hashes, validation results, and changed files when done.
- The lead agent reviews the returned work and is solely responsible for merging or cherry-picking it back to the main branch.
- If the repository state makes safe branch work impossible, stop and choose a read-only or single-agent path instead of improvising.

## Output Contract

When using this skill, the lead agent should usually expose:

1. the task split
2. what stays local versus delegated
3. integration status
4. validation status and any remaining risk

## Trigger Examples

- "Use multiple agents to refactor this service safely."
- "Delegate the test fixes and the UI pass in parallel."
- "Split this repo audit into parallel codebase investigations."
- "Coordinate subagents to implement separate modules."
- "Use one agent for discovery and one for the patch."

## References

- Read `references/delegation-templates.md` when you need reusable prompt shapes for explorer, worker, or review-style delegation.
