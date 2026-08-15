# Animation Presets, Principles & Adjustment Format

## Built-in presets (`build_spine_json.py`)

Listing animation names in the config's `animations` array generates these.
Each generator only touches bones that exist, so a partial rig still works.

| Preset | Duration | Loop | Core technique |
|--------|----------|------|----------------|
| `idle` | 1.6 s | yes | Hip ±1.5px lift, torso ±1.5° sway, head counter-sway, gentle arm drift |
| `walk` | 0.8 s | yes | Opposing arm/leg swing, hip bob, torso lean; back leg straight, front leg bent |
| `run` | 0.5 s | yes | Exaggerated walk + constant forward torso lean + bigger vertical bounce |
| `wave` | 1.2 s | no | Raise right arm, oscillate forearm, slight torso/head tilt |
| `jump` | 1.0 s | no | Anticipation squat → launch → float → land impact → settle (5 phases) |
| `attack` | 0.6 s | no | Wind-up → fast strike → follow-through on right arm + torso lunge |

The generators encode timing offsets between related bones (head peaks slightly
after the torso, etc.) and use Bézier easing presets. Read the generator functions
in `scripts/build_spine_json.py` if you need to know exactly which bones move.

## The 12 principles that make these read well

The presets are deliberately built around classic animation principles; keep them
in mind when authoring custom motion:

- **Anticipation** — wind up before a big action (the squat before a jump, pulling
  the arm back before a strike). Without it, motion looks robotic.
- **Follow-through & overlapping action** — secondary parts (head, hat, hair,
  hands) lag the driving bone by ~0.05–0.15s and settle after it stops.
- **Slow in / slow out** — use Bézier easing, not linear, so motion accelerates and
  decelerates naturally. `[0.25, 0, 0.75, 1]` is the workhorse.
- **Squash & stretch / exaggeration** — scale the amplitude to the energy of the
  action (idle is subtle, run is large).
- **Arcs** — joints rotate around their parent, so limbs naturally travel in arcs;
  this is why bone `length`/`rotation` should be set sensibly.

Practical rules of thumb:

- Larger movements on larger/lower bones (hip > torso > head). The extremities
  inherit and amplify the base motion.
- Every looping animation must return to its starting values on the final keyframe.
- Offset the phase of left vs. right limbs by half the cycle for walk/run.

## Custom animations

For motion the presets don't cover (dance, cast, crouch, a creature-specific move),
add a `custom_animations` block to the build config. It is merged verbatim into the
exported `animations`, so it must already be valid Spine timeline JSON:

```json
"custom_animations": {
  "cast": {
    "bones": {
      "right-upper-arm": { "rotate": [
        { "time": 0, "angle": 0, "curve": [0.25, 0, 0.75, 1] },
        { "time": 0.3, "angle": -110 },
        { "time": 0.8, "angle": -110, "curve": "stepped" },
        { "time": 1.0, "angle": 0 }
      ]}
    }
  }
}
```

See `spine-json-format.md` for the full timeline grammar.

## Interactive editor & adjustment format

When auto-positioning needs hand correction, a small HTML editor (drag parts,
nudge with arrow keys, reorder z-index, edit numeric X/Y/rotation) lets the user
fine-tune placement and export a corrections file. The adjustment format keeps the
original offset, the user delta, and the resulting final value so changes are
**reviewable, revertible, and composable**:

```json
{
  "adjustments": {
    "right-arm": {
      "original_offset": { "x": -1.5, "y": 0 },
      "user_offset":     { "dx": -29.4, "dy": -84.1, "drot": 0 },
      "final_offset":    { "x": -30.9, "y": -84.1 }
    }
  },
  "draw_order": ["right-arm", "left-leg", "torso", "head"]
}
```

To apply: set each attachment's `x`/`y` to its `final_offset`, and reorder slots to
match `draw_order`. Then regenerate the preview to confirm.
