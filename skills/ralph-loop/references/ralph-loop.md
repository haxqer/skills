# Ralph Loop Reference

This reference explains the Ralph-style loop that inspired this skill and how to adapt it to Codex without copying Claude Code's host-specific mechanics.

## What Transfers From Ralph

- Prevent premature stopping. The loop should continue until explicit exit criteria are met.
- Re-enter from durable state. Files, plans, tests, logs, and task notes are better loop memory than long conversational context.
- Work one high-value unresolved item at a time.
- Use validation as backpressure. A failing test, typecheck, build, or runtime probe should decide the next action.
- Keep completion evidence concrete rather than relying on a vague sense that the task is probably done.

## What Does Not Transfer Literally

- Claude Code can implement loop control with hooks that intercept stop events. Codex skills cannot assume that mechanism exists.
- Do not require a background daemon, external watchdog, or auto-resume service unless the host actually provides it.
- Do not treat "autonomous" as permission to bypass system, developer, repository, or safety rules.
- Do not assume infinite context. The loop must survive by leaving useful state in the repo and by re-reading the right files each cycle.

## Codex Adaptation Boundary

- In Codex, the loop is behavioral, not infrastructural.
- The agent re-enters the task by inspecting repository state, open failures, and prior edits rather than by relying on a stop hook.
- Progress updates should stay short so they do not become the main memory store.
- If durable task state is needed, prefer an existing checklist, TODO file, spec, failing test, or tightly scoped task note over repeated prose in chat.

## Engineering Protocol

### 1. Define The Contract

- State the goal in one sentence.
- Define or infer done criteria.
- Identify the strongest available validation signals.
- Choose a loop unit that is small enough to validate quickly.

### 2. Run A Single-Item Loop

1. Re-read the contract and latest evidence.
2. Search before assuming.
3. Pick the highest-leverage unresolved item.
4. Change code or task artifacts for that item only.
5. Validate immediately.
6. Use the result to choose the next loop.

### 3. Preserve Durable State

- Leave tests, scripts, comments, or task notes in a state that helps the next loop restart cleanly.
- If a large task spans many loops, maintain a short ordered checklist with enough specificity to resume from repo state alone.
- Avoid making the conversation transcript the only place where progress exists.

### 4. Escalate Only Real Blockers

- Missing credentials or external approvals
- Destructive or production-impacting actions requiring consent
- Legal, privacy, or safety risks
- Ambiguity that would lead to materially different and hard-to-reverse implementations

Before escalating, try local inspection, narrower validation, alternate entry points, logs, nearby code, and project conventions.

## Validation Ladder

- Start narrow: unit test, focused typecheck, single command, targeted runtime reproduction.
- Widen only after the local slice is green.
- When the repo lacks validation, create the smallest useful check that can act as backpressure in the next loop.
- Prefer reproducible checks over manual belief.

## Common Failure Modes

### Drift

Symptoms:
- The agent starts editing adjacent features because they are nearby.
- The task expands faster than evidence of completion.

Response:
- Shrink the loop unit.
- Return to the explicit done criteria.
- Finish the currently failing or unfinished slice before opening another front.

### Motion Without Proof

Symptoms:
- Many edits, weak validation, no concrete evidence.

Response:
- Add or run a stronger local check.
- Remove speculative branches.
- Convert assumptions into executable validation when possible.

### Context Bloat

Symptoms:
- The agent keeps re-explaining the task in chat.
- Important task state is trapped in commentary instead of files or checks.

Response:
- Move durable state into the repo.
- Keep progress updates operational and short.
- Re-read stable artifacts each loop instead of carrying oversized chat context.

### Premature Completion

Symptoms:
- The agent stops after the first passing check even though the overall request is not complete.

Response:
- Compare current evidence against all done criteria, not just the latest fix.
- Ask whether the user requested the whole implementation, the regression fix, or a broader working flow.

## When To Read This Reference

- The task is large enough that loop drift is likely.
- You need to decide what should count as durable loop state.
- You are adapting Ralph ideas to Codex and need the boundary clearly stated.
- The agent keeps wandering, over-talking, or stopping too early.
