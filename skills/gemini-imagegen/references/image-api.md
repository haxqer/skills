# Image API Notes

This skill uses two different Gemini API surfaces.

## Native Gemini Image Models

Use `client.models.generate_content(...)` with an image-capable Gemini model such as `gemini-3.1-flash-image-preview`.

Typical config surface:

- `response_modalities=["IMAGE"]` for image-only output
- `response_modalities=["TEXT","IMAGE"]` when explanatory text is also useful
- `image_config.aspect_ratio`
- `image_config.image_size`
- `image_config.output_mime_type`
- `image_config.output_compression_quality`
- `image_config.person_generation`
- `tools=[Tool(google_search=...)]` for grounded web or image search

For edits, pass the prompt plus one or more input-image parts:

```python
types.Part.from_bytes(data=path.read_bytes(), mime_type="image/png")
```

The bundled CLI uses this path whenever the selected model name contains `image` and does not start with `imagen-`.

## Imagen Models

Use `client.models.generate_images(...)` with an Imagen model such as `imagen-4.0-generate-001`.

Typical config surface:

- `number_of_images`
- `aspect_ratio`
- `negative_prompt`
- `image_size`
- `output_mime_type`
- `output_compression_quality`
- `person_generation`
- `guidance_scale`
- `seed`
- `enhance_prompt`

The bundled CLI routes any `imagen-*` model here.

## Current Skill Limits

- Imagen is treated as text-to-image only in this skill.
- Input-image edits are routed only to native Gemini image models.
- `--image-search` is restricted to `gemini-3.1-flash-image-preview`, matching the current official docs.

## Official Sources

- <https://ai.google.dev/gemini-api/docs/image-generation>
- <https://ai.google.dev/gemini-api/docs/imagen>
