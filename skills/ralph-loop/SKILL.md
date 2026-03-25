---
name: ralph-loop
description: Drive uninterrupted end-to-end software execution with minimal user interaction using the Ralph Loop engineering protocol. Use when the user wants Codex to keep developing continuously, avoid unnecessary questions, choose reasonable reversible assumptions, push through debugging and validation loops, recover cleanly from interruptions such as model-capacity errors, and only stop for clear completion or truly blocking issues such as destructive actions, missing credentials, legal or safety risk, or irrecoverable ambiguity. Trigger on requests like "don't ask me", "keep going", "work autonomously", "ralph loop", "ralph-loop", "闭环执行", "连续工作", "不要打断", "不要问我", or "一直开发".
---

# Ralph Loop

## Operating Mode

- Run this skill as a Ralph-style closed-loop execution protocol adapted to Codex.
- Do not imitate Claude Code's exact stop-hook mechanics. Import the engineering discipline: explicit exit criteria, one high-value item per loop, durable state, and validation-backed continuation.
- Stay inside system, developer, repository, and safety constraints.
- Read [references/ralph-loop.md](references/ralph-loop.md) when you need Ralph rationale, Codex adaptation boundaries, durable-state guidance, failure-mode handling, or copy-ready resume prompts after interruption.

## Default Resume Prompt

Use this as the default Chinese resume prompt after a capacity error or dropped session:

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

## Set The Loop Contract

- Restate the real goal in one sentence before substantial work.
- Define explicit done criteria as early as possible.
- If the user did not provide done criteria, infer pragmatic ones from the request, repository conventions, and available validation.
- Pick the smallest loop unit that can be validated quickly.
- If the task is large, keep a lightweight ordered checklist in durable form when that materially improves continuity.

## Run The Loop

1. Re-read the goal, active files, open failures, and latest validation signal.
2. Search the codebase before assuming something is missing, broken, or unimplemented.
3. Pick the single highest-value unresolved item that moves the task toward done.
4. Implement only that slice or fix only that failure class.
5. Run the smallest high-signal validation for that slice.
6. If validation fails, debug and retry instead of pausing for approval.
7. If validation passes, update any durable artifacts needed for the next loop.
8. Re-check the done criteria. If not done, continue immediately into the next loop.

## Engineering Rules

- Default to one meaningful item per loop.
- Treat tests, linters, typecheckers, builds, runtime checks, and reproducible scripts as loop backpressure.
- Prefer durable repo state over long conversational reasoning.
- Prefer reversible assumptions over interruptions.
- Match established project conventions unless there is a clear technical reason not to.
- Preserve user changes and adapt to the current worktree instead of reverting unrelated edits.
- Do not stop at analysis if code can be changed and checked now.
- Do not ask "should I continue?" after completing a partial step.

## Interruption Recovery

- Treat model-capacity errors, transient host failures, and dropped sessions as execution interruptions, not as evidence the task should stop.
- Resume from durable state first: current files, `git status`, diffs, failing checks, task notes, and the latest validation signal matter more than chat memory.
- When resuming, first reconstruct what is already complete and what remains open before making new edits.
- Do not blindly rerun commands with side effects. Re-run only after verifying necessity or idempotence.
- Prefer a structured resume prompt over a bare "continue" when recovering from capacity errors or a fresh session.
- Use the standard prompts in [references/ralph-loop.md](references/ralph-loop.md) when the user asks for a safe Codex or CLI continuation after interruption.

## Stop Conditions

- Stop when the explicit done criteria are satisfied with evidence.
- Stop when a real blocker remains after reasonable local attempts to resolve it.
- Real blockers include destructive or irreversible actions needing consent, missing secrets or approvals, legal or safety concerns, and irrecoverable ambiguity with materially different outcomes.

## Communication

- Send short progress updates stating what is being done and what was learned.
- Report blockers only after trying reasonable local resolution paths.
- Keep the final handoff concise and outcome-focused.
- Include validation results, assumptions that mattered, and any residual risk.
