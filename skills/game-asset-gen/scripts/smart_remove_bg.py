#!/usr/bin/env python3
"""
Smart background removal for AI-generated pixel art.
Auto-detects the dominant background color from image corners
and removes it, which is safer than exact #00FF00 matching.
"""

from pathlib import Path
from collections import Counter
from PIL import Image


def detect_bg_color(img, sample_size=15):
    """Detect the dominant background color by sampling corners."""
    w, h = img.size
    samples = []
    for x in range(sample_size):
        for y in range(sample_size):
            samples.append(img.getpixel((x, y))[:3])
            samples.append(img.getpixel((w - 1 - x, y))[:3])
            samples.append(img.getpixel((x, h - 1 - y))[:3])
            samples.append(img.getpixel((w - 1 - x, h - 1 - y))[:3])
    most_common = Counter(samples).most_common(1)[0][0]
    return most_common


def remove_bg_flood_fill(img, bg_color, fuzz=100):
    """
    Remove background using a flood fill algorithm from the borders.
    This allows a higher fuzz tolerance to remove green halos
    without destroying the interior of green sprites (like potions),
    as it stops at the sprite's dark outline.
    """
    data = img.load()
    w, h = img.size
    br, bg, bb = bg_color
    fuzz_sq = fuzz * fuzz

    # Start points: corners and middle of edges
    q = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (0, h // 2),
        (w - 1, h // 2),
        (w // 2, h - 1),
    ]
    visited = set(q)
    removed = 0

    # 8-way directional connectivity
    dirs = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
        (1, 1),
        (-1, -1),
        (1, -1),
        (-1, 1),
    ]

    # Pre-allocate queue for speed, though standard list pop(0) is O(N)
    # Using collections.deque is better for BFS
    from collections import deque

    dq = deque(q)

    while dq:
        x, y = dq.popleft()
        r, g, b, a = data[x, y]

        # Already transparent? Skip
        if a == 0:
            continue

        dr = r - br
        dg = g - bg
        db = b - bb

        # Condition to remove: color is within fuzz OR it's highly green and low other colors
        # This aggressively eats the green anti-aliased edge (halo)
        is_bg = dr * dr + dg * dg + db * db <= fuzz_sq
        if not is_bg and g > 30 and g > r + 15 and g > b + 15:
            # Add a secondary distance check to prevent eating the whole image if g>30
            if dr * dr + dg * dg + db * db <= (fuzz + 120) ** 2:
                is_bg = True

        if is_bg:
            data[x, y] = (0, 0, 0, 0)
            removed += 1

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        dq.append((nx, ny))

    return removed


def process_file(input_path, output_path, downscale=None, fuzz=100):
    img = Image.open(input_path).convert("RGBA")
    bg_color = detect_bg_color(img)
    removed = remove_bg_flood_fill(img, bg_color, fuzz=fuzz)
    total = img.size[0] * img.size[1]
    pct = removed / total * 100

    if downscale and downscale > 0:
        img = img.resize((downscale, downscale), Image.NEAREST)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), "PNG")
    print(
        f"  {Path(input_path).name} -> {out.name}  "
        f"(bg={bg_color}, removed {removed}/{total} = {pct:.0f}%)"
    )


def process_dir(input_dir, output_dir, downscale=None, fuzz=100):
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted(in_dir.glob("*.png"))
    print(f"Processing {len(pngs)} files from {in_dir} -> {out_dir}")
    for png in pngs:
        process_file(str(png), str(out_dir / png.name), downscale=downscale, fuzz=fuzz)
    print(f"Done. {len(pngs)} files processed.")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Smart background removal for AI-generated pixel art"
    )
    p.add_argument("--input-dir", required=True, help="Input directory of raw PNGs")
    p.add_argument("--output-dir", required=True, help="Output directory for cleaned PNGs")
    p.add_argument("--downscale", type=int, default=None, help="Downscale to NxN (nearest-neighbor)")
    p.add_argument("--fuzz", type=int, default=100, help="Color distance tolerance (default: 100)")
    args = p.parse_args()
    process_dir(args.input_dir, args.output_dir, downscale=args.downscale, fuzz=args.fuzz)
