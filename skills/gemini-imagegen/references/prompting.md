# Prompting

## Base Structure

Use this order:

1. Asset purpose
2. Subject
3. Scene or background
4. Composition
5. Style or medium
6. Lighting or mood
7. Exact text, if any
8. Constraints
9. Avoid list

## Gemini-Native Image Models

- Use short labeled specs when the request has multiple constraints.
- For edits, state the invariants explicitly: `change only X; keep Y unchanged`.
- For multi-image edits, label each reference image by role in the prompt.
- When using grounded search, explain what external references should influence the result.

## Imagen

- Keep the main prompt direct and concrete.
- Use `--negative-prompt` for strong exclusions instead of overloading the main prompt.
- Use Imagen when the job is text-to-image and does not need prompt-plus-image editing.

## Text Rendering

- Quote exact text in the prompt.
- Tell the model where the text should appear.
- For dense typography or poster layouts, prefer `gemini-3-pro-image-preview` or `imagen-4.0-ultra-generate-001`.

## Iteration

- Change one thing at a time.
- If the result drifts, restate the unchanged parts.
- If the model adds unwanted clutter, sharpen the `Avoid:` line rather than rewriting the entire prompt.
