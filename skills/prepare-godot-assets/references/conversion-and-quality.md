# Conversion and Quality Gates

Use this reference to create canonical derivatives without mistaking successful
conversion for production quality.

## Conversion Rules

- Preserve the original file and hash. Write one derivative into staging and
  record the tool, relevant settings, and output hash.
- Decode before accepting. A matching magic header is not proof that the complete
  file is valid.
- Convert once from the highest-quality available source. Avoid repeated JPEG,
  MP3, or Ogg transcodes.
- Never change only an extension. Never overwrite a different destination.
- Remove unnecessary metadata when it creates privacy, size, orientation, or
  importer issues, but retain provenance in the asset sidecar.
- Prefer deterministic settings and tool versions. Re-audit every derivative.

The bundled `materialize_asset_plan.py` supports guarded copies, raster-to-PNG,
audio-to-WAV, and audio-to-Ogg. It intentionally does not automate decisions that
need content inspection, such as sprite slicing, background removal, atlas
packing, loop repair, or 3D conversion.

## Image and Sprite Gates

- Decode every image and inspect at 100% plus intended in-game scale.
- Confirm width, height, color mode, alpha behavior, orientation, and absence of
  corrupt rows or unexpected embedded thumbnails.
- For pixel art, preserve integer pixels, disable smoothing during transforms,
  align frames to one canvas/pivot, and test nearest filtering. Reject mixed pixel
  densities within one animation set unless intentional.
- For animation frames, verify ordered numbering, equal canvas dimensions,
  consistent subject registration, no missing/duplicate frames, intended FPS,
  and loop continuity.
- For spritesheets, record cell size, margins, spacing, frame count/order, pivot,
  and whether the sheet includes unused cells. Slice only with verified geometry.
- For tilesets, verify tile size, atlas spacing, edge continuity, transparency,
  terrain variants, collision intent, and camera-zoom seams.
- For UI and nine-patch assets, verify stretch margins, readable target sizes,
  high-DPI strategy, and state completeness.
- For texture maps, keep albedo, normal, roughness, metallic, emission, height,
  and packed-channel roles explicit. Do not apply color transforms to data maps.

## Audio Gates

- Decode or probe every file. Record duration, channels, sample rate, bit depth or
  codec, and unexpected silence.
- Listen for clipping, noise, truncated tails, clicks, inconsistent loudness, and
  loop discontinuities. Waveform statistics alone are insufficient.
- Keep mono/stereo intentional. Do not blindly convert music to mono or short
  spatial effects to stereo.
- Trim only verified unwanted silence. Preserve designed pre-roll and reverb tails.
- Use one delivery encode from a lossless master when possible. If only a lossy
  source exists, prefer keeping a Godot-supported source over lossy transcoding.

## 3D Gates

- Open untrusted source files in an isolated conversion workflow, not the target
  project. Disable or avoid embedded scripts and automatic addon execution.
- Convert to glTF 2.0/GLB with a pinned Blender version when direct import depends
  on external tooling. Keep a conversion log.
- Verify all texture URIs before and after conversion. Pack or copy dependencies
  deliberately; do not accept magenta/default materials as success.
- Inspect transforms, units, axes, origin, object names, triangulation, normals,
  tangents, UVs, material count, texture color spaces, skeleton, weights, clips,
  root motion, blend shapes, LODs, and collider requirements.
- Instantiate the result in Godot under the target renderer. Compare it visually
  with the source application or trusted reference.

## Fonts, SVG, Archives, and Native Resources

- Verify that font licensing permits game embedding. Test required languages,
  shaping, fallback, variable axes, and target-platform rendering.
- Inspect SVG text for external resources, scripts, filters, embedded fonts/data,
  and pathological dimensions. Rasterize when fidelity or security is uncertain.
- Extract archives into a separate read-only intake directory, reject traversal
  and symlink entries, then restart the audit on extracted contents.
- Review Godot scenes/resources/scripts/shaders as code. Resolve stale UIDs and
  paths only after understanding behavior and ownership.

## Acceptance Gates

An asset can advance from staging only when all applicable gates pass:

1. Integrity: hash recorded, full decode succeeds, extension matches content.
2. Safety: no unresolved active content, traversal, external dependency, or
   executable risk.
3. Structure: normalized collision-free path and stable ID assigned.
4. Quality: content-specific checks pass at intended game settings.
5. Library compatibility: use a documented Godot-supported delivery format and
   resolve all file dependencies. Record target-project import results separately
   when the user requested that optional integration check.
6. Runtime: verify representative scene behavior only when a target project and
   runtime validation are in scope.
7. Rights: license/provenance status is explicit, even when still unknown.
8. Retrieval: purpose-revealing filename, description, category, tags,
   recommended uses, relationships, and portable `library_path` are sufficient
   for an Agent to select and locate the asset without guessing.
