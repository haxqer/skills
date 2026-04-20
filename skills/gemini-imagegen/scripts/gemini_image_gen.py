#!/usr/bin/env python3
"""Generate or edit images with Google's Gemini API and Imagen models."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
from typing import Any, Iterable, Sequence

DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_OUT_DIR = Path("output/gemini-imagegen")
DEFAULT_OUTPUT_MIME = "image/png"

KNOWN_GEMINI_IMAGE_MODELS = {
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
}

KNOWN_IMAGEN_MODELS = {
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001",
    "imagen-4.0-ultra-generate-001",
}

PERSON_GENERATION_CHOICES = {
    "dont-allow": "DONT_ALLOW",
    "allow-adult": "ALLOW_ADULT",
    "allow-all": "ALLOW_ALL",
}


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _read_prompt(prompt: str | None, prompt_file: str | None) -> str:
    if prompt and prompt_file:
        _die("Use --prompt or --prompt-file, not both.")
    if prompt_file:
        path = Path(prompt_file)
        if not path.is_file():
            _die(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    _die("Missing prompt. Use --prompt or --prompt-file.")
    return ""


def _ensure_api_key(dry_run: bool) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key
    if dry_run:
        _warn("GEMINI_API_KEY / GOOGLE_API_KEY is not set; continuing in dry-run mode.")
        return None
    _die("GEMINI_API_KEY is not set. Export it before running live requests.")
    return None


def _backend_for_model(model: str) -> str:
    if model.startswith("imagen-"):
        return "imagen"
    if "image" in model:
        return "gemini"
    _die(
        "Model does not look image-capable. Use an image Gemini model such as "
        f"{', '.join(sorted(KNOWN_GEMINI_IMAGE_MODELS))} or an Imagen model such as "
        f"{', '.join(sorted(KNOWN_IMAGEN_MODELS))}."
    )
    return ""


def _check_image_paths(paths: Iterable[str]) -> list[Path]:
    resolved: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            _die(f"Image file not found: {path}")
        resolved.append(path)
    return resolved


def _normalize_input_images(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [os.fspath(value)]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, (str, os.PathLike)):
                _die("Batch job input_images entries must be file paths.")
            normalized.append(os.fspath(item))
        return normalized
    _die("Batch job input_images must be a path or a list of paths.")
    return []


def _mime_for_path(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed:
        return guessed
    suffix = path.suffix.lower()
    if suffix == ".jpg":
        return "image/jpeg"
    if suffix in {".png", ".jpeg", ".webp", ".gif"}:
        return f"image/{suffix.lstrip('.')}"
    _die(f"Unsupported image type for {path}; use png, jpeg, webp, or gif.")
    return ""


def _ext_for_mime(mime_type: str | None) -> str:
    if mime_type == "image/jpeg":
        return ".jpg"
    if mime_type == "image/png":
        return ".png"
    if mime_type == "image/webp":
        return ".webp"
    guessed = mimetypes.guess_extension(mime_type or "")
    return guessed or ".bin"


def _augment_prompt(args: argparse.Namespace, prompt: str) -> str:
    if not args.augment:
        return prompt

    sections: list[str] = []
    if args.use_case:
        sections.append(f"Use case: {args.use_case}")
    if args.asset_type:
        sections.append(f"Asset type: {args.asset_type}")
    sections.append(f"Primary request: {prompt}")
    if args.scene:
        sections.append(f"Scene/background: {args.scene}")
    if args.subject:
        sections.append(f"Subject: {args.subject}")
    if args.style:
        sections.append(f"Style/medium: {args.style}")
    if args.composition:
        sections.append(f"Composition/framing: {args.composition}")
    if args.lighting:
        sections.append(f"Lighting/mood: {args.lighting}")
    if args.palette:
        sections.append(f"Color palette: {args.palette}")
    if args.text:
        sections.append(f'Text (verbatim): "{args.text}"')
    if args.constraints:
        sections.append(f"Constraints: {args.constraints}")
    if args.negative:
        sections.append(f"Avoid: {args.negative}")
    return "\n".join(sections)


def _build_output_paths(
    out: str | None,
    out_dir: str | None,
    count: int,
    extension: str,
) -> list[Path]:
    if count < 1:
        _die("count must be >= 1")

    if out_dir:
        base_dir = Path(out_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        return [base_dir / f"image_{index}{extension}" for index in range(1, count + 1)]

    if out:
        out_path = Path(out)
    else:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        out_path = DEFAULT_OUT_DIR / stamp / f"image{extension}"

    if out_path.suffix == "":
        out_path = out_path.with_suffix(extension)
    elif out_path.suffix.lower() != extension:
        _warn(
            f"Output extension {out_path.suffix} does not match generated mime type {extension}."
        )

    if count == 1:
        return [out_path]

    return [
        out_path.with_name(f"{out_path.stem}-{index}{out_path.suffix}")
        for index in range(1, count + 1)
    ]


def _write_binary_outputs(
    payloads: Sequence[tuple[bytes, str]],
    out: str | None,
    out_dir: str | None,
    force: bool,
) -> list[Path]:
    if not payloads:
        return []

    paths = _build_output_paths(out, out_dir, len(payloads), _ext_for_mime(payloads[0][1]))
    for (blob, _mime_type), path in zip(payloads, paths):
        if path.exists() and not force:
            _die(f"Output already exists: {path} (use --force to overwrite)")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        print(f"Wrote {path}")
    return paths


def _write_text_output(text_chunks: Sequence[str], text_out: str | None, force: bool) -> None:
    if not text_chunks:
        return
    combined = "\n\n".join(chunk.strip() for chunk in text_chunks if chunk.strip()).strip()
    if not combined:
        return
    print("\nText output:\n")
    print(combined)
    if not text_out:
        return
    path = Path(text_out)
    if path.exists() and not force:
        _die(f"Text output already exists: {path} (use --force to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(combined + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def _extract_gemini_parts(response: Any) -> tuple[list[tuple[bytes, str]], list[str]]:
    parts: list[Any] = []
    direct_parts = getattr(response, "parts", None)
    if direct_parts:
        parts.extend(direct_parts)
    else:
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            candidate_parts = getattr(content, "parts", None)
            if candidate_parts:
                parts.extend(candidate_parts)

    images: list[tuple[bytes, str]] = []
    texts: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            texts.append(text)
        inline = getattr(part, "inline_data", None)
        if inline and getattr(inline, "data", None):
            images.append((inline.data, inline.mime_type or DEFAULT_OUTPUT_MIME))
    return images, texts


def _extract_imagen_images(response: Any) -> list[tuple[bytes, str]]:
    payloads: list[tuple[bytes, str]] = []
    for generated in getattr(response, "generated_images", []) or []:
        image = getattr(generated, "image", None)
        if image and getattr(image, "image_bytes", None):
            payloads.append((image.image_bytes, image.mime_type or DEFAULT_OUTPUT_MIME))
    return payloads


def _person_generation_for_imagen(types_module: Any, value: str | None) -> Any:
    if not value:
        return None
    return types_module.PersonGeneration[PERSON_GENERATION_CHOICES[value]]


def _dry_run_summary(args: argparse.Namespace, final_prompt: str, backend: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "mode": args.mode,
        "backend": backend,
        "model": args.model,
        "prompt": final_prompt,
        "input_images": list(getattr(args, "input_image", []) or []),
        "out": args.out,
        "out_dir": args.out_dir,
        "allow_text": args.allow_text,
    }
    for key in (
        "aspect_ratio",
        "image_size",
        "negative_prompt",
        "output_mime_type",
        "output_compression_quality",
        "person_generation",
        "google_search",
        "image_search",
        "n",
        "text_out",
    ):
        value = getattr(args, key, None)
        if value not in (None, False):
            summary[key] = value
    return summary


def _load_sdk() -> tuple[Any, Any]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        _die(
            "Missing dependency google-genai. Re-run with "
            "`uv run --with google-genai python ...` or install it into a uv-managed environment."
        )
        raise AssertionError from exc
    return genai, types


def _build_gemini_tools(types_module: Any, args: argparse.Namespace) -> list[Any] | None:
    if not args.google_search and not args.image_search:
        return None
    if args.model != "gemini-3.1-flash-image-preview":
        _die(
            "--google-search and --image-search currently require "
            "gemini-3.1-flash-image-preview."
        )

    search_types_kwargs: dict[str, Any] = {}
    if args.google_search:
        search_types_kwargs["web_search"] = types_module.WebSearch()
    if args.image_search:
        search_types_kwargs["image_search"] = types_module.ImageSearch()

    return [
        types_module.Tool(
            google_search=types_module.GoogleSearch(
                search_types=types_module.SearchTypes(**search_types_kwargs)
            )
        )
    ]


def _run_gemini_generate_or_edit(args: argparse.Namespace, final_prompt: str, api_key: str) -> None:
    if args.n != 1:
        _warn("Gemini native image models are treated as single-image-per-call; ignoring -n.")

    genai, types_module = _load_sdk()
    client = genai.Client(api_key=api_key)

    contents: list[Any] = [final_prompt]
    for image_path in _check_image_paths(getattr(args, "input_image", []) or []):
        contents.append(
            types_module.Part.from_bytes(
                data=image_path.read_bytes(),
                mime_type=_mime_for_path(image_path),
            )
        )

    response_modalities = ["IMAGE"]
    if args.allow_text:
        response_modalities = ["TEXT", "IMAGE"]

    config = types_module.GenerateContentConfig(
        response_modalities=response_modalities,
        image_config=types_module.ImageConfig(
            aspect_ratio=args.aspect_ratio,
            image_size=args.image_size,
            person_generation=PERSON_GENERATION_CHOICES.get(args.person_generation),
            output_mime_type=args.output_mime_type,
            output_compression_quality=args.output_compression_quality,
        ),
        tools=_build_gemini_tools(types_module, args),
    )

    response = client.models.generate_content(
        model=args.model,
        contents=contents,
        config=config,
    )
    images, texts = _extract_gemini_parts(response)
    if not images:
        _die("The Gemini response did not include image bytes.")
    _write_binary_outputs(images, args.out, args.out_dir, args.force)
    _write_text_output(texts, args.text_out, args.force)


def _run_imagen_generate(args: argparse.Namespace, final_prompt: str, api_key: str) -> None:
    if getattr(args, "input_image", None):
        _die("Imagen generation in this skill is text-to-image only; use a Gemini image model for edits.")

    genai, types_module = _load_sdk()
    client = genai.Client(api_key=api_key)

    config = types_module.GenerateImagesConfig(
        number_of_images=args.n,
        aspect_ratio=args.aspect_ratio,
        negative_prompt=args.negative_prompt,
        output_mime_type=args.output_mime_type,
        output_compression_quality=args.output_compression_quality,
        image_size=args.image_size,
        person_generation=_person_generation_for_imagen(types_module, args.person_generation),
    )

    response = client.models.generate_images(
        model=args.model,
        prompt=final_prompt,
        config=config,
    )
    images = _extract_imagen_images(response)
    if not images:
        _die("The Imagen response did not include image bytes.")
    _write_binary_outputs(images, args.out, args.out_dir, args.force)


def _run_single(args: argparse.Namespace) -> None:
    backend = _backend_for_model(args.model)
    input_images = _normalize_input_images(getattr(args, "input_image", None))
    args.input_image = input_images
    if args.mode == "edit" and not input_images:
        _die("Edit mode requires at least one input image.")
    if backend == "imagen" and args.mode == "edit":
        _die("Edit mode requires a native Gemini image model, not an Imagen model.")

    final_prompt = _augment_prompt(args, _read_prompt(args.prompt, args.prompt_file))
    if args.dry_run:
        print(json.dumps(_dry_run_summary(args, final_prompt, backend), indent=2, ensure_ascii=False))
        return

    api_key = _ensure_api_key(args.dry_run)
    if backend == "gemini":
        _run_gemini_generate_or_edit(args, final_prompt, api_key or "")
        return
    _run_imagen_generate(args, final_prompt, api_key or "")


def _namespace_from_job(job: dict[str, Any], default_mode: str) -> argparse.Namespace:
    prompt = job.get("prompt")
    prompt_file = job.get("prompt_file")
    input_images_value = job.get("input_images")
    if input_images_value is None:
        input_images_value = job.get("input_image")
    input_images = _normalize_input_images(input_images_value)
    mode = job.get("mode") or ("edit" if input_images else default_mode)
    return argparse.Namespace(
        mode=mode,
        prompt=prompt,
        prompt_file=prompt_file,
        model=job.get("model", DEFAULT_MODEL),
        input_image=input_images,
        out=job.get("out"),
        out_dir=job.get("out_dir"),
        force=bool(job.get("force", False)),
        dry_run=bool(job.get("dry_run", False)),
        allow_text=bool(job.get("allow_text", False)),
        text_out=job.get("text_out"),
        aspect_ratio=job.get("aspect_ratio"),
        image_size=job.get("image_size"),
        output_mime_type=job.get("output_mime_type", DEFAULT_OUTPUT_MIME),
        output_compression_quality=job.get("output_compression_quality"),
        person_generation=job.get("person_generation"),
        negative_prompt=job.get("negative_prompt"),
        google_search=bool(job.get("google_search", False)),
        image_search=bool(job.get("image_search", False)),
        n=int(job.get("n", 1)),
        augment=bool(job.get("augment", True)),
        use_case=job.get("use_case"),
        asset_type=job.get("asset_type"),
        scene=job.get("scene"),
        subject=job.get("subject"),
        style=job.get("style"),
        composition=job.get("composition"),
        lighting=job.get("lighting"),
        palette=job.get("palette"),
        text=job.get("text"),
        constraints=job.get("constraints"),
        negative=job.get("negative"),
    )


def _run_batch(args: argparse.Namespace) -> None:
    jobs_path = Path(args.jobs)
    if not jobs_path.is_file():
        _die(f"Jobs file not found: {jobs_path}")

    lines = [line for line in jobs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        _die("Jobs file is empty.")

    for index, line in enumerate(lines, start=1):
        try:
            job = json.loads(line)
        except json.JSONDecodeError as exc:
            _die(f"Invalid JSON on line {index}: {exc}")
        if not isinstance(job, dict):
            _die(f"Line {index} must decode to a JSON object.")
        if args.force:
            job["force"] = True
        if args.dry_run:
            job["dry_run"] = True
        namespace = _namespace_from_job(job, "generate")
        print(f"\n== Job {index}/{len(lines)} ==")
        _run_single(namespace)


def _add_common_prompt_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", help="Prompt text.")
    parser.add_argument("--prompt-file", help="Read the prompt from a UTF-8 text file.")
    parser.add_argument("--use-case", help="Prompt augmentation use-case slug.")
    parser.add_argument("--asset-type", help="Where the generated asset will be used.")
    parser.add_argument("--scene", help="Scene or background notes.")
    parser.add_argument("--subject", help="Primary subject.")
    parser.add_argument("--style", help="Style or medium.")
    parser.add_argument("--composition", help="Composition or framing notes.")
    parser.add_argument("--lighting", help="Lighting or mood notes.")
    parser.add_argument("--palette", help="Color palette notes.")
    parser.add_argument("--text", help="Exact text that must render in the image.")
    parser.add_argument("--constraints", help="Hard constraints to preserve.")
    parser.add_argument("--negative", help="Negative visual constraints for prompt augmentation.")
    parser.add_argument(
        "--no-augment",
        action="store_false",
        dest="augment",
        help="Use the prompt as-is without labeled augmentation.",
    )
    parser.set_defaults(augment=True)


def _add_common_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini or Imagen model name.")
    parser.add_argument("--out", help="Output file path for one image, or a base path for many images.")
    parser.add_argument("--out-dir", help="Write numbered outputs into this directory.")
    parser.add_argument("--aspect-ratio", help="Aspect ratio such as 1:1, 16:9, or 9:16.")
    parser.add_argument("--image-size", help="Optional provider-specific image size string.")
    parser.add_argument(
        "--output-mime-type",
        default=DEFAULT_OUTPUT_MIME,
        help="Requested output MIME type, for example image/png or image/jpeg.",
    )
    parser.add_argument(
        "--output-compression-quality",
        type=int,
        help="Optional output compression quality (provider-specific).",
    )
    parser.add_argument(
        "--person-generation",
        choices=sorted(PERSON_GENERATION_CHOICES.keys()),
        help="Person-generation policy.",
    )
    parser.add_argument(
        "-n",
        type=int,
        default=1,
        help="Requested number of images. Some backends may clamp this.",
    )
    parser.add_argument("--allow-text", action="store_true", help="Allow text alongside image output.")
    parser.add_argument("--text-out", help="Write any returned text to this file.")
    parser.add_argument("--google-search", action="store_true", help="Enable grounded web search.")
    parser.add_argument(
        "--image-search",
        action="store_true",
        help="Enable grounded image search. Current docs restrict this to gemini-3.1-flash-image-preview.",
    )
    parser.add_argument(
        "--negative-prompt",
        help="Imagen-only negative prompt. Ignored by Gemini native image models.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Print the request summary without calling the API.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    generate = subparsers.add_parser("generate", help="Generate new images from a prompt.")
    _add_common_prompt_args(generate)
    _add_common_generation_args(generate)

    edit = subparsers.add_parser("edit", help="Edit one or more input images with a prompt.")
    _add_common_prompt_args(edit)
    _add_common_generation_args(edit)
    edit.add_argument(
        "--input-image",
        action="append",
        required=True,
        help="Input image path. Repeat for multi-image edits.",
    )

    batch = subparsers.add_parser("batch", help="Run multiple JSONL jobs sequentially.")
    batch.add_argument("--jobs", required=True, help="JSONL file with one job object per line.")
    batch.add_argument("--force", action="store_true", help="Force overwrite for every job.")
    batch.add_argument("--dry-run", action="store_true", help="Dry-run every job.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == "batch":
        _run_batch(args)
        return 0

    _run_single(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
