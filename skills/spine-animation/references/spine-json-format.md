# Spine 4.2 JSON & Atlas Format Reference

Condensed reference for generating valid Spine JSON and atlas files programmatically.
Authoritative spec: https://en.esotericsoftware.com/spine-json-format

## Top-level structure

```json
{ "skeleton": {}, "bones": [], "slots": [], "skins": [], "animations": {} }
```

## skeleton

```json
"skeleton": { "hash": "abc123", "spine": "4.2.0", "x": -200, "y": 0, "width": 400, "height": 600, "images": "./images/" }
```

- `x`/`y`/`width`/`height` describe the setup-pose bounding box. A common convention
  is `x = -(width / 2)`, `y = 0` so the origin sits at the feet center.
- `hash` is any stable string; `build_spine_json.py` derives it from the config.

## bones (parent-before-child order is required)

```json
"bones": [
  { "name": "root" },
  { "name": "hip", "parent": "root", "x": 0, "y": 200, "length": 30 },
  { "name": "torso", "parent": "hip", "length": 120 }
]
```

- Defaults when omitted: `x=0, y=0, rotation=0, scaleX=1, scaleY=1, length=0`.
- `x`/`y` are **relative to the parent bone** in the parent's local space.
- A bone must appear **after** its parent in the array, or the runtime rejects the file.

## slots (array order = draw order; lower index draws behind)

```json
"slots": [
  { "name": "back-arm", "bone": "left-upper-arm", "attachment": "back-arm" },
  { "name": "torso", "bone": "torso", "attachment": "torso" }
]
```

The slot order is the single source of truth for z-order. Put back parts first,
front parts last. `attachment` names the region shown in the setup pose.

## skins & region attachments

```json
"skins": [{
  "name": "default",
  "attachments": {
    "torso": { "torso": { "x": 0, "y": 60, "width": 120, "height": 200, "rotation": 0, "scaleX": 1, "scaleY": 1 } }
  }
}]
```

- Outer key = slot name, inner key = attachment name (usually the same).
- `x`/`y` offset the image **relative to its bone**, measured to the image center.
- `width`/`height` are the source region pixel dimensions.

## animation timelines

Timelines are grouped by bone, then by property (`rotate`, `translate`, `scale`, `shear`).

```json
"animations": {
  "idle": {
    "bones": {
      "torso": {
        "rotate": [
          { "time": 0, "angle": 0, "curve": [0.25, 0, 0.75, 1] },
          { "time": 0.8, "angle": 2 },
          { "time": 1.6, "angle": 0 }
        ],
        "translate": [
          { "time": 0, "x": 0, "y": 0 },
          { "time": 0.8, "x": 0, "y": 1.5 },
          { "time": 1.6, "x": 0, "y": 0 }
        ]
      }
    }
  }
}
```

- `rotate` keys use `angle` (degrees). `translate`/`scale` use `x`/`y`.
- For a clean loop, the **last keyframe value must equal the first**.

### Curve types

| Curve | Meaning |
|-------|---------|
| omitted | linear interpolation to the next key |
| `"stepped"` | hold the value until the next key |
| `[cx1, cy1, cx2, cy2]` | cubic Bézier easing |

Common Béziers: ease-in-out `[0.25, 0, 0.75, 1]`, ease-in `[0.42, 0, 1, 1]`,
ease-out `[0, 0, 0.58, 1]`, slight overshoot `[0.34, 1.56, 0.64, 1]`.

## Atlas (.atlas) text format

```
skeleton.png
size: 512, 512
format: RGBA8888
filter: Linear, Linear
repeat: none
torso
  rotate: false
  xy: 2, 2
  size: 120, 200
  orig: 120, 200
  offset: 0, 0
  index: -1
head
  rotate: false
  xy: 124, 2
  size: 96, 96
  orig: 96, 96
  offset: 0, 0
  index: -1
```

- The first line is the page PNG filename, followed by page metadata, then one
  block per region. `xy` is the top-left position of the region inside the page.
- `make_atlas.py` emits exactly this layout, so regenerate rather than hand-edit.
