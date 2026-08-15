#!/usr/bin/env python3
"""
split_character.py — Turn one full character image into separated body-part PNGs.

Two stages:
  1. Generation — send the reference image to an image model with a "deconstruct
     into separated parts on a clean background" instruction, producing a flat
     layout atlas where every limb is isolated.
  2. Segmentation — OpenCV connected-components analysis crops each isolated blob
     into its own transparent PNG, ready for position_parts.py / make_atlas.py.

The generator is provider-agnostic and uses the same configuration conventions
as the game-asset-gen skill, so a single setup works across both:

  --backend   auto | openai | openai-responses | gemini   (auto = infer)
  --base-url  custom OpenAI-compatible endpoint, e.g. https://gw.example.com/v1
  --model     gpt-image-2, gpt-image-1, dall-e-3, gemini-2.5-flash-image, ...
  --api-key   explicit key (else read from env)

Env / config keys (first match wins):
  OpenAI key   : --api-key, OPENAI_API_KEY, IMAGE_API_KEY
  OpenAI base  : --base-url, OPENAI_BASE_URL, IMAGE_API_BASE_URL  (default https://api.openai.com/v1)
  Gemini key   : --api-key, GEMINI_API_KEY, GOOGLE_API_KEY, IMAGE_API_KEY
  Default model: --model, IMAGE_MODEL  (else per-backend default)
A nearby .env (walking up from the working directory) is auto-loaded.

Usage:
  python split_character.py character.png --output-dir parts/
  python split_character.py hero.png --backend openai --model gpt-image-2 --output-dir parts/
  python split_character.py hero.png --atlas-only --atlas-out atlas.png   # skip segmentation
  python split_character.py --segment-only atlas.png --output-dir parts/   # skip generation

Requires: opencv-python, Pillow, numpy (segmentation); google-genai only for the
Gemini backend. Install: pip install opencv-python Pillow numpy google-genai
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-image"
DEFAULT_OPENAI_MODEL = "gpt-image-1"
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
USER_AGENT = "spine-animation/1.0 (+https://github.com/anthropics/claude-code)"
RETRY_STATUS = {409, 429, 500, 502, 503, 504, 524, 529}
DEFAULT_MAX_RETRIES = 5
MAX_RETRIES = DEFAULT_MAX_RETRIES

POSITIVE_PROMPT = (
    "A complete 2D game sprite-sheet texture atlas for Spine skeletal animation of "
    "the exact character in the reference image. The character is fully deconstructed "
    "into separated, isolated body parts laid out flatly with clear space between every "
    "part and no overlap: isolated head, torso, upper arms, lower arms, hands, upper "
    "legs, lower legs, feet, plus any hats/hair/accessories. Clean solid white "
    "background. CRITICAL: keep the exact same art style, shading, face, and color "
    "palette as the reference. Flat character design sheet, 2D game asset."
)
NEGATIVE_PROMPT = (
    "Avoid: 3D, realistic, redesigned or altered style, different face, overlapping "
    "parts, connected limbs, full-body standing pose, dynamic pose, background scenery, "
    "drop shadows, background gradients, missing limbs, merged layers, text, watermarks."
)


def _die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------------- #
# .env loader + config resolution (shared conventions with game-asset-gen)
# --------------------------------------------------------------------------- #

def load_dotenv():
    search_roots = [Path.cwd(), Path(__file__).resolve().parent]
    seen: set[Path] = set()
    for root in search_roots:
        search = root.resolve()
        while True:
            candidate = (search / ".env").resolve()
            if candidate not in seen:
                seen.add(candidate)
                if candidate.is_file():
                    _read_env(candidate)
                    return
            if search.parent == search:
                break
            search = search.parent


def _read_env(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


def resolve_backend(backend: str, model: str | None, base_url: str | None) -> str:
    if backend and backend != "auto":
        return backend
    m = (model or "").lower()
    if m.startswith(("gemini", "imagen")):
        return "gemini"
    if m.startswith(("gpt-image", "dall-e", "dalle")):
        return "openai"
    if base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("IMAGE_API_BASE_URL"):
        return "openai"
    return "gemini"


def default_model_for(backend: str) -> str:
    return os.environ.get("IMAGE_MODEL") or (
        DEFAULT_GEMINI_MODEL if backend == "gemini" else DEFAULT_OPENAI_MODEL
    )


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


# --------------------------------------------------------------------------- #
# HTTP plumbing (OpenAI-compatible, no SDK dependency)
# --------------------------------------------------------------------------- #

def _is_retryable_body(detail: str) -> bool:
    low = detail.lower()
    return "rate_limit" in low or "rate limit" in low or "try again" in low


def _send_with_retry(req: urllib.request.Request, url: str) -> dict:
    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            last_err = f"HTTP {e.code} from {url}: {detail[:500]}"
            if not (e.code in RETRY_STATUS or _is_retryable_body(detail)) or attempt == MAX_RETRIES - 1:
                _die(last_err)
        except urllib.error.URLError as e:
            last_err = f"Request to {url} failed: {e.reason}"
            if attempt == MAX_RETRIES - 1:
                _die(last_err)
        backoff = min(2 ** attempt, 16)
        print(f"  Transient failure (attempt {attempt + 1}/{MAX_RETRIES}); retrying in {backoff}s...",
              file=sys.stderr)
        time.sleep(backoff)
    _die(last_err)
    return {}


def _http_post_multipart(url: str, api_key: str, fields: dict, files: list[tuple[str, Path]]) -> dict:
    boundary = f"----spine{uuid.uuid4().hex}"
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
        parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode())
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


def _http_post_json(url: str, api_key: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    return _send_with_retry(req, url)


def _extract_b64_images(obj) -> list[bytes]:
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


# --------------------------------------------------------------------------- #
# Generation backends
# --------------------------------------------------------------------------- #

def generate_atlas(backend, ref_image_path, atlas_out, base_url, api_key, model):
    """Deconstruct the reference into a flat parts atlas. Returns atlas_out path."""
    prompt = f"{POSITIVE_PROMPT}\n\n{NEGATIVE_PROMPT}"
    ref = Path(ref_image_path)

    if backend == "gemini":
        raw = _gemini_edit(prompt, ref, api_key, model)
    elif backend == "openai-responses":
        raw = _openai_responses(prompt, ref, base_url, api_key, model)
    else:  # openai images/edits
        fields = {"model": model, "prompt": prompt, "n": "1"}
        if model.lower().startswith("gpt-image"):
            fields["output_format"] = "png"
        field_name = "image[]" if model.lower().startswith("gpt-image") else "image"
        resp = _http_post_multipart(f"{base_url}/images/edits", api_key, fields, [(field_name, ref)])
        images = _extract_b64_images(resp) or _fetch_url_images(resp)
        raw = images[0] if images else None

    if not raw:
        _die("Image backend returned no atlas image.")
    Path(atlas_out).parent.mkdir(parents=True, exist_ok=True)
    with open(atlas_out, "wb") as f:
        f.write(raw)
    return atlas_out


def _openai_responses(prompt, ref, base_url, api_key, model):
    mime = mimetypes.guess_type(ref.name)[0] or "image/png"
    b64 = base64.b64encode(ref.read_bytes()).decode()
    content = [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": f"data:{mime};base64,{b64}"},
    ]
    payload = {
        "model": model,
        "input": [{"role": "user", "content": content}],
        "tools": [{"type": "image_generation"}],
    }
    resp = _http_post_json(f"{base_url}/responses", api_key, payload)
    images = _extract_b64_images(resp) or _fetch_url_images(resp)
    return images[0] if images else None


def _gemini_edit(prompt, ref, api_key, model):
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        _die("'google-genai' not found. Install: pip install google-genai")
    client = genai.Client(api_key=api_key)
    mime = mimetypes.guess_type(ref.name)[0] or "image/png"
    response = client.models.generate_content(
        model=model,
        contents=[prompt, types.Part.from_bytes(data=ref.read_bytes(), mime_type=mime)],
        config=types.GenerateContentConfig(response_modalities=["Image"]),
    )
    for part in response.parts:
        if getattr(part, "inline_data", None) is not None:
            return part.inline_data.data
        if getattr(part, "text", None):
            print(f"  Model text: {part.text}")
    return None


# --------------------------------------------------------------------------- #
# Segmentation (OpenCV connected components)
# --------------------------------------------------------------------------- #

def segment_parts(atlas_path, output_dir, min_area=500, padding=12, bg_threshold=240):
    import cv2
    import numpy as np

    img = cv2.imread(atlas_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        _die(f"Could not read atlas image: {atlas_path}")
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, bg_threshold, 255, cv2.THRESH_BINARY_INV)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    os.makedirs(output_dir, exist_ok=True)
    h_img, w_img = img.shape[:2]
    saved = []
    idx = 0
    for label_id in range(1, num_labels):
        if stats[label_id, cv2.CC_STAT_AREA] < min_area:
            continue
        x = stats[label_id, cv2.CC_STAT_LEFT]
        y = stats[label_id, cv2.CC_STAT_TOP]
        w = stats[label_id, cv2.CC_STAT_WIDTH]
        h = stats[label_id, cv2.CC_STAT_HEIGHT]
        x1, y1 = max(x - padding, 0), max(y - padding, 0)
        x2, y2 = min(x + w + padding, w_img), min(y + h + padding, h_img)
        crop = img[y1:y2, x1:x2].copy()
        component_mask = labels[y1:y2, x1:x2] == label_id
        crop[~component_mask] = [0, 0, 0, 0]
        out_path = os.path.join(output_dir, f"part_{idx:02d}.png")
        cv2.imwrite(out_path, crop)
        saved.append(out_path)
        idx += 1
    return saved


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    p = argparse.ArgumentParser(
        description="Deconstruct a full character image into separated body-part PNGs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input_image", help="Character reference image (or atlas PNG with --segment-only)")
    p.add_argument("--output-dir", default="parts", help="Directory for cropped part PNGs (default: parts)")
    p.add_argument("--atlas-out", default="atlas.png", help="Generated deconstruction atlas (default: atlas.png)")
    p.add_argument("--backend", default="auto", choices=["auto", "openai", "openai-responses", "gemini"])
    p.add_argument("--base-url", default=None, help="Custom OpenAI-compatible base URL")
    p.add_argument("--model", default=None, help="Model name (e.g. gpt-image-2, gemini-2.5-flash-image)")
    p.add_argument("--api-key", default=None, help="Explicit API key (else read from env)")
    p.add_argument("--atlas-only", action="store_true", help="Generate the atlas but skip segmentation")
    p.add_argument("--segment-only", action="store_true", help="Treat input_image as an atlas; skip generation")
    p.add_argument("--min-area", type=int, default=500, help="Minimum component area in px (default: 500)")
    p.add_argument("--padding", type=int, default=12, help="Padding around each cropped part (default: 12)")
    p.add_argument("--bg-threshold", type=int, default=240, help="Grayscale background threshold (default: 240)")
    p.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                   help=f"HTTP retries on transient/rate-limit failures (default: {DEFAULT_MAX_RETRIES})")
    args = p.parse_args()

    load_dotenv()
    global MAX_RETRIES
    MAX_RETRIES = args.max_retries

    if not os.path.isfile(args.input_image):
        _die(f"Input not found: {args.input_image}")

    if args.segment_only:
        atlas_path = args.input_image
    else:
        backend = resolve_backend(args.backend, args.model, args.base_url)
        model = args.model or default_model_for(backend)
        base_url = resolve_base_url(args.base_url)
        api_key = resolve_api_key(backend, args.api_key)
        print(f"[1/2] Generating parts atlas (backend={backend}, model={model})...")
        atlas_path = generate_atlas(backend, args.input_image, args.atlas_out, base_url, api_key, model)
        print(f"      Atlas saved to {atlas_path}")
        if args.atlas_only:
            print("Done (atlas only). Inspect it, then re-run with --segment-only to crop parts.")
            return

    print("[2/2] Segmenting parts...")
    parts = segment_parts(atlas_path, args.output_dir, args.min_area, args.padding, args.bg_threshold)
    print(f"      Found {len(parts)} parts -> {args.output_dir}/")
    for pp in parts:
        print(f"        - {os.path.basename(pp)}")
    print(f"\nNext: rename parts meaningfully (head.png, torso.png, ...) and feed {args.output_dir}/ "
          "into position_parts.py (with a reference image) or directly into make_atlas.py.")


if __name__ == "__main__":
    main()
