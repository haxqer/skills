# Animation Frame Specifications

Detailed frame-by-frame pose descriptions for generating consistent animation sequences.

## Contents

- `Player Character Animation`
- `Monster Animation`
- `Effect / VFX Sequences`

---

## Player Character Animation (14 frames)

### Idle (2 frames, ~4 FPS loop)

**Purpose**: Default standing state, subtle life motion.

| Frame | Pose | Key details |
|-------|------|-------------|
| `idle_00` | Standing upright, facing right, arms relaxed at sides, eyes open | Weight on both feet, weapon at rest position |
| `idle_01` | Very subtle shift: slight chest rise (breathing), possibly a blink or small arm shift | Maintain exact same foot position and silhouette width |

**Consistency rule**: Both frames must share identical foot placement and body height. Only the torso/head area should show minimal variation.

---

### Run (4 frames, ~10 FPS loop)

**Purpose**: Horizontal movement cycle.

| Frame | Pose | Key details |
|-------|------|-------------|
| `run_00` | Right foot forward touching ground, left foot back in push-off, left arm forward, right arm back | Body leans slightly forward; dynamic forward-motion pose |
| `run_01` | Mid-stride transition: feet closer together, body more upright, arms at neutral | Contact frame — both feet near the ground |
| `run_02` | Left foot forward touching ground, right foot back (mirror of 00) | Arms mirrored from frame 00 |
| `run_03` | Mid-stride transition returning to start (mirror of 01) | Passing frame — same as 01 but opposite leg leading |

**Consistency rule**: Head height should bob slightly (±1-2 px). Body center-of-mass stays on a smooth sine-like path across all 4 frames.

---

### Attack (2 frames, ~6 FPS play-once)

**Purpose**: Melee/ranged attack action.

| Frame | Pose | Key details |
|-------|------|-------------|
| `attack_00` | Wind-up: weapon pulled back behind body, body coiled, weight shifting back | Clear anticipation pose — player can read the incoming strike |
| `attack_01` | Follow-through: weapon extended fully forward/down, body stretched in direction of attack | Weapon should extend beyond normal idle silhouette |

**Class variations**:
- **Warrior**: Sword/axe overhead then slashing forward-down
- **Mage**: Staff held back, then pointed forward with spell particles at tip
- **Archer**: Bow drawn back, then released with arm extended
- **Thief**: Dagger pulled to side, then thrust forward in quick stab

---

### Jump (1 frame, displayed while ascending)

| Frame | Pose | Key details |
|-------|------|-------------|
| `jump_00` | Body lifted, knees tucked slightly, arms raised or out to sides | Upward arc energy — character clearly in the air going up |

---

### Fall (1 frame, displayed while descending)

| Frame | Pose | Key details |
|-------|------|-------------|
| `fall_00` | Body extended, legs dangling or slightly spread, arms out to sides or up | Downward drift energy — distinct from jump pose; more passive/gravity-affected |

---

### Hurt (1 frame, flashed on damage)

| Frame | Pose | Key details |
|-------|------|-------------|
| `hurt_00` | Body recoiled backward, one eye squinted/closed, slight backward lean | Clear pain/flinch read — body should be displaced from center compared to idle |

---

### Death (1 frame, displayed on defeat)

| Frame | Pose | Key details |
|-------|------|-------------|
| `death_00` | Collapsed on ground, lying flat, or ghost/spirit departing upward from body | X-eyes or closed eyes; weapon dropped or beside body |

**Style options**:
- MapleStory classic: character tombstone or ghost floating up
- Simple: character lying flat with X-eyes
- Either works; maintain consistency within the project

---

### Climb (2 frames, ~4 FPS loop)

**Purpose**: Rope/ladder climbing.

| Frame | Pose | Key details |
|-------|------|-------------|
| `climb_00` | Facing camera (front view), right hand high, left hand low, right leg up, left leg down | Body oriented vertically, not the usual side-view |
| `climb_01` | Alternate: left hand high, right hand low, left leg up, right leg down | Mirror of climb_00 on the other side |

---

## Monster Animation (6 frames)

### Idle (2 frames, ~3-4 FPS loop)

| Frame | Pose | Key details |
|-------|------|-------------|
| `idle_00` | Default resting pose, facing right | Species-specific idle: slimes sit, boars stand, mushrooms stand |
| `idle_01` | Subtle variation: slight squish/bounce/blink | Maintain same ground contact point; only body deformation |

---

### Hop / Walk (2 frames, ~6 FPS loop)

| Frame | Pose | Key details |
|-------|------|-------------|
| `hop_00` | Compressed/crouched, about to launch, body squished shorter | Ground contact frame — wider and shorter than idle |
| `hop_01` | Extended upward in mid-hop, body stretched | Air frame — taller and narrower than idle |

**For legged monsters**: Replace `hop` with `walk` using the same run-cycle logic as players but simpler (2 frames instead of 4).

---

### Hurt (1 frame)

| Frame | Pose | Key details |
|-------|------|-------------|
| `hurt_00` | Knocked back/recoiled, body tilted, pained expression | May include flash/white tint as game-side overlay |

---

### Death (1 frame)

| Frame | Pose | Key details |
|-------|------|-------------|
| `death_00` | Flattened / exploding / dissolving / fading | For slimes: splattered flat; for mushrooms: toppled; for boars: collapsed |

**Post-death VFX**: The `effects/death_poof_*` sequence can overlay on top for a uniform death effect across all monsters.

---

## Effect / VFX Sequences (variable frame count)

### General Principles

- Effects play once (not looping) unless noted
- Frame 00 is always the initiating/emerging state
- Final frame is always the dissipating/fading state
- Mid frames are the peak intensity
- Use bright, saturated colors that contrast with the green chroma key background

### Standard Timings

| Effect | Frames | Playback FPS | Total duration |
|--------|--------|-------------|----------------|
| Slash | 3 | 12 | ~0.25s |
| Hit Spark | 2 | 12 | ~0.17s |
| Level Up | 3 | 8 | ~0.38s |
| Portal | 4 | 6 (loop) | looping ~0.67s |
| Death Poof | 3 | 10 | ~0.3s |
| Item Pickup | 2-3 | 10 | ~0.2-0.3s |
| Skill VFX | 3-5 | 10-12 | ~0.25-0.5s |
