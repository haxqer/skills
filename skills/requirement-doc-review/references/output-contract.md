# Output Contract

## File Naming

Use the source basename and write Markdown files in the same directory as the
source unless the user requests another location.

- Source: `xxx.docx` -> `xxx_formated.md`
- Source: `xxx.md` -> `xxx_formated.md`
- Source: `xxx.txt` -> `xxx_formated.md`
- PM review: `xxx_pm_review.md`
- Architect review: `xxx_architect_review.md`
- Engineering review: `xxx_engineering_review.md`

Preserve the exact suffix `_formated` because that is the requested contract.
Do not silently replace it with `_formatted`.

If the user provides pasted text without a source filename, default the base
name to `requirement_doc` in the current working directory unless a better
target path is already implied.

## Deliverable Set

Create exactly four files by default:

1. formatted document
2. PM review
3. architect review
4. engineering review

Create extra files only when the user explicitly asks for them.

## Formatted Document Rules

- Reorganize for readability only.
- Preserve the original meaning, scope, and uncertainty.
- Keep original facts, examples, IDs, numbers, URLs, and literal rules.
- Normalize obvious structural issues:
  - heading levels
  - list nesting
  - inconsistent numbering
  - broken tables that can be safely reconstructed
  - duplicated headings caused by poor formatting
- Avoid adding invented sections just to make the document look complete.
- Add a short `Open Questions` section only when the source already implies
  missing information that must be called out to preserve meaning.

## Review Document Structure

Use this structure for every review file:

1. `Overview`
- Summarize the document goal, current maturity, and main review scope.

2. `Key Findings`
- List the highest-signal issues first.
- Use severity labels such as `High`, `Medium`, and `Low`.
- For each finding, include:
  - `Problem`
  - `Impact`
  - `Recommendation`

3. `Suggested Revisions`
- Propose the concrete document or product changes needed to resolve the gaps.

4. `Blocking Questions`
- List missing decisions, undefined rules, or dependency clarifications.
- Keep this section even when empty only if the document is clearly immature.

## Writing Style

- Keep the source language unless the user requests another language.
- Prefer concise, reviewer-style prose over tutorial-style explanations.
- Write statements that a delivery team can act on directly.
- Separate confirmed facts from inference with explicit labels when needed.
