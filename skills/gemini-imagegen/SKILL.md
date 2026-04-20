---
name: gemini-imagegen
description: Generate or edit images with the Google Gemini API and Imagen models. Use when Codex needs to handle text-to-image generation, conversational image editing, multi-image grounding, background replacement, product shots, concept art, UI mockups, or model selection between Gemini native image models and Imagen 4 variants; run the bundled CLI (`scripts/gemini_image_gen.py`) and require `GEMINI_API_KEY` for live calls.
---

# Gemini Image Generation

Generate or edit images for the current project with Google's Gemini API. Default to `gemini-3.1-flash-image-preview` for most work, switch to `gemini-3-pro-image-preview` for higher fidelity and more complex instructions, and use `imagen-4.0-*` when the task is pure text-to-image and benefits from Imagen's specialized generator.

## When To Use

- Generate a new image for a website, app, game, document, or product concept.
- Edit an existing image with prompt-guided changes.
- Merge prompt text with one or more reference images.
- Choose which current Gemini / Imagen model should handle a generation request.
- Batch several image jobs through one local CLI run.

## Decision Tree

- If the user supplies one or more input images, use a native Gemini image model instead of Imagen.
- If the task needs multi-turn refinement, grounded search, or image search grounding, prefer `gemini-3.1-flash-image-preview`.
- If the task needs the highest Gemini-native fidelity, stronger text rendering, or 4K output, prefer `gemini-3-pro-image-preview`.
- If the task is simple and latency-sensitive, prefer `gemini-2.5-flash-image`.
- If the task is pure text-to-image and does not need input-image editing, consider `imagen-4.0-generate-001`, `imagen-4.0-fast-generate-001`, or `imagen-4.0-ultra-generate-001`.
- Do not route image-generation work to plain text-output Gemini models such as `gemini-2.5-flash` or `gemini-2.5-pro`.

Read [references/model-matrix.md](references/model-matrix.md) before choosing a model when accuracy matters.

## Workflow

1. Classify the request as generate, edit, or batch.
2. Pick the model family:
   - native Gemini image model via `generate_content`
   - Imagen via `generate_images`
3. Collect the full prompt, any exact text that must render verbatim, hard constraints, and any input images.
4. If the request is complex, rewrite the prompt into a short labeled spec instead of adding unrelated creative details.
5. Run [`scripts/gemini_image_gen.py`](scripts/gemini_image_gen.py) with explicit output paths.
6. Inspect the output and verify subject, composition, text rendering, invariants, and grounded references.
7. Iterate with one targeted prompt or constraint change at a time.

Use [references/cli.md](references/cli.md) for commands, [references/image-api.md](references/image-api.md) for API-level behavior, [references/prompting.md](references/prompting.md) for prompt structure, and [references/sample-prompts.md](references/sample-prompts.md) for copy-paste starting points.

## Temp And Output Conventions

- Use `tmp/gemini-imagegen/` for intermediate JSONL or scratch files and delete them when finished.
- Write final outputs under `output/gemini-imagegen/` when working in this repo.
- Keep filenames stable and descriptive with `--out` or `--out-dir`.

## Python Execution

Use `uv` for every Python operation in this skill.

For one-off CLI usage, prefer runtime dependency injection:

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py --help
```

Do not invoke `python`, `python3`, `pip`, or manual `venv` / `virtualenv` commands directly in this skill.

`Pillow` is optional for local inspection workflows; when needed, add it through `uv`, for example `uv run --with google-genai --with pillow python ...`.

## Environment

- `GEMINI_API_KEY` is required for live API calls.
- `GOOGLE_API_KEY` is accepted as a fallback when that is already how the local environment is configured.

If the key is missing:

1. Create an API key in Google AI Studio: <https://aistudio.google.com/apikey>
2. Export `GEMINI_API_KEY` in the local shell.
3. Re-run the CLI.

Never ask the user to paste the full key in chat.

## Defaults And Rules

- Default to `gemini-3.1-flash-image-preview`.
- If Python is needed, always run it through `uv` such as `uv run ...` or `uv run --with ...`.
- Use the Google Gen AI Python SDK (`google-genai`), not raw HTTP.
- For native Gemini image models, use `client.models.generate_content(...)`.
- For Imagen models, use `client.models.generate_images(...)`.
- If the request includes input images, do not use Imagen in this skill unless the official docs later add edit support and the references are updated.
- For complex iterative edits, keep the same Gemini image model through the iteration loop unless the user explicitly wants a quality or latency tradeoff.
- Prefer one dry-run first when wiring a new batch or unusual prompt.

## Prompt Augmentation

Make implicit production constraints explicit without inventing new creative requirements.

Template:

```text
Use case: <taxonomy slug>
Asset type: <where the asset will be used>
Primary request: <user prompt>
Scene/background: <environment>
Subject: <main subject>
Style/medium: <photo/illustration/3D/etc>
Composition/framing: <wide/close/top-down; placement>
Lighting/mood: <lighting + mood>
Color palette: <palette notes>
Text (verbatim): "<exact text>"
Constraints: <must keep / must avoid>
Avoid: <negative constraints>
```

Rules:

- Add only details the user already implied.
- Quote exact text that must render.
- For edits, repeat the invariants every iteration.
- For multi-image prompts, label each reference image by role.
- For Imagen, keep the prompt compact and use `--negative-prompt` when the user clearly asks for exclusions.

## Taxonomy

Generate:

- `photorealistic-natural`
- `product-mockup`
- `ui-mockup`
- `infographic-diagram`
- `logo-brand`
- `illustration-story`
- `stylized-concept`
- `historical-scene`

Edit:

- `text-localization`
- `identity-preserve`
- `precise-object-edit`
- `lighting-weather`
- `background-extraction`
- `style-transfer`
- `compositing`
- `sketch-to-render`

## Reference Map

- [references/model-matrix.md](references/model-matrix.md): current Gemini / Imagen image-capable model matrix and routing guidance
- [references/cli.md](references/cli.md): CLI flags, command examples, and batch format
- [references/image-api.md](references/image-api.md): API behavior by backend (`generate_content` vs `generate_images`)
- [references/prompting.md](references/prompting.md): prompt-structure and iteration rules
- [references/sample-prompts.md](references/sample-prompts.md): sample prompts for common asset types
