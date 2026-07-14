#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _asset_utils import sha256_file
from build_asset_catalog import (
    build_record,
    compatibility_result,
    write_agent_index,
)
from materialize_asset_plan import validate_row, write_sidecar


def retrieval_metadata(
    asset_id: str,
    source_path: str,
    *,
    source_sha256: str | None = None,
) -> dict:
    source = {"original_path": source_path}
    if source_sha256 is not None:
        source["sha256"] = source_sha256
    return {
        "asset_id": asset_id,
        "name": "Balance data",
        "description": "Structured data used by game-balance tooling.",
        "category": "data/balance",
        "tags": ["balance", "data"],
        "technical_status": "ready",
        "license": {"status": "owned"},
        "source": source,
        "usage": {"recommended_for": ["game-balance configuration"]},
    }


class MaterializeContractTests(unittest.TestCase):
    def test_strict_validation_rejects_duplicate_asset_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root = root / "source"
            source_root.mkdir()
            first = source_root / "first.csv"
            second = source_root / "second.csv"
            first.write_text("id,value\nfirst,1\n", encoding="utf-8")
            second.write_text("id,value\nsecond,2\n", encoding="utf-8")
            destinations: set[Path] = set()
            asset_ids: set[str] = set()

            first_row = {
                "_line": 1,
                "source": first.name,
                "destination": "data/first.csv",
                "action": "copy",
                "expected_sha256": sha256_file(first),
                "metadata": retrieval_metadata("data.shared", first.name),
            }
            second_row = {
                "_line": 2,
                "source": second.name,
                "destination": "data/second.csv",
                "action": "copy",
                "expected_sha256": sha256_file(second),
                "metadata": retrieval_metadata("data.shared", second.name),
            }

            validate_row(
                first_row,
                source_root,
                root / "library" / "assets",
                destinations,
                asset_ids,
                True,
            )
            with self.assertRaisesRegex(ValueError, "Duplicate metadata.asset_id"):
                validate_row(
                    second_row,
                    source_root,
                    root / "library" / "assets",
                    destinations,
                    asset_ids,
                    True,
                )

    def test_strict_validation_rejects_incorrect_source_hash_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root = root / "source"
            source_root.mkdir()
            source = source_root / "balance.csv"
            source.write_text("id,value\nfirst,1\n", encoding="utf-8")
            row = {
                "_line": 1,
                "source": source.name,
                "destination": "data/balance.csv",
                "action": "copy",
                "expected_sha256": sha256_file(source),
                "metadata": retrieval_metadata(
                    "data.balance",
                    source.name,
                    source_sha256="0" * 64,
                ),
            }

            with self.assertRaisesRegex(ValueError, "source.sha256"):
                validate_row(
                    row,
                    source_root,
                    root / "library" / "assets",
                    set(),
                    set(),
                    True,
                )

    def test_sidecar_uses_verified_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "asset.csv"
            verified_hash = "a" * 64
            write_sidecar(
                {
                    "destination": destination,
                    "source_sha256": verified_hash,
                    "metadata": retrieval_metadata(
                        "data.balance",
                        "asset.csv",
                        source_sha256="0" * 64,
                    ),
                }
            )
            sidecar = json.loads(
                Path(str(destination) + ".asset.json").read_text(encoding="utf-8")
            )
            self.assertEqual(sidecar["source"]["sha256"], verified_hash)

            legacy_destination = Path(temporary) / "legacy.csv"
            write_sidecar(
                {
                    "destination": legacy_destination,
                    "source_sha256": verified_hash,
                    "metadata": {"source_sha256": "0" * 64},
                }
            )
            legacy_sidecar = json.loads(
                Path(str(legacy_destination) + ".asset.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(legacy_sidecar["source_sha256"], verified_hash)


class CatalogCompatibilityTests(unittest.TestCase):
    def test_non_external_import_is_neutral_for_ready_asset(self) -> None:
        result = compatibility_result(
            {"status": "not-external-import"}, "4.4.stable"
        )
        self.assertEqual(result["status"], "not_applicable")

        with tempfile.TemporaryDirectory() as temporary:
            library_root = Path(temporary) / "library"
            asset_root = library_root / "assets"
            asset = asset_root / "data" / "balance_config.tres"
            asset.parent.mkdir(parents=True)
            asset.write_text(
                '[gd_resource type="Resource" format=3]\n', encoding="utf-8"
            )
            metadata = retrieval_metadata("data.balance_config", "balance_config.tres")
            Path(str(asset) + ".asset.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )

            record = build_record(
                asset,
                asset_root,
                library_root,
                {"data/balance_config.tres": {"status": "not-external-import"}},
                "4.4.stable",
            )
            self.assertEqual(
                record["godot_compatibility"]["status"], "not_applicable"
            )
            self.assertTrue(record["ready_for_agent"])


class AgentIndexTests(unittest.TestCase):
    def test_agent_index_maps_categories_to_directories_and_usage(self) -> None:
        records = [
            {
                "category": "audio/sfx",
                "description": "Metal sword impact.",
                "library_path": "assets/audio/sfx/combat/sword_hit_metal_01.wav",
                "ready_for_agent": True,
                "usage": {"recommended_for": ["melee combat impact sound"]},
            },
            {
                "category": "audio/sfx",
                "description": "Wooden shield impact.",
                "library_path": "assets/audio/sfx/combat/shield_hit_wood_01.wav",
                "ready_for_agent": False,
                "usage": {"recommended_for": ["melee combat impact sound"]},
            },
            {
                "category": "2d/ui",
                "description": "Inventory slot hover state.",
                "library_path": "assets/2d/ui/controls/inventory_slot_hover.png",
                "ready_for_agent": True,
                "usage": {"recommended_for": ["inventory slot hover state"]},
            },
        ]
        summary = {"asset_count": 3, "ready_for_agent_count": 2}

        with tempfile.TemporaryDirectory() as temporary:
            index_path = write_agent_index(Path(temporary), records, summary)
            content = index_path.read_text(encoding="utf-8")

        self.assertEqual(index_path.name, "AGENTS.md")
        self.assertIn("| Audio / SFX | `assets/audio/sfx/combat` |", content)
        self.assertIn("melee combat impact sound", content)
        self.assertIn("| 1 / 2 |", content)
        self.assertIn("catalog/asset_catalog.jsonl", content)
        self.assertIn("How To Use This Package", content)


if __name__ == "__main__":
    unittest.main()
