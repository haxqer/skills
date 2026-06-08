#!/usr/bin/env python3
"""
Game Asset Generator CLI — multi-provider image generation for game art.

Supports three request backends behind one interface:
  - openai            OpenAI-compatible Images API   (POST {base}/images/generations, /images/edits)
  - openai-responses  OpenAI-compatible Responses API (POST {base}/responses, image_generation tool)
  - gemini            Google Gemini / Imagen via the google-genai SDK

Everything is configurable so the same CLI works against the real OpenAI API,
a self-hosted gateway, or any OpenAI-compatible relay:
  --backend   openai | openai-responses | gemini | auto   (auto = infer from model/base-url)
  --base-url  custom endpoint, e.g. https://my-gateway.example.com/v1
  --model     custom model, e.g. gpt-image-2, gpt-image-1, dall-e-3, gemini-2.5-flash-image
  --api-key   explicit key (else read from env, see below)

Background handling for downstream cutout / Spine / paper-doll work:
  - OpenAI gpt-image-* return real alpha when --transparent (default for openai backends),
    so no chroma key is needed.
  - Gemini has no transparent mode, so generate on flat green (#00FF00) and chroma-key,
    or run scripts/smart_remove_bg.py afterward.

Env / config keys (first match wins):
  OpenAI key   : --api-key, OPENAI_API_KEY, IMAGE_API_KEY
  OpenAI base  : --base-url, OPENAI_BASE_URL, IMAGE_API_BASE_URL  (default https://api.openai.com/v1)
  Gemini key   : --api-key, GEMINI_API_KEY, GOOGLE_API_KEY, IMAGE_API_KEY
  Default model: --model, IMAGE_MODEL  (else per-backend default)

Usage:
  python scripts/generate_asset.py generate --prompt "..." --out out.png
  python scripts/generate_asset.py edit --image base.png --prompt "add steel armor" --out armored.png
  python scripts/generate_asset.py generate-batch --input jobs.jsonl --out-dir out/
  python scripts/generate_asset.py chroma-key --input raw.png --out clean.png --downscale 48
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-image"
DEFAULT_OPENAI_MODEL = "gpt-image-1"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_FUZZ = 30
GREEN = (0, 255, 0)
# Some gateways sit behind Cloudflare and reject the default urllib UA (error 1010).
USER_AGENT = "game-asset-gen/1.0 (+https://github.com/anthropics/claude-code)"
# Retry on transient upstream failures. Note: some gateways wrap an upstream
# rate-limit (rate_limit_exceeded) inside a 502, so 502 is treated as retryable.
RETRY_STATUS = {409, 429, 500, 502, 503, 504, 524, 529}
DEFAULT_MAX_RETRIES = 5
# Mutable at runtime via --max-retries (gateways with saturated shared keys may
# need a long retry budget before a slot frees up).
MAX_RETRIES = DEFAULT_MAX_RETRIES


# ---------------------------------------------------------------------------
# .env loader (minimal, no external dependency)
# ---------------------------------------------------------------------------

def load_dotenv(env_path: Path | None = None):
    """Load key=value pairs from a .env file into os.environ (no overwrite)."""
    if env_path is None:
        search_roots = [Path.cwd(), Path(__file__).resolve().parent]
        seen: set[Path] = set()
        for root in search_roots:
            search = root.resolve()
            while True:
                candidate = (search / ".env").resolve()
                if candidate not in seen:
                    seen.add(candidate)
                    if candidate.is_file():
                        env_path = candidate
                        break
                if search.parent == search:
                    break
                search = search.parent
            if env_path is not None:
                break
    if env_path is None or not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


def _die(message: str, code: int = 1):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Backend / config resolution
# ---------------------------------------------------------------------------

def resolve_backend(backend: str, model: str | None, base_url: str | None) -> str:
    """Map 'auto' to a concrete backend using the model name and base-url hints."""
    if backend and backend != "auto":
        return backend
    m = (model or "").lower()
    if m.startswith(("gemini", "imagen")):
        return "gemini"
    if m.startswith(("gpt-image", "dall-e", "dalle")):
        return "openai"
    # A custom base-url almost always means an OpenAI-compatible gateway.
    if base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("IMAGE_API_BASE_URL"):
        return "openai"
    return "gemini"


def default_model_for(backend: str) -> str:
    env_model = os.environ.get("IMAGE_MODEL")
    if env_model:
        return env_model
    return DEFAULT_GEMINI_MODEL if backend == "gemini" else DEFAULT_OPENAI_MODEL


def resolve_base_url(base_url: str | None) -> str:
    base = (
        base_url
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("IMAGE_API_BASE_URL")
        or DEFAULT_OPENAI_BASE
    )
    return base.rstrip("/")


def resolve_api_key(backend: str, api_key: str | None) -> str:
    if api_key:
        return api_key
    if backend == "gemini":
        key = (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("IMAGE_API_KEY")
        )
        if not key:
            _die("No Gemini key. Set GEMINI_API_KEY (or GOOGLE_API_KEY / IMAGE_API_KEY) or pass --api-key.")
    else:
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("IMAGE_API_KEY")
        if not key:
            _die("No OpenAI key. Set OPENAI_API_KEY (or IMAGE_API_KEY) or pass --api-key.")
    return key


# ---------------------------------------------------------------------------
# Image post-processing (chroma key + downscale)
# ---------------------------------------------------------------------------

def _apply_chroma_key(img, fuzz: int = DEFAULT_FUZZ):
    """Remove green (#00FF00) background pixels from a PIL RGBA image."""
    data = list(img.getdata())
    new_data = []
    removed = 0
    for r, g, b, a in data:
        if r < fuzz and g > (255 - fuzz) and b < fuzz:
            new_data.append((r, g, b, 0))
            removed += 1
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img, removed


def _postprocess_and_save(
    img,
    output_path: str,
    chroma_key: bool,
    fuzz: int,
    downscale: int | None,
    log_prefix: str = "  ",
):
    """Shared save path: optional chroma key, optional NN downscale, write PNG."""
    from PIL import Image as PILImage

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    if chroma_key:
        img, removed = _apply_chroma_key(img, fuzz=fuzz)
        total = img.width * img.height
        pct = removed * 100.0 / total if total else 0
        print(f"{log_prefix}Chroma-key: removed {removed} green pixels ({pct:.1f}%)")

    if downscale and downscale > 0:
        img = img.resize((downscale, downscale), PILImage.NEAREST)
        print(f"{log_prefix}Downscaled to {downscale}x{downscale}")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), "PNG")
    print(f"{log_prefix}Saved: {out}")


def _bytes_to_image(raw: bytes):
    from PIL import Image as PILImage

    return PILImage.open(io.BytesIO(raw)).convert("RGBA")


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

def ensure_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        _die("'Pillow' not found. Install with: pip install Pillow  (or use `uv run --with Pillow ...`)")


def ensure_gemini():
    try:
        from google import genai  # noqa: F401
    except ImportError:
        _die("'google-genai' not found. Install with: pip install google-genai  (or `uv run --with google-genai ...`)")


# ---------------------------------------------------------------------------
# OpenAI Images API backend (HTTP, no SDK dependency)
# ---------------------------------------------------------------------------

def _is_retryable_body(detail: str) -> bool:
    """Some gateways return 200/4xx envelopes whose body signals a rate limit."""
    low = detail.lower()
    return "rate_limit" in low or "rate limit" in low or "try again" in low


def _send_with_retry(req: urllib.request.Request, url: str, max_retries: int | None = None) -> dict:
    """POST with exponential backoff on transient upstream failures (incl. 502-wrapped rate limits)."""
    import time

    if max_retries is None:
        max_retries = MAX_RETRIES
    last_err = ""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            last_err = f"HTTP {e.code} from {url}: {detail[:500]}"
            retryable = e.code in RETRY_STATUS or _is_retryable_body(detail)
            if not retryable or attempt == max_retries - 1:
                _die(last_err)
        except urllib.error.URLError as e:
            last_err = f"Request to {url} failed: {e.reason}"
            if attempt == max_retries - 1:
                _die(last_err)
        backoff = min(2 ** attempt, 16)
        print(f"  Transient failure (attempt {attempt + 1}/{max_retries}); retrying in {backoff}s...", file=sys.stderr)
        time.sleep(backoff)
    _die(last_err)
    return {}


def _http_post_json(url: str, api_key: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    return _send_with_retry(req, url)


def _http_post_multipart(url: str, api_key: str, fields: dict, files: list[tuple[str, Path]]) -> dict:
    boundary = f"----gameasset{uuid.uuid4().hex}"
    parts: list[bytes] = []

    for name, value in fields.items():
        if value is None:
            continue
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    for name, path in files:
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {mime}\r\n\r\n".encode())
        parts.append(path.read_bytes())
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    return _send_with_retry(req, url)


def _extract_b64_images(obj) -> list[bytes]:
    """Walk an arbitrary OpenAI-style response and collect all b64 image payloads.

    Handles Images API ({"data":[{"b64_json":...}]}) and Responses API
    (output items of type image_generation_call with a 'result' field)."""
    found: list[bytes] = []

    def visit(node):
        if isinstance(node, dict):
            for key in ("b64_json", "result"):
                val = node.get(key)
                if isinstance(val, str) and len(val) > 100:
                    try:
                        found.append(base64.b64decode(val))
                    except Exception:
                        pass
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    visit(obj)
    return found


def _fetch_url_images(obj) -> list[bytes]:
    """Fallback for backends that return image URLs instead of b64."""
    urls: list[str] = []

    def visit(node):
        if isinstance(node, dict):
            u = node.get("url")
            if isinstance(u, str) and u.startswith("http"):
                urls.append(u)
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    visit(obj)
    out: list[bytes] = []
    for u in urls:
        try:
            dl = urllib.request.Request(u, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(dl, timeout=120) as r:
                out.append(r.read())
        except Exception as e:
            print(f"  WARNING: failed to download {u}: {e}", file=sys.stderr)
    return out


def openai_generate(
    prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    size: str,
    background: str | None,
    n: int = 1,
) -> list[bytes]:
    payload: dict = {"model": model, "prompt": prompt, "n": n}
    if size and size != "auto":
        payload["size"] = size
    # gpt-image-* support transparent background + output_format; dall-e does not.
    if model.lower().startswith("gpt-image"):
        if background:
            payload["background"] = background
        payload["output_format"] = "png"
    elif background == "transparent":
        # dall-e cannot do transparency; request b64 and rely on later cutout.
        payload["response_format"] = "b64_json"
    resp = _http_post_json(f"{base_url}/images/generations", api_key, payload)
    images = _extract_b64_images(resp) or _fetch_url_images(resp)
    if not images:
        _die(f"No image in response: {json.dumps(resp)[:400]}")
    return images


def openai_edit(
    prompt: str,
    image_paths: list[Path],
    mask_path: Path | None,
    base_url: str,
    api_key: str,
    model: str,
    size: str,
    background: str | None,
    n: int = 1,
) -> list[bytes]:
    fields: dict = {"model": model, "prompt": prompt, "n": str(n)}
    if size and size != "auto":
        fields["size"] = size
    if model.lower().startswith("gpt-image"):
        if background:
            fields["background"] = background
        fields["output_format"] = "png"
    files: list[tuple[str, Path]] = []
    # gpt-image-1 accepts multiple input images via image[]; dall-e accepts one image.
    field_name = "image[]" if model.lower().startswith("gpt-image") else "image"
    for p in image_paths:
        files.append((field_name, p))
    if mask_path:
        files.append(("mask", mask_path))
    resp = _http_post_multipart(f"{base_url}/images/edits", api_key, fields, files)
    images = _extract_b64_images(resp) or _fetch_url_images(resp)
    if not images:
        _die(f"No image in edit response: {json.dumps(resp)[:400]}")
    return images


def openai_responses_generate(
    prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    size: str,
    background: str | None,
    input_images: list[Path] | None = None,
) -> list[bytes]:
    """OpenAI Responses API with the image_generation tool (POST {base}/responses)."""
    tool: dict = {"type": "image_generation"}
    if size and size != "auto":
        tool["size"] = size
    if background:
        tool["background"] = background

    if input_images:
        content: list[dict] = [{"type": "input_text", "text": prompt}]
        for p in input_images:
            mime = mimetypes.guess_type(p.name)[0] or "image/png"
            b64 = base64.b64encode(p.read_bytes()).decode()
            content.append({"type": "input_image", "image_url": f"data:{mime};base64,{b64}"})
        payload: dict = {"model": model, "input": [{"role": "user", "content": content}], "tools": [tool]}
    else:
        payload = {"model": model, "input": prompt, "tools": [tool]}

    resp = _http_post_json(f"{base_url}/responses", api_key, payload)
    images = _extract_b64_images(resp) or _fetch_url_images(resp)
    if not images:
        _die(f"No image in responses output: {json.dumps(resp)[:400]}")
    return images


# ---------------------------------------------------------------------------
# Gemini backend (google-genai SDK)
# ---------------------------------------------------------------------------

def gemini_generate(
    prompt: str,
    api_key: str,
    model: str,
    aspect_ratio: str,
    input_images: list[Path] | None = None,
) -> list[bytes]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    contents: list = [prompt]
    for p in (input_images or []):
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["Image"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )

    images: list[bytes] = []
    for part in response.parts:
        if getattr(part, "inline_data", None) is not None:
            images.append(part.inline_data.data)
        elif getattr(part, "text", None):
            print(f"  Model text: {part.text}")
    if not images:
        _die("Gemini returned no image (the model may have declined the prompt).")
    return images


# ---------------------------------------------------------------------------
# Unified single-image entry point
# ---------------------------------------------------------------------------

def run_generate(args, prompt: str, out_path: str, input_images: list[Path] | None = None):
    backend = resolve_backend(args.backend, args.model, args.base_url)
    model = args.model or default_model_for(backend)
    chroma = _should_chroma_key(args, backend)

    if args.dry_run:
        print(f"[DRY RUN] backend={backend} model={model} chroma_key={'ON' if chroma else 'OFF'}")
        print(f"[DRY RUN] out={out_path}")
        print(f"[DRY RUN] prompt: {prompt[:200]}")
        if input_images:
            print(f"[DRY RUN] input_images: {[str(p) for p in input_images]}")
        return

    ensure_pillow()
    api_key = resolve_api_key(backend, args.api_key)
    background = _resolve_background(args, backend)

    print(f"Generating with backend={backend}, model={model}...")
    print(f"  Prompt: {prompt[:120]}...")

    if backend == "gemini":
        ensure_gemini()
        raw_list = gemini_generate(prompt, api_key, model, args.aspect_ratio, input_images)
    elif backend == "openai-responses":
        base = resolve_base_url(args.base_url)
        raw_list = openai_responses_generate(prompt, base, api_key, model, args.size, background, input_images)
    else:  # openai
        base = resolve_base_url(args.base_url)
        if input_images:
            raw_list = openai_edit(prompt, input_images, None, base, api_key, model, args.size, background)
        else:
            raw_list = openai_generate(prompt, base, api_key, model, args.size, background)

    _save_results(raw_list, out_path, chroma, args.fuzz, args.downscale)


def _save_results(raw_list, out_path, chroma, fuzz, downscale):
    if len(raw_list) == 1:
        _postprocess_and_save(_bytes_to_image(raw_list[0]), out_path, chroma, fuzz, downscale)
    else:
        stem = Path(out_path)
        for i, raw in enumerate(raw_list):
            numbered = stem.with_name(f"{stem.stem}_{i:02d}{stem.suffix}")
            _postprocess_and_save(_bytes_to_image(raw), str(numbered), chroma, fuzz, downscale)


def _should_chroma_key(args, backend: str) -> bool:
    if args.chroma_key == "on":
        return True
    if args.chroma_key == "off":
        return False
    # auto: only Gemini (no transparent mode) needs green keying by default.
    return backend == "gemini"


def _resolve_background(args, backend: str) -> str | None:
    if backend == "gemini":
        return None  # Gemini has no transparent control.
    if args.background:
        return args.background
    return "transparent" if args.transparent else "opaque"


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_generate(args):
    run_generate(args, args.prompt, args.out)


def cmd_edit(args):
    images = [Path(p) for p in args.image]
    for p in images:
        if not p.is_file():
            _die(f"Input image not found: {p}")
    backend = resolve_backend(args.backend, args.model, args.base_url)
    model = args.model or default_model_for(backend)
    chroma = _should_chroma_key(args, backend)

    if args.dry_run:
        print(f"[DRY RUN] EDIT backend={backend} model={model}")
        print(f"[DRY RUN] images={[str(p) for p in images]} mask={args.mask}")
        print(f"[DRY RUN] prompt: {args.prompt[:200]}")
        return

    ensure_pillow()
    api_key = resolve_api_key(backend, args.api_key)
    background = _resolve_background(args, backend)

    if backend == "gemini":
        ensure_gemini()
        raw_list = gemini_generate(args.prompt, api_key, model, args.aspect_ratio, images)
    elif backend == "openai-responses":
        base = resolve_base_url(args.base_url)
        raw_list = openai_responses_generate(args.prompt, base, api_key, model, args.size, background, images)
    else:
        base = resolve_base_url(args.base_url)
        mask = Path(args.mask) if args.mask else None
        if mask and not mask.is_file():
            _die(f"Mask not found: {mask}")
        raw_list = openai_edit(args.prompt, images, mask, base, api_key, model, args.size, background)

    _save_results(raw_list, args.out, chroma, args.fuzz, args.downscale)


def cmd_generate_batch(args):
    jobs = []
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))

    print(f"Loaded {len(jobs)} jobs from {args.input}")

    if args.dry_run:
        for i, job in enumerate(jobs):
            out_name = job.get("out_name", f"output_{i:03d}.png")
            print(f"  [DRY RUN] [{i}] {out_name}: {job['prompt'][:80]}...")
        return

    ensure_pillow()
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _gen(idx_job):
        idx, job = idx_job
        prompt = job["prompt"]
        model = job.get("model", args.model)
        backend = resolve_backend(job.get("backend", args.backend), model, args.base_url)
        model = model or default_model_for(backend)
        out_name = job.get("out_name", f"output_{idx:03d}.png")
        out_path = Path(args.out_dir) / out_name
        downscale = job.get("downscale", args.downscale)
        fuzz = job.get("fuzz", args.fuzz)
        aspect = job.get("aspect_ratio", args.aspect_ratio)
        size = job.get("size", args.size)
        input_images = [Path(p) for p in job.get("input_images", [])]

        # Per-job chroma override; else auto by backend.
        if "chroma_key" in job:
            chroma = bool(job["chroma_key"])
        else:
            chroma = _should_chroma_key(args, backend)

        try:
            api_key = resolve_api_key(backend, args.api_key)
            if backend == "gemini":
                ensure_gemini()
                raw_list = gemini_generate(prompt, api_key, model, aspect, input_images or None)
            elif backend == "openai-responses":
                base = resolve_base_url(args.base_url)
                bg = job.get("background", "transparent" if args.transparent else "opaque")
                raw_list = openai_responses_generate(prompt, base, api_key, model, size, bg, input_images or None)
            else:
                base = resolve_base_url(args.base_url)
                bg = job.get("background", "transparent" if args.transparent else "opaque")
                if input_images:
                    raw_list = openai_edit(prompt, input_images, None, base, api_key, model, size, bg)
                else:
                    raw_list = openai_generate(prompt, base, api_key, model, size, bg)

            _save_results(raw_list, str(out_path), chroma, fuzz, downscale)
            print(f"  [{idx}] OK {out_path}")
            return True
        except SystemExit as e:
            print(f"  [{idx}] FAILED: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"  [{idx}] ERROR: {e}", file=sys.stderr)
            return False

    success = failed = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(_gen, (i, job)): i for i, job in enumerate(jobs)}
        for future in as_completed(futures):
            if future.result():
                success += 1
            else:
                failed += 1

    print(f"\nBatch complete: {success} succeeded, {failed} failed of {len(jobs)} total")


def cmd_chroma_key(args):
    ensure_pillow()
    from PIL import Image as PILImage

    out = args.out
    if out is None:
        p = Path(args.input)
        out = str(p.parent / f"{p.stem}_keyed{p.suffix}")
    img = PILImage.open(args.input).convert("RGBA")
    _postprocess_and_save(img, out, True, args.fuzz, args.downscale)


def cmd_chroma_key_dir(args):
    ensure_pillow()
    from PIL import Image as PILImage

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir) if args.output_dir else in_dir / "keyed"
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted(in_dir.glob("*.png"))
    print(f"Processing {len(pngs)} PNGs from {in_dir}...")
    for png in pngs:
        img = PILImage.open(str(png)).convert("RGBA")
        _postprocess_and_save(img, str(out_dir / png.name), True, args.fuzz, args.downscale)
    print(f"Done. Output in {out_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_backend_args(p, with_aspect=True):
    p.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "openai", "openai-responses", "gemini"],
        help="Request backend. auto = infer from model/base-url (default: auto).",
    )
    p.add_argument("--base-url", default=None, help="Custom OpenAI-compatible base URL, e.g. https://gw/v1")
    p.add_argument("--model", default=None, help="Model name, e.g. gpt-image-2, gpt-image-1, gemini-2.5-flash-image")
    p.add_argument("--api-key", default=None, help="Explicit API key (else read from env)")
    p.add_argument("--size", default="1024x1024", help="OpenAI image size, e.g. 1024x1024 or 'auto' (default: 1024x1024)")
    if with_aspect:
        p.add_argument("--aspect-ratio", default="1:1", help="Gemini aspect ratio (default: 1:1)")
    p.add_argument(
        "--background",
        default=None,
        choices=["transparent", "opaque", "auto"],
        help="OpenAI gpt-image background mode (overrides --transparent).",
    )
    p.add_argument("--transparent", action="store_true", default=True, help="Request transparent bg on OpenAI (default ON)")
    p.add_argument("--no-transparent", action="store_false", dest="transparent", help="Disable transparent request")
    p.add_argument(
        "--chroma-key",
        default="auto",
        choices=["auto", "on", "off"],
        help="Green-screen removal. auto = on for Gemini, off for OpenAI (default: auto).",
    )
    p.add_argument("--fuzz", type=int, default=DEFAULT_FUZZ, help=f"Chroma-key tolerance (default: {DEFAULT_FUZZ})")
    p.add_argument("--downscale", type=int, default=None, help="Downscale to NxN nearest-neighbor (pixel art)")
    p.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"HTTP retries on transient/rate-limit failures (default: {DEFAULT_MAX_RETRIES}). "
        "Raise this for gateways with saturated shared keys.",
    )
    p.add_argument("--dry-run", action="store_true", help="Print the request without calling any API")


def main():
    parser = argparse.ArgumentParser(
        description="Game Asset Generator — multi-provider (OpenAI / Gemini) image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # OpenAI gpt-image-2, transparent PNG, no chroma key needed
  python generate_asset.py generate --backend openai --model gpt-image-2 \\
    --prompt "front-facing hero base body, T-pose, transparent background" \\
    --out art/hero/base.png

  # Custom OpenAI-compatible gateway
  python generate_asset.py generate --base-url https://my-gw/v1 --model gpt-image-2 \\
    --prompt "..." --out out.png

  # OpenAI Responses API (image_generation tool)
  python generate_asset.py generate --backend openai-responses --model gpt-5 \\
    --prompt "..." --out out.png

  # Gemini pixel-art sprite on green, auto chroma-keyed + downscaled
  python generate_asset.py generate --backend gemini \\
    --prompt "chibi pixel warrior, 48x48, solid #00FF00 background" \\
    --out art/player/idle_00.png --downscale 48

  # Paper-doll: edit a base body to add an equipment layer (keeps pose/anchor)
  python generate_asset.py edit --backend openai --model gpt-image-2 \\
    --image art/hero/base.png --prompt "same character wearing steel plate armor" \\
    --out art/hero/armor_steel.png
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="Generate a single image from a prompt")
    g.add_argument("--prompt", required=True)
    g.add_argument("--out", default="output.png")
    _add_backend_args(g)
    g.set_defaults(func=cmd_generate)

    e = sub.add_parser("edit", help="Edit/extend image(s) with a prompt (paper-doll, consistency)")
    e.add_argument("--prompt", required=True)
    e.add_argument("--image", required=True, action="append", help="Input image (repeat for multiple)")
    e.add_argument("--mask", default=None, help="Optional mask PNG (OpenAI edits): transparent = area to change")
    e.add_argument("--out", default="output.png")
    _add_backend_args(e)
    e.set_defaults(func=cmd_edit)

    b = sub.add_parser("generate-batch", help="Batch generate from a JSONL file")
    b.add_argument("--input", required=True, help="JSONL with one job per line")
    b.add_argument("--out-dir", default="output")
    b.add_argument("--concurrency", type=int, default=3)
    _add_backend_args(b)
    b.set_defaults(func=cmd_generate_batch)

    ck = sub.add_parser("chroma-key", help="Remove green background from one image")
    ck.add_argument("--input", required=True)
    ck.add_argument("--out", default=None)
    ck.add_argument("--fuzz", type=int, default=DEFAULT_FUZZ)
    ck.add_argument("--downscale", type=int, default=None)
    ck.set_defaults(func=cmd_chroma_key)

    ckd = sub.add_parser("chroma-key-dir", help="Remove green background from a directory of PNGs")
    ckd.add_argument("--input-dir", required=True)
    ckd.add_argument("--output-dir", default=None)
    ckd.add_argument("--fuzz", type=int, default=DEFAULT_FUZZ)
    ckd.add_argument("--downscale", type=int, default=None)
    ckd.set_defaults(func=cmd_chroma_key_dir)

    args = parser.parse_args()
    load_dotenv()
    global MAX_RETRIES
    if getattr(args, "max_retries", None):
        MAX_RETRIES = args.max_retries
    args.func(args)


if __name__ == "__main__":
    main()
