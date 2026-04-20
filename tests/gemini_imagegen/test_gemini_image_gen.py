#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import tempfile
from contextlib import redirect_stderr
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "skills/gemini-imagegen/scripts/gemini_image_gen.py"


def load_module():
    spec = importlib.util.spec_from_file_location("gemini_image_gen", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    test_namespace_from_job_accepts_scalar_input_image()
    test_run_single_rejects_edit_without_input_images()
    test_batch_flags_override_per_job_values()
    print("All gemini image generation tests passed.")


def test_namespace_from_job_accepts_scalar_input_image() -> None:
    module = load_module()

    single = module._namespace_from_job(
        {"prompt": "edit this", "input_image": "assets/foo.png"},
        "generate",
    )
    plural = module._namespace_from_job(
        {"prompt": "edit this", "input_images": "assets/bar.png"},
        "generate",
    )

    assert single.mode == "edit"
    assert single.input_image == ["assets/foo.png"]
    assert plural.mode == "edit"
    assert plural.input_image == ["assets/bar.png"]


def test_run_single_rejects_edit_without_input_images() -> None:
    module = load_module()
    args = argparse.Namespace(
        mode="edit",
        model=module.DEFAULT_MODEL,
        input_image=[],
        prompt="Retouch the product photo",
        prompt_file=None,
        augment=False,
        use_case=None,
        asset_type=None,
        scene=None,
        subject=None,
        style=None,
        composition=None,
        lighting=None,
        palette=None,
        text=None,
        constraints=None,
        negative=None,
        dry_run=True,
        out=None,
        out_dir=None,
        allow_text=False,
        aspect_ratio=None,
        image_size=None,
        output_mime_type=module.DEFAULT_OUTPUT_MIME,
        output_compression_quality=None,
        person_generation=None,
        google_search=False,
        image_search=False,
        negative_prompt=None,
        n=1,
        text_out=None,
        force=False,
    )

    stderr = io.StringIO()
    try:
        with redirect_stderr(stderr):
            module._run_single(args)
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected edit mode without input images to fail.")

    assert "Edit mode requires at least one input image." in stderr.getvalue()


def test_batch_flags_override_per_job_values() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="gemini-imagegen-batch-") as temp_dir:
        jobs_path = Path(temp_dir) / "jobs.jsonl"
        jobs_path.write_text(
            json.dumps(
                {
                    "prompt": "Minimal product shot",
                    "force": False,
                    "dry_run": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        captured: list[argparse.Namespace] = []
        original_run_single = module._run_single

        def fake_run_single(namespace: argparse.Namespace) -> None:
            captured.append(namespace)

        module._run_single = fake_run_single
        try:
            module._run_batch(
                argparse.Namespace(
                    jobs=str(jobs_path),
                    force=True,
                    dry_run=True,
                )
            )
        finally:
            module._run_single = original_run_single

    assert len(captured) == 1
    assert captured[0].force is True
    assert captured[0].dry_run is True


if __name__ == "__main__":
    main()
