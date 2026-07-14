# Godot 4 Asset Compatibility

Use this reference to choose portable delivery formats and interpret optional
import results from an existing user-supplied project. Do not create a Godot
project as the asset-library deliverable. A target executable is authoritative
only for that project's compatibility because importer behavior varies by Godot
version, platform, build, and installed extensions.

## Canonical Matrix

| Asset class | Preferred delivery | Usually importable | Convert or review |
| --- | --- | --- | --- |
| Pixel art, sprites, UI, masks | PNG | PNG, WebP, BMP, TGA | GIF, TIFF, PSD, Aseprite; verify alpha and frames |
| Photos, opaque backgrounds | JPEG or WebP | JPEG, WebP, PNG | CMYK JPEG, huge source masters |
| Vector UI | SVG when simple; otherwise PNG | SVG rasterized by importer | External fonts, filters, scripts, linked resources |
| HDR/environment textures | EXR or HDR | EXR, HDR, DDS/KTX depending on use | Platform GPU formats and KTX2 need target testing |
| Short sound effects | WAV | WAV | FLAC/AAC/M4A; normalize only when required |
| Music and ambience | Ogg Vorbis | OGG, MP3 | Lossy-to-lossy conversion, loop metadata |
| Built-in video | Ogg Theora (`.ogv`) | OGV | MP4/WebM/MOV generally need conversion or a plugin |
| 3D scenes | glTF 2.0 (`.glb` or `.gltf`) | GLB, glTF, OBJ | FBX/Blend/DAE are version/toolchain dependent |
| Runtime fonts | TTF/OTF; test WOFF/WOFF2 | TTF, OTF, WOFF, WOFF2 | Variable/color fonts and licensing restrictions |
| Godot-native content | TSCN/TRES after review | TSCN, SCN, TRES, RES | Scripts, shaders, editor plugins, stale UIDs |

## Format Decisions

### Images

- Prefer PNG for pixel-perfect edges, transparency, normal maps, masks, UI, and
  sources that must remain lossless.
- Use JPEG only for opaque continuous-tone content. Reject or convert CMYK files
  that the target importer cannot decode.
- Use WebP when its target-platform import and quality tradeoff were verified.
- Treat SVG as active XML-like input. Inspect for scripts, remote references,
  embedded data, filters, external fonts, unsupported features, and extreme
  dimensions before importing. Godot rasterizes SVG; compare the imported result
  at actual UI scale.
- Keep color-space intent explicit. Albedo/UI usually use sRGB; data textures,
  normal maps, masks, and packed channels must not be treated as color data.
- Set pixel-art filtering, mipmaps, repeat, and compression intentionally in the
  target project. Import success does not prove correct sampling.

### Audio

- Prefer WAV for short effects that need low latency or exact samples. Avoid
  shipping unnecessarily high sample rates, channels, or long PCM tracks.
- Prefer Ogg Vorbis for longer music and ambience. Keep a lossless master when
  available and encode a single delivery derivative.
- Preserve documented loop start/end behavior. Listen through the loop boundary;
  metadata can be lost during conversion.
- Check channel count, duration, sample rate, clipped peaks, DC offset, leading
  silence, and unexpected embedded artwork or metadata.

### 3D

- Prefer glTF 2.0. Use GLB for a self-contained handoff; use glTF plus external
  files when diffability or texture replacement matters.
- Inspect scene scale, axis orientation, transforms, material slots, texture
  resolution, UVs, normals/tangents, skeleton hierarchy, skin weights, animation
  names/ranges, root motion, blend shapes, and collider expectations.
- Treat `.blend` direct import as conditional on the configured Blender path and
  matching exporter behavior. Treat FBX import as version-dependent. Convert to
  glTF/GLB in a controlled Blender pipeline when reproducibility matters.
- Keep a model bundle together until every URI and material reference resolves.
  Do not flatten a directory merely to satisfy a cosmetic taxonomy.

### Godot-Native and Active Content

- Never trust downloaded `.gd`, `.gdshader`, `.tscn`, `.tres`, `.res`, addons,
  GDExtensions, DLLs, shared libraries, or editor plugins as passive media.
- Read text resources and scripts before opening the pack in an editor. Binary
  native resources require a trusted provenance or isolation strategy.
- Do not import downloaded executables. Do not follow symlinks out of the source.

## Import State

- Run import verification only when the user supplied an existing target project
  and requested compatibility testing. Keep the standalone library free of Godot
  project files, `.godot/`, `.import`, `.uid`, and temporary test scenes.
- Let the target Godot version create adjacent `.import` metadata and the
  `.godot/imported/` cache. Never copy these from the downloaded dump or hand-edit
  them as a substitute for a real import.
- Preserve project-owned import settings according to repository convention after
  validation, but regenerate stale cache data when the target version changes.
- Treat `valid=false`, missing external-resource sidecars, importer error output,
  broken dependency paths, or placeholder materials as failures.
- Re-run import verification after renaming, moving, converting, changing import
  settings, upgrading Godot, or changing a model's dependencies.

## Runtime Validation

After headless import, instantiate representative assets in a test scene. Check:

- sprites at intended scale, filter mode, mipmaps, pivots, and animation timing;
- tiles at camera zoom with no seams and correct terrain/atlas coordinates;
- UI at supported DPI and stretch modes;
- audio start latency, loudness, spatial behavior, and seamless loops;
- models under the project renderer with correct materials, scale, skeleton,
  animations, and collision behavior;
- memory and package size on the actual target platform.
