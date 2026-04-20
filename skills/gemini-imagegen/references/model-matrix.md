# Model Matrix

Use this file to decide which current Gemini API image-capable model to call. Re-check the linked official docs if Google changes model names or capabilities.

## Native Gemini Image Models

These models use `client.models.generate_content(...)` and can combine prompt text with image inputs.

- `gemini-3.1-flash-image-preview`
  - Default choice for most requests.
  - Best all-around Gemini-native image generation.
  - Supports grounded web search and grounded image search.
  - Good for generate, edit, and multi-turn refinement.
- `gemini-3-pro-image-preview`
  - Use when the request needs stronger prompt following, higher fidelity, better text rendering, or 4K output.
  - Better for dense instructions and premium outputs.
- `gemini-2.5-flash-image`
  - Use when latency matters more than top-end quality.
  - Good for quick ideation and simple instructions.

## Imagen Models

These models use `client.models.generate_images(...)` and are currently documented in the Gemini API as text-to-image generation models.

- `imagen-4.0-generate-001`
  - General-purpose Imagen 4 model.
  - Good default when the task is pure text-to-image.
- `imagen-4.0-fast-generate-001`
  - Faster and cheaper than the general model.
  - Good for ideation, exploration, and batch runs.
- `imagen-4.0-ultra-generate-001`
  - Highest prompt fidelity in the Imagen 4 family.
  - Use for premium single-image generation when latency and cost are secondary.

## Models To Avoid For Image Output

- Plain text-output Gemini models such as `gemini-2.5-flash`, `gemini-2.5-pro`, and similar non-image variants accept multimodal input but do not emit image output.
- When the task needs image bytes back, use an image-suffixed Gemini model or an Imagen model.

## Routing Rules

- If the user provides input images: use a native Gemini image model.
- If the user wants grounded generation with Google Search or image search: use `gemini-3.1-flash-image-preview`.
- If the user wants the strongest Gemini-native fidelity or 4K output: use `gemini-3-pro-image-preview`.
- If the user wants fastest Gemini-native generation: use `gemini-2.5-flash-image`.
- If the user wants pure text-to-image with Imagen-specific controls like negative prompts: use an `imagen-4.0-*` model.

## Official Sources

- Gemini image generation docs: <https://ai.google.dev/gemini-api/docs/image-generation>
- Imagen docs in Gemini API: <https://ai.google.dev/gemini-api/docs/imagen>
- Gemini API key docs: <https://ai.google.dev/gemini-api/docs/api-key>
