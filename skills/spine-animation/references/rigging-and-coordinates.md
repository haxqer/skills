# Rigging, Coordinates & Auto-Positioning

How to turn separated parts into a correctly placed, correctly layered skeleton.

## Standard humanoid hierarchy

```
root
└── hip
    ├── torso
    │   ├── neck → head → hat / hair
    │   ├── left-shoulder  → left-upper-arm  → left-lower-arm  → left-hand
    │   └── right-shoulder → right-upper-arm → right-lower-arm → right-hand
    ├── left-upper-leg  → left-lower-leg  → left-foot
    └── right-upper-leg → right-lower-leg → right-foot
```

Keep this naming (`left-upper-arm`, `right-lower-leg`, `hip`, `torso`, `head`, …)
because the animation presets in `build_spine_json.py` match bones by these exact
names. Parts that do not map to a standard bone (a sword, a cape, a tail) just get
their own bone parented to the nearest sensible joint.

Non-humanoid rigs (animals, vehicles, props) follow the same idea: one `root`, a
central body bone, then limbs/segments as children. Presets will simply skip bones
they don't recognize, so a custom rig still exports — you author its motion as a
custom animation (see `animation-presets.md`).

## Coordinate system

Spine is **Y-up** with the origin conventionally at the character's feet center.
Image/pixel space is Y-down with origin top-left, so convert when you read pixel
positions out of a layout:

```
center_x = canvas_width / 2          # horizontal middle of the reference
bottom_y = feet_pixel_y              # the y where the feet rest (often near canvas bottom)

spine_x = pixel_x - center_x
spine_y = bottom_y - pixel_y
```

### Bone positions are relative to the parent

Compute each bone's world position first (where the joint sits in Spine space),
then store the **delta** from its parent:

```
bone.x, bone.y  =  child_world_pos - parent_world_pos   (in the parent's frame)
```

`length` and `rotation` describe the bone's resting direction — useful so that a
rotation timeline bends the limb around the joint rather than sliding it.

### Attachment offsets are relative to the bone

An attachment's `x`/`y` place the **image center** relative to the bone origin:

```
attachment.x, attachment.y  =  image_center_world_pos - bone_world_pos
```

If a part looks offset from its joint when previewed, this is almost always the
number to adjust.

## Auto-positioning with `position_parts.py`

When the user supplies separated parts **and** an assembled reference image, the
script recovers each part's placement and the draw order automatically.

```bash
python scripts/position_parts.py \
  --reference assembled_character.png \
  --parts parts/ \
  --output layout.json \
  --debug debug/ \
  --min-matches 4 \
  --ratio 0.80
```

**Phase 1 — placement (SIFT + RANSAC).** SIFT keypoints are extracted from each
alpha-masked part and from the reference, matched with FLANN + Lowe's ratio test,
then a similarity transform (translate + uniform scale + rotation, 4 DOF) is fit
with `cv2.estimateAffinePartial2D`. A 4-DOF similarity is far more robust than a
full 8-DOF homography for flat game art with sparse features. SIFT is tuned for
stylized art (`contrastThreshold=0.02, edgeThreshold=20`). Parts too small or
featureless for SIFT fall back to multi-scale template matching, seeded from the
median SIFT scale so the fallback searches a sensible size range.

**Phase 2 — z-order (occlusion voting).** For every overlapping pair of placed
parts, sample the overlap region and compare each pixel's color against the
reference: whichever part matches the reference better is "in front." Votes build
a directed occlusion graph that is topologically sorted into a back-to-front draw
order, which becomes the slot order.

### Reviewing and correcting the result

Always open `debug/comparison.png` (reference vs. recomposited parts side by side)
and judge it visually. Per-part match overlays are in `debug/sift_<part>.jpg`, and
`debug/bboxes.png` shows the detected boxes. `layout.json` records each part's
`x, y, width, height, scale, rotation, z_index` plus the `z_order` list.

Heavily occluded parts (a thigh behind a belt, a hand behind a hip) are the usual
failure cases — they have too few visible features. Fix them by editing the
offsets in `layout.json` directly, or by using the interactive editor and applying
the exported adjustments (see `animation-presets.md`). Re-running the preview after
each correction is the fastest way to converge.
