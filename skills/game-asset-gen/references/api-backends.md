# API Backends — Provider, URL, Model, and Key Configuration

The generator (`scripts/generate_asset.py`) speaks three request formats behind
one CLI. This reference covers how to point it at any provider or gateway.

## Backends

| `--backend`        | Endpoint(s)                                              | Typical models                          | SDK needed     |
|--------------------|----------------------------------------------------------|-----------------------------------------|----------------|
| `openai`           | `POST {base}/images/generations`, `POST {base}/images/edits` | `gpt-image-2`, `gpt-image-1`, `dall-e-3` | none (stdlib HTTP) |
| `openai-responses` | `POST {base}/responses` (`image_generation` tool)        | `gpt-5`, any model with the image tool  | none (stdlib HTTP) |
| `gemini`           | `google-genai` SDK                                       | `gemini-2.5-flash-image`, Imagen        | `google-genai` |
| `auto` (default)   | inferred from `--model` / `--base-url` (see below)       | —                                       | —              |

Only `Pillow` is required for OpenAI backends; Gemini also needs `google-genai`.

### Auto-resolution rules

`auto` chooses a concrete backend as follows:

1. model starts with `gpt-image` / `dall-e` / `dalle` → `openai`
2. model starts with `gemini` / `imagen` → `gemini`
3. a `--base-url` (or `OPENAI_BASE_URL` / `IMAGE_API_BASE_URL`) is set → `openai`
4. otherwise → `gemini`

Set `--backend` explicitly when using a custom OpenAI-compatible model name that
does not match these prefixes.

## Custom URL

Any OpenAI-compatible gateway, relay, or self-hosted endpoint works. Pass a base
URL that already includes the API version segment (usually `/v1`):

```bash
python generate_asset.py generate \
  --base-url https://my-gateway.example.com/v1 \
  --model gpt-image-2 --prompt "..." --out out.png
```

The script appends `/images/generations`, `/images/edits`, or `/responses` to the
base URL. Trailing slashes are trimmed automatically.

Precedence for the base URL: `--base-url` > `OPENAI_BASE_URL` >
`IMAGE_API_BASE_URL` > `https://api.openai.com/v1`.

## Custom Model

```bash
--model gpt-image-2          # OpenAI images
--model gpt-image-1
--model dall-e-3
--model gemini-2.5-flash-image
--model my-org/custom-image  # any gateway-specific id (set --backend explicitly)
```

Precedence: `--model` > `IMAGE_MODEL` > per-backend default (`gpt-image-1` for
OpenAI, `gemini-2.5-flash-image` for Gemini).

## API Keys (env, first match wins)

| Backend | `--api-key` then env order                                  |
|---------|-------------------------------------------------------------|
| OpenAI  | `OPENAI_API_KEY`, `IMAGE_API_KEY`                           |
| Gemini  | `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `IMAGE_API_KEY`         |

`IMAGE_API_KEY` is a generic fallback for either backend, handy when a single
gateway key serves multiple model families. The CLI also auto-loads a `.env` by
walking up from the working directory, then from the script location; explicit
environment variables take precedence over `.env`.

Example `.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://my-gateway.example.com/v1
IMAGE_MODEL=gpt-image-2
# GEMINI_API_KEY=...
```

## Transparency vs Chroma Key

Transparency is what makes assets usable for cutout, Spine, and paper-doll.

- **OpenAI `gpt-image-*` (direct API)**: send `--transparent` (default for
  OpenAI backends). The script sets `background=transparent` and
  `output_format=png`, returned PNG carries real alpha. **No chroma key needed.**
- **OpenAI-compatible gateways / relays**: many relays (e.g. Codex relay) do
  **not** forward `background=transparent` to the upstream and will return HTTP 400
  (`Transparent background is not supported for this model`). Use `--no-transparent`
  and generate on a solid white background (`"... solid pure white background, no shadow ..."`
  in the prompt), then cut out with `scripts/smart_remove_bg.py`.
  `smart_remove_bg.py` auto-detects the corner color so white/off-white backgrounds
  are removed just as cleanly as green ones. This path is verified working:
  ```bash
  python generate_asset.py generate \
    --backend openai --base-url https://your-relay/v1 --model gpt-image-2 \
    --no-transparent \
    --prompt "cute green slime, chibi RPG, solid pure white background, no shadow" \
    --out raw/slime.png --size 1024x1024
  python smart_remove_bg.py --input-dir raw/ --output-dir art/ --fuzz 80 --downscale 48
  ```
- **`dall-e-3`**: cannot produce transparency. Use the white-background + cutout
  path above.
- **Gemini**: has no transparent mode. Generate on flat `#00FF00` (state it in
  the prompt), then chroma-key. `--chroma-key auto` turns keying on for Gemini
  and off for OpenAI; override with `on` / `off`.

## Output Sizing

- OpenAI: `--size 1024x1024` (also `1024x1536`, `1536x1024`, or `auto`). gpt-image
  supports transparency only at its supported sizes.
- Gemini: `--aspect-ratio 1:1` (also `16:9`, `9:16`, etc.).
- Pixel art: generate large, then `--downscale 48` (nearest-neighbor) after
  cutout for crisp pixels.

## Editing & Masking (paper-doll, consistency)

The `edit` subcommand drives image-to-image:

```bash
python generate_asset.py edit \
  --backend openai --model gpt-image-2 \
  --image base.png --image overlay.png \      # multiple inputs (gpt-image)
  --mask region.png \                         # transparent area = what to change
  --prompt "same character, add a red cape" --out caped.png
```

- OpenAI `images/edits`: `image[]` accepts multiple inputs; `mask` is optional.
- OpenAI Responses: input images are sent as `input_image` content parts.
- Gemini: input images are passed as `Part.from_bytes` alongside the prompt.

See `pipeline-spine-paperdoll.md` for how to use edits to keep layers registered.

## Troubleshooting

- **401 / auth error** — wrong or missing key for the resolved backend. Confirm
  which env var is read (table above) and that `--base-url` matches the key.
- **404 on `/responses`** — the gateway doesn't expose the Responses API; use
  `--backend openai` (Images API) instead.
- **HTTP 400 "Transparent background is not supported"** — the relay does not
  forward the `background` param. Add `--no-transparent` and use a white-background
  prompt + `smart_remove_bg.py` for cutout (see Transparency section above).
- **HTTP 502 with body `rate_limit_exceeded` / "Rate limit reached"** — a shared
  relay org key hit its per-minute image limit. The script retries automatically
  with exponential backoff; raise `--max-retries` (e.g. `--max-retries 40`) to
  wait longer. Avoid extra probe calls during saturation — they burn quota.
- **No transparency in OpenAI output** — model is `dall-e-*` (no alpha) or the
  gateway dropped `background`; use white-background + `smart_remove_bg.py`.
- **"No image in response"** — the printed JSON snippet shows the gateway's error
  or an unexpected shape. The extractor looks for `b64_json`/`result` fields and
  falls back to downloading `url` fields.
- **Gemini import error** — install `google-genai` (`uv run --with google-genai ...`).
- **`auto` picked the wrong backend** — pass `--backend` explicitly; custom model
  names that don't match known prefixes default by base-url presence.
