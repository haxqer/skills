---
name: "requirement-doc-review"
description: "Format and review requirement documents, PRDs, meeting notes, or draft specs into a standard Markdown deliverable pack. Use when Codex needs to整理需求文档、仅整理原文格式并生成 `_formated.md` 文件，然后分别从产品经理、架构师、前后端研发视角识别业务、逻辑、交互、数据与实现问题，输出新的评审文档。"
---

# Requirement Doc Review

## Overview

Turn rough requirement material into a stable Markdown pack.
Keep the formatted file faithful to the source, then write separate review
documents for product, architecture, and engineering.

## Workflow

1. Stabilize the source.
- Accept a file path, pasted text, or a small set of related requirement files.
- Preserve the source language by default. Translate only when the user asks.
- Process each source document independently unless the user explicitly asks
  for a merged pack.

2. Create the formatted document.
- Read `references/output-contract.md` before creating files.
- Reformat only: headings, lists, numbering, tables, grouping, whitespace, and
  terminology consistency.
- Do not add new requirements, do not fix ambiguous business intent silently,
  and do not turn guesses into facts.
- Preserve unclear or incomplete material and make it easier to scan without
  changing meaning.

3. Write the PM review.
- Read `references/review-checklists.md` and use the `PM` checklist.
- Focus on business goal, user value, scope boundary, roles, flows, rules,
  exceptions, acceptance, metrics, release scope, and dependency clarity.
- Surface interaction issues only from the product behavior perspective.
- Turn gaps into concrete product decisions, recommendations, or blocking
  questions.

4. Write the architect review.
- Use the `Architect` checklist.
- Focus on domain model, service boundary, data flow, state transitions,
  consistency, performance, security, observability, extensibility, and
  integration contracts.
- Convert vague statements into explicit architecture options, risks, and
  tradeoffs.
- Mark every assumption clearly.

5. Write the frontend/backend review.
- Use the `Engineering` checklist.
- Keep one engineering document by default with separate `Frontend` and
  `Backend` sections.
- For frontend, inspect screens, interaction states, validation, async flows,
  permission handling, error feedback, accessibility, and analytics hooks.
- For backend, inspect APIs, schemas, idempotency, transactions, async jobs,
  permission rules, failure handling, configuration, and testability.
- Split frontend and backend into separate files only when the user explicitly
  asks.

6. Close the pack.
- Create exactly four files for the default flow.
- Keep facts, inference, and proposed solutions clearly separated.
- List unresolved questions in a dedicated section instead of hiding them in
  general commentary.
- If the source is incomplete, still write the review docs and include
  `Blocking Questions`.

## Output Contract

Create files in this order for one source document:

1. formatted document
2. PM review
3. architect review
4. engineering review

Follow the exact naming and section rules in `references/output-contract.md`.

## Quality Bar

- Preserve source meaning in the formatted document.
- Keep PM, architect, and engineering concerns separate.
- State contradictions explicitly instead of normalizing them away.
- Prefer concrete findings with impact and recommendation over generic advice.
- Keep recommendations implementable and scoped.
- Distinguish confirmed source facts from inference or proposed changes.
- Avoid mixing frontend and backend concerns without labeling ownership.

## Trigger Examples

- "整理这个需求文档，补成规范 Markdown，再从产品、架构、研发角度给我评审。"
- "Review this rough PRD and write separate PM, architect, and FE/BE review
  files."
- "把会议纪要整理成需求文档，并按角色拆出问题和方案。"

## References

- Read `references/output-contract.md` before naming files or writing the
  deliverables.
- Read `references/review-checklists.md` before drafting the role-based review
  documents.
