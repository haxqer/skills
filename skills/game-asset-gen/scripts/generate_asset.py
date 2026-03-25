#!/usr/bin/env python3
"""
Game Asset Generator CLI — generates pixel art game assets via Gemini API.

Usage:
  python scripts/generate_asset.py generate --prompt "..." [--out output.png] [--model ...]
  python scripts/generate_asset.py generate-batch --input prompts.jsonl --out-dir ./out/ [--concurrency 3]

Requires: google-genai, Pillow
API key: reads GEMINI_API_KEY from the environment or a nearby .env file.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# .env loader (minimal, no external dependency)
# ---------------------------------------------------------------------------

def load_dotenv(env_path: Path | None = None):
    """Load key=value pairs from a .env file into os.environ."""
    if env_path is None:
        # Search from the current working directory first so installed skills
        # can still pick up a project-local .env, then fall back to the script.
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


# ---------------------------------------------------------------------------
# Gemini image generation
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gemini-2.5-flash-image"
DEFAULT_FUZZ = 30


def _apply_chroma_key(img, fuzz: int = DEFAULT_FUZZ):
    """Remove green (#00FF00) background pixels from a PIL RGBA image in-place.
    Returns the modified image."""
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


def ensure_deps():
    """Check that required packages are available."""
    try:
        from google import genai  # noqa: F401
    except ImportError:
        print("ERROR: 'google-genai' package not found.", file=sys.stderr)
        print("Install with: pip install google-genai Pillow", file=sys.stderr)
        sys.exit(1)
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("ERROR: 'Pillow' package not found.", file=sys.stderr)
        print("Install with: pip install Pillow", file=sys.stderr)
        sys.exit(1)


def get_client():
    """Create Gemini client, reading API key from environment."""
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set.", file=sys.stderr)
        print(
            "Set it in your project .env file or as an environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)
    return genai.Client(api_key=api_key)


def generate_image(
    prompt: str,
    output_path: str = "output.png",
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = "1:1",
    dry_run: bool = False,
    downscale: int | None = None,
    auto_chroma_key: bool = True,
    fuzz: int = DEFAULT_FUZZ,
):
    """Generate a single image from a text prompt.
    By default, auto-removes green (#00FF00) background (disable with auto_chroma_key=False for backgrounds).
    """
    if dry_run:
        ck_label = "ON" if auto_chroma_key else "OFF"
        print(f"[DRY RUN] model={model}, aspect_ratio={aspect_ratio}, chroma_key={ck_label}")
        print(f"[DRY RUN] prompt: {prompt[:200]}...")
        print(f"[DRY RUN] output: {output_path}")
        return

    from google.genai import types
    from PIL import Image as PILImage

    client = get_client()

    print(f"Generating image with {model}...")
    print(f"  Prompt: {prompt[:120]}...")

    response = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["Image"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            ),
        ),
    )

    # Extract image from response
    image_saved = False
    for part in response.parts:
        if part.inline_data is not None:
            import io
            img = PILImage.open(io.BytesIO(part.inline_data.data)).convert("RGBA")

            # Auto chroma-key: remove green background
            if auto_chroma_key:
                img, removed = _apply_chroma_key(img, fuzz=fuzz)
                total = img.width * img.height
                pct = removed * 100.0 / total if total else 0
                print(f"  Chroma-key: removed {removed} green pixels ({pct:.1f}%)")

            # Optional downscale (nearest-neighbor for pixel art)
            if downscale and downscale > 0:
                img = img.resize((downscale, downscale), PILImage.NEAREST)
                print(f"  Downscaled to {downscale}x{downscale}")

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(out), "PNG")
            print(f"  Saved: {out}")
            image_saved = True
            break
        elif part.text is not None:
            print(f"  Model text: {part.text}")

    if not image_saved:
        print("WARNING: No image was generated. The model may have declined the prompt.", file=sys.stderr)
        return False
    return True


def generate_batch(
    input_path: str,
    out_dir: str = "output",
    model: str = DEFAULT_MODEL,
    concurrency: int = 3,
    dry_run: bool = False,
    auto_chroma_key: bool = True,
    fuzz: int = DEFAULT_FUZZ,
):
    """Generate images from a JSONL file (one job per line).
    By default, auto-removes green background. Per-job override: set "chroma_key": false in JSONL.
    """
    jobs = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))

    ck_label = "ON" if auto_chroma_key else "OFF"
    print(f"Loaded {len(jobs)} jobs from {input_path}")
    print(f"Model: {model}, Concurrency: {concurrency}, Chroma-key: {ck_label}")
    print(f"Output dir: {out_dir}")

    if dry_run:
        for i, job in enumerate(jobs):
            out_name = job.get("out_name", f"output-{i:03d}.png")
            job_ck = job.get("chroma_key", auto_chroma_key)
            ck_str = "CK" if job_ck else "no-CK"
            print(f"  [DRY RUN] [{i}] {out_name} ({ck_str}): {job['prompt'][:80]}...")
        return

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    client = get_client()

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _gen(idx_job):
        idx, job = idx_job
        from google.genai import types
        from PIL import Image as PILImage

        prompt = job["prompt"]
        job_model = job.get("model", model)
        aspect = job.get("aspect_ratio", "1:1")
        downscale = job.get("downscale", None)
        job_chroma_key = job.get("chroma_key", auto_chroma_key)
        job_fuzz = job.get("fuzz", fuzz)
        out_name = job.get("out_name", f"output-{idx:03d}.png")
        out_path = Path(out_dir) / out_name

        print(f"  [{idx}] Generating: {prompt[:80]}...")

        try:
            response = client.models.generate_content(
                model=job_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["Image"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect,
                    ),
                ),
            )

            for part in response.parts:
                if part.inline_data is not None:
                    import io
                    img = PILImage.open(io.BytesIO(part.inline_data.data)).convert("RGBA")

                    # Auto chroma-key
                    if job_chroma_key:
                        img, removed = _apply_chroma_key(img, fuzz=job_fuzz)
                        total = img.width * img.height
                        pct = removed * 100.0 / total if total else 0
                        print(f"  [{idx}] Chroma-key: removed {removed} green px ({pct:.1f}%)")

                    if downscale and downscale > 0:
                        img = img.resize((downscale, downscale), PILImage.NEAREST)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(str(out_path), "PNG")
                    print(f"  [{idx}] Saved: {out_path}")
                    return True
                elif part.text is not None:
                    print(f"  [{idx}] Model text: {part.text}")

            print(f"  [{idx}] WARNING: No image generated", file=sys.stderr)
            return False

        except Exception as e:
            print(f"  [{idx}] ERROR: {e}", file=sys.stderr)
            return False

    success = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_gen, (i, job)): i for i, job in enumerate(jobs)}
        for future in as_completed(futures):
            if future.result():
                success += 1
            else:
                failed += 1

    print(f"\nBatch complete: {success} succeeded, {failed} failed out of {len(jobs)} total")


def chroma_key(
    input_path: str,
    output_path: str | None = None,
    fuzz: int = DEFAULT_FUZZ,
    downscale: int | None = None,
):
    """Remove green (#00FF00) background and optionally downscale."""
    from PIL import Image as PILImage

    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_keyed{p.suffix}")

    img = PILImage.open(input_path).convert("RGBA")
    img, removed = _apply_chroma_key(img, fuzz=fuzz)
    total = img.width * img.height
    pct = removed * 100.0 / total if total else 0

    if downscale and downscale > 0:
        img = img.resize((downscale, downscale), PILImage.NEAREST)
        print(f"  Downscaled to {downscale}x{downscale}")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), "PNG")
    print(f"  Saved: {out} (removed {removed} green px, {pct:.1f}%)")


def chroma_key_dir(
    input_dir: str,
    output_dir: str | None = None,
    fuzz: int = 30,
    downscale: int | None = None,
):
    """Chroma key all PNGs in a directory."""
    in_dir = Path(input_dir)
    out_dir = Path(output_dir) if output_dir else in_dir / "keyed"
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(in_dir.glob("*.png"))
    print(f"Processing {len(pngs)} PNGs from {in_dir}...")

    for png in pngs:
        out_path = out_dir / png.name
        print(f"  {png.name}...", end="")
        chroma_key(str(png), str(out_path), fuzz=fuzz, downscale=downscale)

    print(f"Done. Output in {out_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Game Asset Generator — generate pixel art via Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Generate a single asset
  python generate_asset.py generate --prompt "chibi pixel art warrior..." --out art/player/warrior/idle_00.png

  # Batch generate from JSONL
  python generate_asset.py generate-batch --input frames.jsonl --out-dir tmp/raw/

  # Remove green background
  python generate_asset.py chroma-key --input raw.png --out clean.png --downscale 48

  # Chroma key entire directory
  python generate_asset.py chroma-key-dir --input-dir tmp/raw/ --output-dir art/player/warrior/ --downscale 48
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- generate ---
    gen_p = sub.add_parser(
        "generate", help="Generate a single image (auto chroma-key by default)"
    )
    gen_p.add_argument("--prompt", required=True, help="Text prompt")
    gen_p.add_argument(
        "--out", default="output.png", help="Output file path (default: output.png)"
    )
    gen_p.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Gemini model (default: {DEFAULT_MODEL})"
    )
    gen_p.add_argument("--aspect-ratio", default="1:1", help="Aspect ratio (default: 1:1)")
    gen_p.add_argument(
        "--downscale",
        type=int,
        default=None,
        help="Downscale to NxN pixels (nearest-neighbor)",
    )
    gen_p.add_argument(
        "--no-chroma-key",
        action="store_true",
        help="Skip basic green background removal; recommended when using smart_remove_bg.py afterward",
    )
    gen_p.add_argument(
        "--fuzz",
        type=int,
        default=DEFAULT_FUZZ,
        help=f"Chroma-key color tolerance (default: {DEFAULT_FUZZ})",
    )
    gen_p.add_argument("--dry-run", action="store_true", help="Print prompt without calling API")

    # --- generate-batch ---
    batch_p = sub.add_parser(
        "generate-batch",
        help="Batch generate from JSONL (auto chroma-key by default)",
    )
    batch_p.add_argument("--input", required=True, help="JSONL file with one job per line")
    batch_p.add_argument("--out-dir", default="output", help="Output directory (default: output/)")
    batch_p.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Default model (default: {DEFAULT_MODEL})"
    )
    batch_p.add_argument("--concurrency", type=int, default=3, help="Max concurrent requests (default: 3)")
    batch_p.add_argument(
        "--no-chroma-key",
        action="store_true",
        help="Skip basic green background removal for all jobs; recommended when using smart_remove_bg.py afterward",
    )
    batch_p.add_argument(
        "--fuzz",
        type=int,
        default=DEFAULT_FUZZ,
        help=f"Chroma-key color tolerance (default: {DEFAULT_FUZZ})",
    )
    batch_p.add_argument("--dry-run", action="store_true", help="Print jobs without calling API")

    # --- chroma-key ---
    ck_p = sub.add_parser("chroma-key", help="Remove green background from an image")
    ck_p.add_argument("--input", required=True, help="Input PNG file")
    ck_p.add_argument("--out", default=None, help="Output file (default: input_keyed.png)")
    ck_p.add_argument("--fuzz", type=int, default=30, help="Color tolerance (0-255, default: 30)")
    ck_p.add_argument("--downscale", type=int, default=None, help="Downscale to NxN pixels")

    # --- chroma-key-dir ---
    ckd_p = sub.add_parser("chroma-key-dir", help="Chroma key all PNGs in a directory")
    ckd_p.add_argument("--input-dir", required=True, help="Input directory")
    ckd_p.add_argument("--output-dir", default=None, help="Output directory (default: input_dir/keyed/)")
    ckd_p.add_argument("--fuzz", type=int, default=30, help="Color tolerance (0-255, default: 30)")
    ckd_p.add_argument("--downscale", type=int, default=None, help="Downscale to NxN pixels")

    args = parser.parse_args()

    # Load .env from project root
    load_dotenv()

    if args.command == "generate":
        if not args.dry_run:
            ensure_deps()
        generate_image(
            prompt=args.prompt,
            output_path=args.out,
            model=args.model,
            aspect_ratio=args.aspect_ratio,
            dry_run=args.dry_run,
            downscale=args.downscale,
            auto_chroma_key=not args.no_chroma_key,
            fuzz=args.fuzz,
        )

    elif args.command == "generate-batch":
        if not args.dry_run:
            ensure_deps()
        generate_batch(
            input_path=args.input,
            out_dir=args.out_dir,
            model=args.model,
            concurrency=args.concurrency,
            dry_run=args.dry_run,
            auto_chroma_key=not args.no_chroma_key,
            fuzz=args.fuzz,
        )

    elif args.command == "chroma-key":
        from PIL import Image as PILImage  # noqa: F401
        chroma_key(
            input_path=args.input,
            output_path=args.out,
            fuzz=args.fuzz,
            downscale=args.downscale,
        )

    elif args.command == "chroma-key-dir":
        from PIL import Image as PILImage  # noqa: F401
        chroma_key_dir(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            fuzz=args.fuzz,
            downscale=args.downscale,
        )


if __name__ == "__main__":
    main()
