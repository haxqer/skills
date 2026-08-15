#!/usr/bin/env python3
"""Deterministic tests for the spine-animation pipeline.

Modules that need Pillow, numpy, or OpenCV are imported defensively so the suite
still runs on a bare interpreter; their tests skip instead of erroring. Note that
`make_atlas` calls sys.exit() when Pillow is missing, so SystemExit is caught too.
"""

import base64
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent

import build_spine_json
import generate_spine_player
import split_character


def _optional(name):
    try:
        return importlib.import_module(name)
    except (ImportError, SystemExit):
        return None


make_atlas = _optional("make_atlas")
position_parts = _optional("position_parts")
_pil = _optional("PIL.Image")

HAS_ATLAS = make_atlas is not None
HAS_PIL = _pil is not None
HAS_CV = position_parts is not None

FULL_SKELETON = {
    "root", "hip", "torso", "neck", "head",
    "left-upper-arm", "left-lower-arm", "right-upper-arm", "right-lower-arm",
    "left-upper-leg", "left-lower-leg", "left-foot",
    "right-upper-leg", "right-lower-leg", "right-foot",
}


def minimal_config(**overrides):
    config = {
        "skeleton": {"name": "test", "width": 400, "height": 600},
        "bones": [
            {"name": "root"},
            {"name": "hip", "parent": "root", "x": 0, "y": 300},
            {"name": "torso", "parent": "hip", "x": 0, "y": 60},
            {"name": "head", "parent": "torso", "x": 0, "y": 90},
        ],
        "slots": [
            {"name": "torso", "bone": "torso", "attachment": "torso"},
            {"name": "head", "bone": "head", "attachment": "head"},
        ],
        "attachments": {
            "torso": {"width": 120, "height": 200},
            "head": {"width": 96, "height": 96},
        },
        "animations": ["idle"],
    }
    config.update(overrides)
    return config


# --------------------------------------------------------------------------- #
# build_spine_json: keyframe helpers
# --------------------------------------------------------------------------- #


class KeyframeTests(unittest.TestCase):
    def test_omits_unset_properties(self) -> None:
        self.assertEqual(
            build_spine_json._kf(0.5, angle=10),
            {"time": 0.5, "angle": 10, "curve": build_spine_json.EASE},
        )

    def test_curve_none_drops_the_curve_key(self) -> None:
        self.assertNotIn("curve", build_spine_json._kf(0, angle=0, curve=None))

    def test_rounding(self) -> None:
        kf = build_spine_json._kf(1 / 3, angle=1 / 3, x=2 / 3, y=-1 / 3)
        self.assertEqual(kf["time"], 0.3333)
        self.assertEqual(kf["angle"], 0.33)
        self.assertEqual(kf["x"], 0.67)
        self.assertEqual(kf["y"], -0.33)

    def test_zero_values_are_kept_not_treated_as_unset(self) -> None:
        kf = build_spine_json._kf(0, angle=0, x=0, y=0)
        self.assertEqual(kf["angle"], 0)
        self.assertEqual(kf["x"], 0)
        self.assertEqual(kf["y"], 0)

    def test_has_is_an_any_of_check(self) -> None:
        self.assertTrue(build_spine_json._has({"head", "hip"}, "missing", "hip"))
        self.assertFalse(build_spine_json._has({"head"}, "hip", "torso"))


# --------------------------------------------------------------------------- #
# build_spine_json: animation presets
# --------------------------------------------------------------------------- #


class PresetTests(unittest.TestCase):
    def test_every_preset_is_registered_and_callable(self) -> None:
        self.assertEqual(
            set(build_spine_json.PRESETS),
            {"idle", "walk", "run", "wave", "jump", "attack"},
        )

    def test_presets_produce_timelines_for_a_full_skeleton(self) -> None:
        for name, generator in build_spine_json.PRESETS.items():
            with self.subTest(preset=name):
                self.assertTrue(generator(FULL_SKELETON).get("bones"))

    def test_presets_are_empty_for_an_unrelated_skeleton(self) -> None:
        for name, generator in build_spine_json.PRESETS.items():
            with self.subTest(preset=name):
                self.assertEqual(generator({"tail", "wing"}), {})

    def test_presets_only_touch_bones_that_exist(self) -> None:
        partial = {"hip", "torso", "head"}
        for name, generator in build_spine_json.PRESETS.items():
            with self.subTest(preset=name):
                for bone in generator(partial).get("bones", {}):
                    self.assertIn(bone, partial)

    def test_keyframe_times_are_non_decreasing(self) -> None:
        for name, generator in build_spine_json.PRESETS.items():
            for bone, timelines in generator(FULL_SKELETON).get("bones", {}).items():
                for timeline, keys in timelines.items():
                    with self.subTest(preset=name, bone=bone, timeline=timeline):
                        times = [key["time"] for key in keys]
                        self.assertEqual(times, sorted(times))

    def test_timelines_close_the_loop(self) -> None:
        """references/spine-json-format.md: the last key must equal the first."""
        for name, generator in build_spine_json.PRESETS.items():
            for bone, timelines in generator(FULL_SKELETON).get("bones", {}).items():
                for timeline, keys in timelines.items():
                    first, last = keys[0], keys[-1]
                    for prop in ("angle", "x", "y"):
                        with self.subTest(preset=name, bone=bone, prop=prop):
                            self.assertEqual(first.get(prop, 0), last.get(prop, 0))

    def test_first_keyframe_has_no_curve(self) -> None:
        for name, generator in build_spine_json.PRESETS.items():
            for bone, timelines in generator(FULL_SKELETON).get("bones", {}).items():
                for timeline, keys in timelines.items():
                    with self.subTest(preset=name, bone=bone, timeline=timeline):
                        self.assertNotIn("curve", keys[0])

    def test_curves_are_four_element_beziers(self) -> None:
        for name, generator in build_spine_json.PRESETS.items():
            for timelines in generator(FULL_SKELETON).get("bones", {}).values():
                for keys in timelines.values():
                    for key in keys:
                        if "curve" in key:
                            with self.subTest(preset=name):
                                self.assertEqual(len(key["curve"]), 4)

    def test_rotate_uses_angle_and_translate_uses_xy(self) -> None:
        for name, generator in build_spine_json.PRESETS.items():
            for bone, timelines in generator(FULL_SKELETON).get("bones", {}).items():
                for timeline, keys in timelines.items():
                    with self.subTest(preset=name, bone=bone, timeline=timeline):
                        for key in keys:
                            if timeline == "rotate":
                                self.assertNotIn("x", key)
                                self.assertNotIn("y", key)
                            elif timeline == "translate":
                                self.assertNotIn("angle", key)


# --------------------------------------------------------------------------- #
# build_spine_json: skeleton assembly
# --------------------------------------------------------------------------- #


class SkeletonTests(unittest.TestCase):
    def test_top_level_shape(self) -> None:
        spine = build_spine_json.build_spine_json(minimal_config())
        self.assertEqual(
            set(spine), {"skeleton", "bones", "slots", "skins", "animations"}
        )

    def test_skeleton_metadata(self) -> None:
        skeleton = build_spine_json.build_spine_json(minimal_config())["skeleton"]
        self.assertEqual(skeleton["spine"], "4.2.0")
        self.assertEqual(skeleton["width"], 400)
        self.assertEqual(skeleton["height"], 600)
        self.assertEqual(skeleton["x"], -200)
        self.assertEqual(skeleton["y"], 0)
        self.assertEqual(skeleton["images"], "./images/")

    def test_skeleton_defaults_when_metadata_is_absent(self) -> None:
        config = minimal_config()
        del config["skeleton"]
        skeleton = build_spine_json.build_spine_json(config)["skeleton"]
        self.assertEqual((skeleton["width"], skeleton["height"]), (400, 600))
        self.assertEqual(skeleton["x"], -200)

    def test_hash_is_stable_for_the_same_config(self) -> None:
        first = build_spine_json.build_spine_json(minimal_config())["skeleton"]["hash"]
        second = build_spine_json.build_spine_json(minimal_config())["skeleton"]["hash"]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 20)

    def test_hash_changes_with_the_config(self) -> None:
        base = build_spine_json.build_spine_json(minimal_config())["skeleton"]["hash"]
        changed = minimal_config()
        changed["bones"][1]["y"] = 999
        self.assertNotEqual(
            base, build_spine_json.build_spine_json(changed)["skeleton"]["hash"]
        )

    def test_hash_ignores_key_ordering(self) -> None:
        config = minimal_config()
        reordered = {key: config[key] for key in reversed(list(config))}
        self.assertEqual(
            build_spine_json.build_spine_json(config)["skeleton"]["hash"],
            build_spine_json.build_spine_json(reordered)["skeleton"]["hash"],
        )

    def test_bones_and_slots_pass_through_in_order(self) -> None:
        config = minimal_config()
        spine = build_spine_json.build_spine_json(config)
        self.assertEqual(spine["bones"], config["bones"])
        self.assertEqual([s["name"] for s in spine["slots"]], ["torso", "head"])

    def test_slot_order_is_draw_order(self) -> None:
        """references/spine-json-format.md: slot array order is the z-order."""
        config = minimal_config()
        config["slots"] = list(reversed(config["slots"]))
        spine = build_spine_json.build_spine_json(config)
        self.assertEqual([s["name"] for s in spine["slots"]], ["head", "torso"])

    def test_default_skin_nests_slot_then_attachment(self) -> None:
        spine = build_spine_json.build_spine_json(minimal_config())
        skin = spine["skins"][0]
        self.assertEqual(skin["name"], "default")
        self.assertEqual(
            skin["attachments"]["torso"], {"torso": {"width": 120, "height": 200}}
        )

    def test_slot_without_explicit_attachment_uses_its_own_name(self) -> None:
        config = minimal_config()
        config["slots"] = [{"name": "head", "bone": "head"}]
        skin = build_spine_json.build_spine_json(config)["skins"][0]
        self.assertIn("head", skin["attachments"])

    def test_slot_with_no_matching_attachment_is_omitted_from_the_skin(self) -> None:
        config = minimal_config()
        config["slots"].append({"name": "cape", "bone": "torso", "attachment": "cape"})
        skin = build_spine_json.build_spine_json(config)["skins"][0]
        self.assertNotIn("cape", skin["attachments"])
        self.assertEqual(len(skin["attachments"]), 2)

    def test_renamed_attachment_is_keyed_by_the_attachment_name(self) -> None:
        config = minimal_config()
        config["slots"] = [{"name": "front-arm", "bone": "torso", "attachment": "arm"}]
        config["attachments"] = {"arm": {"width": 30, "height": 80}}
        skin = build_spine_json.build_spine_json(config)["skins"][0]
        self.assertEqual(skin["attachments"]["front-arm"], {"arm": {"width": 30, "height": 80}})

    def test_requested_presets_are_generated(self) -> None:
        config = minimal_config(animations=["idle", "walk"])
        spine = build_spine_json.build_spine_json(config)
        self.assertEqual(set(spine["animations"]), {"idle", "walk"})

    def test_idle_is_the_default_animation(self) -> None:
        config = minimal_config()
        del config["animations"]
        self.assertEqual(
            set(build_spine_json.build_spine_json(config)["animations"]), {"idle"}
        )

    def test_unknown_preset_is_skipped_not_fatal(self) -> None:
        config = minimal_config(animations=["idle", "moonwalk"])
        with mock.patch("sys.stdout"):
            spine = build_spine_json.build_spine_json(config)
        self.assertEqual(set(spine["animations"]), {"idle"})

    def test_preset_with_no_matching_bones_is_not_emitted(self) -> None:
        config = minimal_config(animations=["walk"])
        config["bones"] = [{"name": "root"}, {"name": "tail", "parent": "root"}]
        self.assertEqual(build_spine_json.build_spine_json(config)["animations"], {})

    def test_custom_animations_are_merged(self) -> None:
        custom = {"bones": {"head": {"rotate": [{"time": 0, "angle": 0}]}}}
        config = minimal_config(custom_animations={"nod": custom})
        spine = build_spine_json.build_spine_json(config)
        self.assertEqual(set(spine["animations"]), {"idle", "nod"})
        self.assertEqual(spine["animations"]["nod"], custom)

    def test_custom_animation_overrides_a_preset_of_the_same_name(self) -> None:
        custom = {"bones": {"head": {"rotate": [{"time": 0, "angle": 42}]}}}
        config = minimal_config(custom_animations={"idle": custom})
        spine = build_spine_json.build_spine_json(config)
        self.assertEqual(spine["animations"]["idle"], custom)

    def test_output_is_json_serialisable(self) -> None:
        config = minimal_config(animations=list(build_spine_json.PRESETS))
        json.dumps(build_spine_json.build_spine_json(config))


class BuilderCliTests(unittest.TestCase):
    def test_cli_writes_a_loadable_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            output_path = Path(directory) / "skeleton.json"
            config_path.write_text(json.dumps(minimal_config(animations=["idle", "walk"])))
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_spine_json.py"),
                 "--config", str(config_path), "--output", str(output_path)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            spine = json.loads(output_path.read_text())
            self.assertEqual(spine["skeleton"]["spine"], "4.2.0")
            self.assertEqual(set(spine["animations"]), {"idle", "walk"})


# --------------------------------------------------------------------------- #
# make_atlas
# --------------------------------------------------------------------------- #


class _FakeImage:
    """Stand-in for a PIL image: pack() only reads .width and .height."""

    def __init__(self, width, height):
        self.width = width
        self.height = height


@unittest.skipUnless(HAS_ATLAS, "make_atlas requires Pillow")
class NextPow2Tests(unittest.TestCase):
    def test_exact_powers_are_unchanged(self) -> None:
        for value in (1, 2, 4, 8, 512, 1024):
            self.assertEqual(make_atlas.next_pow2(value), value)

    def test_rounds_up(self) -> None:
        self.assertEqual(make_atlas.next_pow2(3), 4)
        self.assertEqual(make_atlas.next_pow2(100), 128)
        self.assertEqual(make_atlas.next_pow2(513), 1024)

    def test_degenerate_input_stays_positive(self) -> None:
        self.assertEqual(make_atlas.next_pow2(0), 1)
        self.assertEqual(make_atlas.next_pow2(1), 1)


@unittest.skipUnless(HAS_ATLAS, "make_atlas requires Pillow")
class PackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.images = {
            "torso": _FakeImage(120, 200),
            "head": _FakeImage(96, 96),
            "arm": _FakeImage(30, 80),
            "foot": _FakeImage(40, 24),
        }

    def test_every_image_is_placed_at_its_own_size(self) -> None:
        _, _, placements = make_atlas.pack(self.images)
        self.assertEqual(set(placements), set(self.images))
        for name, (_, _, width, height) in placements.items():
            self.assertEqual((width, height), (self.images[name].width, self.images[name].height))

    def test_atlas_dimensions_are_powers_of_two(self) -> None:
        width, height, _ = make_atlas.pack(self.images)
        for value in (width, height):
            self.assertEqual(value & (value - 1), 0)

    def test_regions_do_not_overlap(self) -> None:
        _, _, placements = make_atlas.pack(self.images, padding=2)
        boxes = list(placements.values())
        for i, (ax, ay, aw, ah) in enumerate(boxes):
            for bx, by, bw, bh in boxes[i + 1:]:
                overlaps = ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah
                self.assertFalse(overlaps, f"{(ax, ay, aw, ah)} overlaps {(bx, by, bw, bh)}")

    def test_regions_fit_inside_the_atlas(self) -> None:
        width, height, placements = make_atlas.pack(self.images)
        for name, (x, y, w, h) in placements.items():
            with self.subTest(region=name):
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, width)
                self.assertLessEqual(y + h, height)

    def test_padding_offsets_the_first_region(self) -> None:
        _, _, placements = make_atlas.pack(self.images, padding=8)
        self.assertEqual(placements["torso"][:2], (8, 8))

    def test_regions_are_separated_by_at_least_the_padding(self) -> None:
        """Touching regions are not enough: filtering bleeds across a zero gap."""
        for padding in (2, 8):
            _, _, placements = make_atlas.pack(self.images, padding=padding)
            boxes = list(placements.items())
            for i, (a_name, (ax, ay, aw, ah)) in enumerate(boxes):
                for b_name, (bx, by, bw, bh) in boxes[i + 1:]:
                    gap_x = max(ax - (bx + bw), bx - (ax + aw))
                    gap_y = max(ay - (by + bh), by - (ay + ah))
                    with self.subTest(padding=padding, pair=(a_name, b_name)):
                        self.assertGreaterEqual(
                            max(gap_x, gap_y), padding,
                            f"{a_name} and {b_name} are separated by "
                            f"{max(gap_x, gap_y)}px, need {padding}px",
                        )

    def test_regions_keep_the_padding_from_the_page_edges(self) -> None:
        for padding in (2, 8):
            width, height, placements = make_atlas.pack(self.images, padding=padding)
            for name, (x, y, w, h) in placements.items():
                with self.subTest(padding=padding, region=name):
                    self.assertGreaterEqual(x, padding)
                    self.assertGreaterEqual(y, padding)
                    self.assertLessEqual(x + w + padding, width)
                    self.assertLessEqual(y + h + padding, height)

    def test_tallest_image_is_placed_first(self) -> None:
        _, _, placements = make_atlas.pack(self.images)
        first = min(placements.items(), key=lambda item: (item[1][1], item[1][0]))
        self.assertEqual(first[0], "torso")

    def test_single_image(self) -> None:
        width, height, placements = make_atlas.pack({"solo": _FakeImage(64, 64)})
        self.assertEqual(placements["solo"], (2, 2, 64, 64))
        self.assertLessEqual(66, width)
        self.assertLessEqual(66, height)


@unittest.skipUnless(HAS_PIL, "atlas CLI test requires Pillow")
class AtlasFileFormatTests(unittest.TestCase):
    """The .atlas text layout is contractual; references/spine-json-format.md pins it."""

    def _build(self, directory, sizes, name="skeleton", padding=2):
        from PIL import Image

        parts = Path(directory) / "parts"
        parts.mkdir()
        for part_name, (width, height) in sizes.items():
            Image.new("RGBA", (width, height), (255, 0, 0, 255)).save(parts / f"{part_name}.png")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "make_atlas.py"), "--parts", str(parts),
             "--output", directory, "--name", name, "--padding", str(padding)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return (Path(directory) / f"{name}.atlas").read_text()

    def test_header_and_region_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = self._build(directory, {"torso": (120, 200), "head": (96, 96)})
            lines = text.splitlines()
            self.assertEqual(lines[0], "skeleton.png")
            self.assertRegex(lines[1], r"^size: \d+,\d+$")
            self.assertEqual(lines[2], "format: RGBA8888")
            self.assertEqual(lines[3], "filter: Linear,Linear")
            self.assertEqual(lines[4], "repeat: none")
            self.assertIn("  rotate: false", lines)
            self.assertIn("  size: 120, 200", lines)
            self.assertIn("  orig: 120, 200", lines)
            self.assertIn("  offset: 0, 0", lines)
            self.assertIn("  index: -1", lines)

    def test_every_region_has_a_complete_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = self._build(directory, {"torso": (120, 200), "head": (96, 96), "arm": (30, 80)})
            for region in ("torso", "head", "arm"):
                self.assertIn(f"\n{region}\n  rotate: false\n", text)
            self.assertEqual(text.count("  rotate: false"), 3)
            self.assertTrue(text.endswith("\n"))

    def test_declared_page_size_covers_every_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = self._build(directory, {"a": (100, 40), "b": (60, 90), "c": (20, 20)})
            page_w, page_h = (int(v) for v in re.search(r"size: (\d+),(\d+)", text).groups())
            for x, y, w, h in re.findall(
                r"xy: (\d+), (\d+)\n  size: (\d+), (\d+)", text
            ):
                self.assertLessEqual(int(x) + int(w), page_w)
                self.assertLessEqual(int(y) + int(h), page_h)

    def test_empty_parts_directory_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parts = Path(directory) / "empty"
            parts.mkdir()
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "make_atlas.py"),
                 "--parts", str(parts), "--output", directory],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)


# --------------------------------------------------------------------------- #
# split_character: pure helpers only, no network paths
# --------------------------------------------------------------------------- #


class ReadEnvTests(unittest.TestCase):
    def _write(self, directory, text):
        path = Path(directory) / ".env"
        path.write_text(text, encoding="utf-8")
        return path

    def test_parses_simple_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {}, clear=True):
            split_character._read_env(self._write(directory, "FOO=bar\nBAZ=qux\n"))
            self.assertEqual(os.environ["FOO"], "bar")
            self.assertEqual(os.environ["BAZ"], "qux")

    def test_does_not_overwrite_an_existing_variable(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"FOO": "original"}, clear=True
        ):
            split_character._read_env(self._write(directory, "FOO=from-file\n"))
            self.assertEqual(os.environ["FOO"], "original")

    def test_strips_quotes_and_surrounding_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {}, clear=True):
            split_character._read_env(
                self._write(directory, "  A = 'single'  \nB=\"double\"\n")
            )
            self.assertEqual(os.environ["A"], "single")
            self.assertEqual(os.environ["B"], "double")

    def test_skips_comments_blanks_and_malformed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {}, clear=True):
            split_character._read_env(
                self._write(directory, "# comment\n\nNOEQUALS\nGOOD=1\n")
            )
            self.assertEqual(os.environ["GOOD"], "1")
            self.assertNotIn("NOEQUALS", os.environ)
            self.assertNotIn("# comment", os.environ)

    def test_keeps_equals_signs_inside_the_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {}, clear=True):
            split_character._read_env(self._write(directory, "URL=https://x/y?a=1&b=2\n"))
            self.assertEqual(os.environ["URL"], "https://x/y?a=1&b=2")


class BackendResolutionTests(unittest.TestCase):
    def test_explicit_backend_wins_over_every_hint(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_BASE_URL": "http://x"}, clear=True):
            self.assertEqual(
                split_character.resolve_backend("gemini", "gpt-image-1", "http://x"), "gemini"
            )

    def test_gemini_model_prefixes(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            for model in ("gemini-2.5-flash-image", "Gemini-Pro", "imagen-3"):
                with self.subTest(model=model):
                    self.assertEqual(split_character.resolve_backend("auto", model, None), "gemini")

    def test_openai_model_prefixes(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            for model in ("gpt-image-1", "DALL-E-3", "dalle-2"):
                with self.subTest(model=model):
                    self.assertEqual(split_character.resolve_backend("auto", model, None), "openai")

    def test_base_url_argument_implies_openai(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                split_character.resolve_backend("auto", None, "https://proxy/v1"), "openai"
            )

    def test_base_url_environment_implies_openai(self) -> None:
        for variable in ("OPENAI_BASE_URL", "IMAGE_API_BASE_URL"):
            with self.subTest(variable=variable):
                with mock.patch.dict(os.environ, {variable: "https://proxy/v1"}, clear=True):
                    self.assertEqual(split_character.resolve_backend("auto", None, None), "openai")

    def test_default_is_gemini(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(split_character.resolve_backend("auto", None, None), "gemini")
            self.assertEqual(split_character.resolve_backend("", None, None), "gemini")

    def test_unknown_model_falls_back_to_gemini(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(split_character.resolve_backend("auto", "llama-vision", None), "gemini")


class UrlAndModelResolutionTests(unittest.TestCase):
    def test_base_url_precedence_and_trailing_slash(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_BASE_URL": "https://env/v1"}, clear=True):
            self.assertEqual(split_character.resolve_base_url("https://arg/v1/"), "https://arg/v1")
            self.assertEqual(split_character.resolve_base_url(None), "https://env/v1")

    def test_base_url_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                split_character.resolve_base_url(None), split_character.DEFAULT_OPENAI_BASE
            )

    def test_default_model_per_backend(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                split_character.default_model_for("gemini"), split_character.DEFAULT_GEMINI_MODEL
            )
            self.assertEqual(
                split_character.default_model_for("openai"), split_character.DEFAULT_OPENAI_MODEL
            )

    def test_image_model_environment_overrides_the_default(self) -> None:
        with mock.patch.dict(os.environ, {"IMAGE_MODEL": "custom-model"}, clear=True):
            self.assertEqual(split_character.default_model_for("gemini"), "custom-model")


class ApiKeyResolutionTests(unittest.TestCase):
    def test_explicit_key_wins(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "env"}, clear=True):
            self.assertEqual(split_character.resolve_api_key("gemini", "explicit"), "explicit")

    def test_gemini_key_fallback_chain(self) -> None:
        for variable in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "IMAGE_API_KEY"):
            with self.subTest(variable=variable):
                with mock.patch.dict(os.environ, {variable: "k"}, clear=True):
                    self.assertEqual(split_character.resolve_api_key("gemini", None), "k")

    def test_openai_key_fallback_chain(self) -> None:
        for variable in ("OPENAI_API_KEY", "IMAGE_API_KEY"):
            with self.subTest(variable=variable):
                with mock.patch.dict(os.environ, {variable: "k"}, clear=True):
                    self.assertEqual(split_character.resolve_api_key("openai", None), "k")

    def test_missing_key_exits_rather_than_calling_the_api(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("sys.stderr"):
            for backend in ("gemini", "openai"):
                with self.subTest(backend=backend), self.assertRaises(SystemExit):
                    split_character.resolve_api_key(backend, None)

    def test_gemini_key_does_not_leak_into_the_openai_path(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "g"}, clear=True), mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                split_character.resolve_api_key("openai", None)


# --------------------------------------------------------------------------- #
# generate_spine_player
# --------------------------------------------------------------------------- #


class AtlasImageDiscoveryTests(unittest.TestCase):
    def _atlas(self, directory, text, pages=()):
        path = Path(directory) / "skeleton.atlas"
        path.write_text(text)
        for page in pages:
            (Path(directory) / page).write_bytes(b"\x89PNG\r\n")
        return path

    def test_finds_the_page_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            atlas = self._atlas(
                directory, "skeleton.png\nsize: 512,512\nformat: RGBA8888\n", ["skeleton.png"]
            )
            found = generate_spine_player.find_atlas_images(atlas)
            self.assertEqual([name for name, _ in found], ["skeleton.png"])

    def test_finds_multiple_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            atlas = self._atlas(
                directory,
                "page1.png\nsize: 512,512\nformat: RGBA8888\n"
                "torso\n  rotate: false\n  xy: 2, 2\n"
                "page2.png\nsize: 256,256\nformat: RGBA8888\n",
                ["page1.png", "page2.png"],
            )
            found = generate_spine_player.find_atlas_images(atlas)
            self.assertEqual([name for name, _ in found], ["page1.png", "page2.png"])

    def test_region_names_are_not_mistaken_for_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            atlas = self._atlas(
                directory,
                "skeleton.png\nsize: 512,512\nformat: RGBA8888\n"
                "torso\n  rotate: false\n  xy: 2, 2\n  size: 10, 10\n",
                ["skeleton.png"],
            )
            self.assertEqual(len(generate_spine_player.find_atlas_images(atlas)), 1)

    def test_missing_page_file_is_warned_not_returned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            atlas = self._atlas(directory, "gone.png\nsize: 512,512\n")
            with mock.patch("sys.stdout"):
                self.assertEqual(generate_spine_player.find_atlas_images(atlas), [])


class PlayerHtmlTests(unittest.TestCase):
    def _fixture(self, directory):
        base = Path(directory)
        (base / "skeleton.json").write_text(json.dumps({"skeleton": {"spine": "4.2.0"}}))
        (base / "skeleton.atlas").write_text("skeleton.png\nsize: 64,64\n")
        (base / "skeleton.png").write_bytes(b"\x89PNG\r\n\x1a\nFAKE")
        return base

    def _html(self, directory, **kwargs):
        base = self._fixture(directory)
        kwargs.setdefault("runtime", None)
        return generate_spine_player.generate_html(
            str(base / "skeleton.json"),
            str(base / "skeleton.atlas"),
            [("skeleton.png", str(base / "skeleton.png"))],
            **kwargs,
        )

    def test_assets_are_embedded_as_data_uris(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory)
            for filename, mime in (
                ("skeleton.json", "application/json"),
                ("skeleton.atlas", "application/octet-stream"),
                ("skeleton.png", "image/png"),
            ):
                with self.subTest(asset=filename):
                    self.assertIn(f'"{filename}": "data:{mime};base64,', html)

    def test_embedded_payload_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory)
            payload = re.search(
                r'"skeleton\.json": "data:application/json;base64,([^"]+)"', html
            ).group(1)
            self.assertEqual(
                json.loads(base64.b64decode(payload)), {"skeleton": {"spine": "4.2.0"}}
            )

    def test_no_local_file_paths_leak_into_the_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory)
            self.assertNotIn(directory, html)

    # Only <script src> and <link href> fetch resources; <a href> is a hyperlink.
    RESOURCE_URL = r'<(?:script|link)\b[^>]*?(?:src|href)="(https?://[^"]+)"'

    def test_cdn_mode_links_a_pinned_runtime_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory, runtime=None)
            runtime_urls = re.findall(self.RESOURCE_URL, html)
            self.assertTrue(runtime_urls, "expected a CDN runtime reference")
            for url in runtime_urls:
                self.assertIn(generate_spine_player.RUNTIME_VERSION, url)
                self.assertNotIn("*", url, "the version must be pinned, not a wildcard")

    def test_embedded_runtime_loads_no_external_resources(self) -> None:
        """The whole point: an embedded page must open with no network."""
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory, runtime=("/* js */", "/* css */"))
            self.assertEqual(
                re.findall(self.RESOURCE_URL, html), [],
                "no resource may be fetched over the network",
            )

    def test_embedded_runtime_round_trips(self) -> None:
        js = 'var x = "</script> <!-- <script>";'
        css = ".spine-player { color: red }"
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory, runtime=(js, css))
            for payload, mime, expected in (
                (js, "text/javascript", js), (css, "text/css", css)
            ):
                encoded = re.search(rf'"data:{re.escape(mime)};base64,([^"]+)"', html).group(1)
                self.assertEqual(base64.b64decode(encoded).decode("utf-8"), expected)

    def test_hostile_runtime_content_cannot_break_out_of_the_page(self) -> None:
        """`</script>` inside the runtime must not terminate the document early."""
        js = 'var a = "</script><h1>escaped</h1>";'
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory, runtime=(js, ""))
            self.assertNotIn("<h1>escaped</h1>", html)
            self.assertEqual(html.rstrip().endswith("</html>"), True)

    def test_embedded_runtime_carries_the_license_notice(self) -> None:
        """The Spine Runtimes License requires the notice to travel with a copy."""
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory, runtime=("/* js */", "/* css */"))
            self.assertIn("Spine Runtimes License Agreement", html)
            self.assertIn("Esoteric Software", html)

    def test_cdn_mode_does_not_claim_a_license_it_is_not_shipping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertNotIn(
                "Spine Runtimes License Agreement", self._html(directory, runtime=None)
            )

    def test_selected_animation_and_title_reach_the_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            html = self._html(directory, animation="walk", title="My Preview")
            self.assertIn('animation: "walk"', html)
            self.assertIn("My Preview", html)

    def test_controls_toggle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertIn("showControls: false", self._html(directory, show_controls=False))
            self.assertIn("showControls: true", self._html(directory, show_controls=True))

    def test_default_skin_is_not_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertNotIn("skin:", self._html(directory, skin="default"))
            self.assertIn('skin: "armoured"', self._html(directory, skin="armoured"))


class RuntimeResolutionTests(unittest.TestCase):
    """Every test here must resolve the runtime without touching the network."""

    def test_data_uri_encodes_and_labels_the_payload(self) -> None:
        uri = generate_spine_player.to_data_uri("body { }", "text/css")
        self.assertTrue(uri.startswith("data:text/css;base64,"))
        self.assertEqual(base64.b64decode(uri.split(",", 1)[1]).decode(), "body { }")

    def test_data_uri_survives_non_ascii(self) -> None:
        uri = generate_spine_player.to_data_uri("/* café ✓ */", "text/javascript")
        self.assertEqual(base64.b64decode(uri.split(",", 1)[1]).decode("utf-8"), "/* café ✓ */")

    def test_explicit_local_paths_are_used_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            js = Path(directory) / "p.js"
            css = Path(directory) / "p.css"
            js.write_text("JS-BODY")
            css.write_text("CSS-BODY")
            self.assertEqual(
                generate_spine_player.load_runtime(js_path=str(js), css_path=str(css)),
                ("JS-BODY", "CSS-BODY"),
            )

    def test_one_local_path_without_the_other_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            generate_spine_player.load_runtime(js_path="only.js")
        with self.assertRaises(ValueError):
            generate_spine_player.load_runtime(css_path="only.css")

    def test_cache_directory_follows_xdg_and_the_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": directory}, clear=True):
                path = generate_spine_player.runtime_cache_dir("9.9.9")
            self.assertEqual(path, Path(directory) / "spine-animation" / "spine-player-9.9.9")

    def test_a_populated_cache_is_used_without_downloading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"XDG_CACHE_HOME": directory}, clear=True):
                cache = generate_spine_player.runtime_cache_dir()
                cache.mkdir(parents=True)
                (cache / "spine-player.js").write_text("CACHED-JS")
                (cache / "spine-player.css").write_text("CACHED-CSS")
                with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
                    self.assertEqual(
                        generate_spine_player.load_runtime(), ("CACHED-JS", "CACHED-CSS")
                    )

    def test_an_empty_cache_file_is_not_trusted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache_file = Path(directory) / "spine-player.js"
            cache_file.write_text("")
            with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
                with self.assertRaises(OSError):
                    generate_spine_player.fetch_runtime_asset("https://x/y.js", cache_file)

    def test_a_download_populates_the_cache(self) -> None:
        class FakeResponse:
            def read(self):
                return b"DOWNLOADED"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with tempfile.TemporaryDirectory() as directory:
            cache_file = Path(directory) / "nested" / "spine-player.js"
            with mock.patch("urllib.request.urlopen", return_value=FakeResponse()):
                text = generate_spine_player.fetch_runtime_asset("https://x/y.js", cache_file)
            self.assertEqual(text, "DOWNLOADED")
            self.assertEqual(cache_file.read_text(), "DOWNLOADED")

    def test_runtime_version_is_pinned_not_a_wildcard(self) -> None:
        self.assertRegex(generate_spine_player.RUNTIME_VERSION, r"^\d+\.\d+\.\d+$")


class PlayerCliTests(unittest.TestCase):
    def _assets(self, directory):
        base = Path(directory)
        (base / "skeleton.json").write_text(json.dumps({"skeleton": {"spine": "4.2.0"}}))
        (base / "skeleton.atlas").write_text("skeleton.png\nsize: 64,64\n")
        (base / "skeleton.png").write_bytes(b"\x89PNG\r\n\x1a\nFAKE")
        (base / "rt.js").write_text("/* local runtime */")
        (base / "rt.css").write_text("/* local css */")
        return base

    def _run(self, base, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "generate_spine_player.py"),
             "--skeleton", str(base / "skeleton.json"),
             "--atlas", str(base / "skeleton.atlas"),
             "--output", str(base / "out.html"), *extra],
            capture_output=True, text=True,
        )

    def test_local_runtime_files_are_embedded_offline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = self._assets(directory)
            result = self._run(base, "--runtime-js", str(base / "rt.js"),
                               "--runtime-css", str(base / "rt.css"))
            self.assertEqual(result.returncode, 0, result.stderr)
            html = (base / "out.html").read_text()
            self.assertIn(generate_spine_player.to_data_uri("/* local runtime */",
                                                            "text/javascript"), html)
            self.assertIn("Spine Runtimes License Agreement", html)

    def test_cdn_flag_skips_embedding_entirely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = self._assets(directory)
            result = self._run(base, "--cdn-runtime")
            self.assertEqual(result.returncode, 0, result.stderr)
            html = (base / "out.html").read_text()
            self.assertIn("unpkg.com", html)
            self.assertNotIn("Spine Runtimes License Agreement", html)

    def test_unreachable_runtime_warns_and_degrades_to_cdn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = self._assets(directory)
            env = {**os.environ, "XDG_CACHE_HOME": str(base / "empty-cache")}
            result = subprocess.run(
                [sys.executable, "-c",
                 "import urllib.request, sys, runpy;"
                 "urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(OSError('offline'));"
                 f"sys.argv = ['gen', '--skeleton', {str(base / 'skeleton.json')!r},"
                 f" '--atlas', {str(base / 'skeleton.atlas')!r},"
                 f" '--output', {str(base / 'out.html')!r}];"
                 f"runpy.run_path({str(SCRIPTS / 'generate_spine_player.py')!r}, run_name='__main__')"],
                capture_output=True, text=True, env=env, cwd=directory,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARNING", result.stdout)
            self.assertIn("unpkg.com", (base / "out.html").read_text())


# --------------------------------------------------------------------------- #
# position_parts (needs numpy + OpenCV)
# --------------------------------------------------------------------------- #


@unittest.skipUnless(HAS_CV, "position_parts requires numpy, OpenCV, and Pillow")
class ForegroundMaskTests(unittest.TestCase):
    def _rgba(self, width, height, rgb, alpha):
        import numpy as np

        image = np.zeros((height, width, 4), dtype=np.uint8)
        image[:, :, :3] = rgb
        image[:, :, 3] = alpha
        return image

    def test_transparent_pixels_are_background(self) -> None:
        mask = position_parts.create_foreground_mask(self._rgba(32, 32, (10, 200, 10), 0))
        self.assertEqual(int(mask.max()), 0)

    def test_opaque_background_coloured_pixels_are_background(self) -> None:
        mask = position_parts.create_foreground_mask(self._rgba(32, 32, (255, 255, 255), 255))
        self.assertEqual(int(mask.max()), 0)

    def test_opaque_distinct_pixels_are_foreground(self) -> None:
        mask = position_parts.create_foreground_mask(self._rgba(32, 32, (10, 200, 10), 255))
        self.assertEqual(int(mask.min()), 255)

    def test_mask_is_binary(self) -> None:
        import numpy as np

        image = self._rgba(32, 32, (10, 200, 10), 255)
        image[:, :16, 3] = 0
        mask = position_parts.create_foreground_mask(image)
        self.assertEqual(set(np.unique(mask)).issubset({0, 255}), True)

    def test_background_colour_is_configurable(self) -> None:
        black = self._rgba(32, 32, (0, 0, 0), 255)
        self.assertEqual(int(position_parts.create_foreground_mask(black).min()), 255)
        self.assertEqual(
            int(position_parts.create_foreground_mask(black, bg_color=(0, 0, 0)).max()), 0
        )

    def test_threshold_controls_near_background_pixels(self) -> None:
        near_white = self._rgba(32, 32, (245, 245, 245), 255)
        self.assertEqual(int(position_parts.create_foreground_mask(near_white).max()), 0)
        loose = position_parts.create_foreground_mask(near_white, bg_threshold=5)
        self.assertEqual(int(loose.min()), 255)


@unittest.skipUnless(HAS_CV, "position_parts requires numpy, OpenCV, and Pillow")
class ZOrderTests(unittest.TestCase):
    """The reference image decides occlusion: whichever part matches the shared
    pixels is drawn in front. Returned order is back to front."""

    def _scene(self, directory):
        from PIL import Image

        parts = Path(directory) / "parts"
        parts.mkdir()
        # Two 40x40 squares overlapping in a 20x40 strip. The reference shows the
        # blue square's colour in the overlap, so blue must land in front.
        red, blue = (220, 40, 40, 255), (40, 40, 220, 255)
        Image.new("RGBA", (40, 40), red).save(parts / "back.png")
        Image.new("RGBA", (40, 40), blue).save(parts / "front.png")

        reference = Image.new("RGBA", (80, 60), (0, 0, 0, 0))
        reference.paste(Image.new("RGBA", (40, 40), red), (10, 10))
        reference.paste(Image.new("RGBA", (40, 40), blue), (30, 10))
        reference_path = Path(directory) / "reference.png"
        reference.save(reference_path)

        positions = {
            "back": {"x": 10, "y": 10, "width": 40, "height": 40, "method": "test"},
            "front": {"x": 30, "y": 10, "width": 40, "height": 40, "method": "test"},
        }
        return reference_path, parts, positions

    def test_occluding_part_is_ordered_in_front(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout"):
            reference, parts, positions = self._scene(directory)
            order, depth = position_parts.compute_z_order(str(reference), str(parts), positions)
            self.assertEqual(order, ["back", "front"])
            self.assertLess(depth["back"], depth["front"])

    def test_non_overlapping_parts_are_all_returned(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout"):
            reference, parts, positions = self._scene(directory)
            positions["front"]["x"] = 200
            order, _ = position_parts.compute_z_order(str(reference), str(parts), positions)
            self.assertEqual(sorted(order), ["back", "front"])

    def test_parts_without_a_file_are_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch("sys.stdout"):
            reference, parts, positions = self._scene(directory)
            positions["ghost"] = {"x": 0, "y": 0, "width": 10, "height": 10, "method": "test"}
            order, _ = position_parts.compute_z_order(str(reference), str(parts), positions)
            self.assertNotIn("ghost", order)


if __name__ == "__main__":
    unittest.main()
