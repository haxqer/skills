#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(
        "Pillow is required for test_chroma_key_cutout.py. Create a virtualenv and install "
        "Pillow plus NumPy before running this test."
    ) from exc


REPO_ROOT = Path(__file__).resolve().parents[2]
CUTOUT_SCRIPT = REPO_ROOT / "skills/godot/scripts/assets/chroma_key_cutout.py"
TEMP_ROOTS: list[Path] = []


def main() -> None:
    try:
        test_single_image_cutout_preserves_canvas_and_alpha()
        test_directory_batch_uses_natural_sort_and_auto_bg_detection()
        test_tight_crop_reduces_canvas_to_subject_bounds()
        print("All chroma key cutout tests passed.")
    finally:
        cleanup_temp_roots()


def test_single_image_cutout_preserves_canvas_and_alpha() -> None:
    temp_root = create_temp_root()
    source_path = temp_root / "source.png"
    output_path = temp_root / "cutout.png"
    create_test_image(
        source_path,
        background=(0, 255, 0, 255),
        subject_pixels=[(3, 3), (4, 3), (3, 4), (4, 4)],
        subject_color=(30, 220, 180, 255),
    )

    run_cutout(
        [
            "--input",
            str(source_path),
            "--output",
            str(output_path),
            "--bg-color",
            "00ff00",
            "--tolerance",
            "0",
            "--feather",
            "0",
        ]
    )

    result = Image.open(output_path).convert("RGBA")
    assert result.size == (8, 8)
    assert result.getpixel((0, 0))[3] == 0
    assert result.getpixel((3, 3))[3] == 255


def test_directory_batch_uses_natural_sort_and_auto_bg_detection() -> None:
    temp_root = create_temp_root()
    input_dir = temp_root / "frames"
    output_dir = temp_root / "out"
    input_dir.mkdir(parents=True, exist_ok=True)

    create_test_image(
        input_dir / "frame_10.png",
        background=(0, 255, 0, 255),
        subject_pixels=[(2, 2), (2, 3)],
        subject_color=(255, 180, 30, 255),
    )
    create_test_image(
        input_dir / "frame_2.png",
        background=(0, 255, 0, 255),
        subject_pixels=[(4, 4), (5, 4)],
        subject_color=(40, 120, 255, 255),
    )
    create_test_image(
        input_dir / "frame_1.png",
        background=(0, 255, 0, 255),
        subject_pixels=[(1, 1), (1, 2)],
        subject_color=(255, 255, 255, 255),
    )
    (input_dir / "ignore.txt").write_text("not an image", encoding="utf-8")

    result = run_cutout(
        [
            "--input",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--bg-color",
            "auto",
            "--tolerance",
            "0",
            "--feather",
            "0",
        ]
    )

    output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert output_lines == [
        str((output_dir / "frame_1.png").resolve()),
        str((output_dir / "frame_2.png").resolve()),
        str((output_dir / "frame_10.png").resolve()),
    ]

    frame_1 = Image.open(output_dir / "frame_1.png").convert("RGBA")
    frame_2 = Image.open(output_dir / "frame_2.png").convert("RGBA")
    frame_10 = Image.open(output_dir / "frame_10.png").convert("RGBA")
    assert frame_1.getpixel((0, 0))[3] == 0
    assert frame_2.getpixel((0, 0))[3] == 0
    assert frame_10.getpixel((0, 0))[3] == 0
    assert not (output_dir / "ignore.png").exists()


def test_tight_crop_reduces_canvas_to_subject_bounds() -> None:
    temp_root = create_temp_root()
    source_path = temp_root / "source.png"
    output_path = temp_root / "cropped.png"
    create_test_image(
        source_path,
        background=(255, 0, 255, 255),
        subject_pixels=[(5, 1), (6, 1), (5, 2), (6, 2)],
        subject_color=(255, 255, 255, 255),
    )

    run_cutout(
        [
            "--input",
            str(source_path),
            "--output",
            str(output_path),
            "--bg-color",
            "ff00ff",
            "--tolerance",
            "0",
            "--feather",
            "0",
            "--tight-crop",
        ]
    )

    result = Image.open(output_path).convert("RGBA")
    assert result.size == (2, 2)
    assert result.getpixel((0, 0))[3] == 255


def create_test_image(
    path: Path,
    *,
    background: tuple[int, int, int, int],
    subject_pixels: list[tuple[int, int]],
    subject_color: tuple[int, int, int, int],
) -> None:
    image = Image.new("RGBA", (8, 8), background)
    for coordinates in subject_pixels:
        image.putpixel(coordinates, subject_color)
    image.save(path, format="PNG")


def run_cutout(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(CUTOUT_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Cutout script failed ({result.returncode}).\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def create_temp_root() -> Path:
    temp_root = Path(tempfile.mkdtemp(prefix="godot-cutout-test-"))
    TEMP_ROOTS.append(temp_root)
    return temp_root


def cleanup_temp_roots() -> None:
    while TEMP_ROOTS:
        shutil.rmtree(TEMP_ROOTS.pop(), ignore_errors=True)


if __name__ == "__main__":
    main()
