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

## Interruption Recovery

Use this section when a Codex or CLI run is interrupted by a model-capacity error, transient network failure, host reset, or similar non-semantic stop.

### Recovery Principles

- Treat the interruption as transport failure, not task completion.
- Rebuild context from repository state before trusting conversational memory.
- Recover the latest validation signal before editing more code.
- Resume with one validated next step instead of replaying the whole task.
- Avoid duplicate side effects such as installs, migrations, deploys, data writes, or destructive git operations unless they are known to be safe to rerun.

### Standard Resume Prompts

Choose the narrowest prompt that matches the recovery path.

#### Recommended Default Prompt, Chinese

Use this as the default copy-ready prompt for everyday recovery after a capacity error or dropped session.

```text
使用 $ralph-loop。上一轮 Codex/CLI 因容量或连接问题中断。
不要依赖聊天记忆，先从当前仓库状态恢复：检查 git status、变更文件、最近 diff、失败的测试/日志，以及已有任务说明。
然后：
1. 用一句话重述目标。
2. 列出完成标准。
3. 区分哪些已经完成，哪些仍未完成。
4. 继续当前最高价值的下一步。
5. 完成后立刻做最小但有效的验证。
不要重复已经成功的编辑、安装、迁移或其他有副作用的命令，除非你先确认确实还需要执行。
除非任务已完成或遇到真实阻塞，否则继续闭环执行，不要停下来询问是否继续。
```

#### 1. Same Session, Minimal Retry

Use when the session is still open and you only need the agent to continue safely after a transient failure.

```text
Continue from the last completed step.
First inspect the current repository state and latest validation signal.
Summarize what is already done in 3 bullets max.
Then resume the next highest-value unresolved item.
Do not repeat edits or commands that already succeeded.
```

#### 2. Fresh Session After Capacity Error

Use when the prior session is gone or unreliable and you need a clean recovery from repo state.

```text
Use $ralph-loop. The previous Codex session was interrupted by a model-capacity error.
Reconstruct state from the repository, git diff, pending failures, and recent task artifacts instead of assuming chat memory.
Then:
1. State the goal in one sentence.
2. List the done criteria.
3. Summarize what appears completed vs still unresolved.
4. Resume with the single highest-value next step.
5. Validate immediately after that step.
Do not redo successful edits, installs, migrations, or external side effects unless you verify they are still needed.
Stop only if the task is complete or you hit a real blocker.
```

#### 3. CLI-Oriented Strict Resume

Use when you want an explicit repo-first recovery routine in Codex CLI.

```text
Use $ralph-loop. Resume this interrupted task from repo state, not chat history.
Start by checking git status, changed files, failing tests or logs, and any task notes.
Report a brief recovery summary, then continue the loop until done.
Never ask whether to continue.
Never repeat successful commands blindly.
For any command with possible side effects, verify necessity before rerunning it.
```

#### 4. Large Task With Durable Checklist

Use when the task spans many loops and the next agent should refresh or maintain a short checklist before continuing.

```text
Use $ralph-loop. The previous run was interrupted.
Before editing, inspect the repo and rebuild a short ordered checklist from the current state, existing TODOs, failing checks, and changed files.
Mark what is already complete, identify the single next unresolved item, implement only that item, and validate it.
Keep the checklist durable in the repo only if it materially improves continuation.
Do not duplicate completed edits or rerun side-effecting commands without verification.
Continue looping until the explicit done criteria are satisfied or a real blocker remains.
```

#### 5. Patch-Safe Resume For Risky Replays

Use when the prior run may have partially edited files and you want the agent to be conservative.

```text
Use $ralph-loop. Recover this interrupted task conservatively.
Inspect the existing diffs and file contents before making any new edits.
Assume partial progress may already be present.
First identify which intended changes are already applied, which are partial, and which are still missing.
Only add the missing pieces, then run the smallest useful validation.
Do not overwrite or reformat unrelated user changes.
```

### Prompt Selection Guide

- Use prompt 1 for a quick in-place retry.
- Use prompt 2 as the default after "Selected model is at capacity" or any hard session drop.
- Use prompt 3 when driving Codex CLI directly and you want an explicit repo inspection sequence.
- Use prompt 4 for broad tasks that benefit from a durable checklist.
- Use prompt 5 when there is a high risk of duplicated edits or partially applied changes.

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
- You need a standard recovery prompt after a capacity error or interrupted session.
