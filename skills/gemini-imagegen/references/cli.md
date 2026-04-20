# CLI

The bundled CLI is [`scripts/gemini_image_gen.py`](../scripts/gemini_image_gen.py).

## Python Runtime

Use `uv` for every Python command in this skill.

For ad hoc execution, inject the dependency at runtime:

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py --help
```

Do not call `python`, `python3`, `pip`, or manual `venv` commands directly.

## Environment

```bash
export GEMINI_API_KEY="your-key-here"
```

`GOOGLE_API_KEY` also works as a fallback.

## Generate With Default Gemini Model

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py generate \
  --prompt "A studio product photo of a matte black mechanical keyboard" \
  --use-case product-mockup \
  --asset-type "ecommerce hero" \
  --composition "three-quarter view, centered, generous negative space" \
  --out output/gemini-imagegen/keyboard.png
```

## Edit An Existing Image

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py edit \
  --model gemini-3.1-flash-image-preview \
  --input-image assets/product.png \
  --prompt "Replace the background with warm sunrise window light" \
  --constraints "change only the background; keep the product silhouette unchanged" \
  --out output/gemini-imagegen/product-edit.png
```

## Premium Gemini Output

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py generate \
  --model gemini-3-pro-image-preview \
  --prompt "A premium poster with crisp serif typography for a chamber music festival" \
  --allow-text \
  --text "AURELIA FESTIVAL" \
  --out output/gemini-imagegen/poster.png
```

## Imagen Text-To-Image

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py generate \
  --model imagen-4.0-generate-001 \
  --prompt "A ceramic coffee mug on travertine, editorial product photography" \
  --negative-prompt "text, logo, watermark, clutter" \
  --aspect-ratio 4:5 \
  --out output/gemini-imagegen/mug.png
```

## Grounded Search

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py generate \
  --model gemini-3.1-flash-image-preview \
  --prompt "Create a travel poster based on current reference imagery for Kyoto in spring" \
  --google-search \
  --image-search \
  --allow-text \
  --out output/gemini-imagegen/kyoto-poster.png
```

## Dry Run

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py generate \
  --prompt "A retro sci-fi paperback cover" \
  --dry-run
```

## Batch JSONL

Each line is one JSON object:

```json
{"prompt":"A charcoal sketch of a lighthouse","model":"gemini-2.5-flash-image","out":"output/gemini-imagegen/lighthouse.png"}
{"prompt":"Minimal sneaker product shot","model":"imagen-4.0-fast-generate-001","negative_prompt":"text, logo, watermark","out":"output/gemini-imagegen/sneaker.png"}
```

Run:

```bash
uv run --with google-genai python skills/gemini-imagegen/scripts/gemini_image_gen.py batch \
  --jobs tmp/gemini-imagegen/jobs.jsonl
```
