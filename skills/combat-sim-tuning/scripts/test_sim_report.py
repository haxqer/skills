#!/usr/bin/env python3

import math
import unittest

from sim_report import (
    aggregate,
    binary_entropy,
    bootstrap_interval,
    describe,
    effective_count,
    get_path,
    gini,
    paired_compare,
    quantile,
    render_markdown,
    wilson_interval,
)


def record(seed, winner, rounds=10, damage=(50, 50), taken=(10, 10), survived=(True, True),
           first_death_team=None, winner_was_behind=False, winner_hp=0.5, timeout=False):
    units = {}
    for index, team in enumerate(("A", "B")):
        units[f"{team}/u"] = {
            "team": team,
            "unit_id": "u",
            "role": "dps",
            "survived": survived[index],
            "death_round": None if survived[index] else rounds,
            "hp_fraction": 1.0 if survived[index] else 0.0,
            "damage_dealt": damage[index],
            "overkill": 0.0,
            "damage_taken": taken[index],
            "damage_absorbed": 0.0,
            "healing_done": 0.0,
            "overhealing": 0.0,
            "actions": rounds,
            "hits": rounds,
            "misses": 0,
            "crits": 0,
            "kills": 0,
        }
    return {
        "seed": seed,
        "winner": winner,
        "timeout": timeout,
        "rounds": rounds,
        "duration": rounds * 1.0,
        "team_hp_fraction": {"A": 0.5, "B": 0.5},
        "margin": 0.5,
        "first_death_team": first_death_team,
        "first_death_round": None if first_death_team is None else rounds,
        "lead_flips": 1 if winner_was_behind else 0,
        "winner_was_behind": winner_was_behind,
        "winner_hp_fraction": winner_hp,
        "units": units,
        "trace": None,
    }


class IntervalTests(unittest.TestCase):
    def test_wilson_stays_inside_the_unit_interval_at_zero(self) -> None:
        result = wilson_interval(0, 100)
        self.assertEqual(result["point"], 0.0)
        self.assertGreaterEqual(result["low"], 0.0)
        self.assertGreater(result["high"], 0.0)

    def test_wilson_stays_inside_the_unit_interval_at_one(self) -> None:
        result = wilson_interval(100, 100)
        self.assertLessEqual(result["high"], 1.0)
        self.assertLess(result["low"], 1.0)

    def test_wilson_narrows_as_samples_grow(self) -> None:
        small = wilson_interval(50, 100)["half_width"]
        large = wilson_interval(5000, 10000)["half_width"]
        self.assertLess(large, small)
        self.assertAlmostEqual(large, small / 10, delta=0.005)

    def test_wilson_rejects_impossible_counts(self) -> None:
        with self.assertRaises(ValueError):
            wilson_interval(5, 4)

    def test_wilson_handles_zero_trials(self) -> None:
        self.assertEqual(wilson_interval(0, 0)["samples"], 0)


class DescriptiveTests(unittest.TestCase):
    def test_quantiles_interpolate(self) -> None:
        values = [1, 2, 3, 4]
        self.assertAlmostEqual(quantile(values, 0.0), 1)
        self.assertAlmostEqual(quantile(values, 0.5), 2.5)
        self.assertAlmostEqual(quantile(values, 1.0), 4)

    def test_describe_reports_dispersion_and_tails(self) -> None:
        stats = describe([10] * 50 + [20] * 50)
        self.assertAlmostEqual(stats["mean"], 15)
        self.assertAlmostEqual(stats["p10"], 10)
        self.assertAlmostEqual(stats["p90"], 20)
        self.assertGreater(stats["cv"], 0)
        self.assertEqual(stats["samples"], 100)

    def test_describe_of_a_constant_has_no_spread(self) -> None:
        stats = describe([7.0] * 10)
        self.assertEqual(stats["sd"], 0.0)
        self.assertEqual(stats["half_width"], 0.0)

    def test_describe_of_nothing_is_safe(self) -> None:
        self.assertEqual(describe([])["samples"], 0)

    def test_gini_bounds(self) -> None:
        self.assertAlmostEqual(gini([1, 1, 1, 1]), 0.0)
        self.assertGreater(gini([0, 0, 0, 1]), 0.7)
        self.assertEqual(gini([0, 0]), 0.0)

    def test_binary_entropy_peaks_at_a_coin_flip(self) -> None:
        self.assertAlmostEqual(binary_entropy(0.5), 1.0)
        self.assertEqual(binary_entropy(1.0), 0.0)
        self.assertEqual(binary_entropy(0.0), 0.0)

    def test_effective_count_matches_an_even_split(self) -> None:
        self.assertAlmostEqual(effective_count([0.25] * 4), 4.0)
        self.assertAlmostEqual(effective_count([1.0, 0.0, 0.0]), 1.0)

    def test_bootstrap_is_deterministic(self) -> None:
        values = [float(index % 7) for index in range(200)]
        self.assertEqual(bootstrap_interval(values, 200), bootstrap_interval(values, 200))


class AggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            record(index, "A" if index < 60 else "B", rounds=10 + index % 5)
            for index in range(100)
        ]

    def test_win_rate_matches_the_records(self) -> None:
        report = aggregate(self.records, "A")
        self.assertAlmostEqual(report["win_rate"]["point"], 0.60)
        self.assertAlmostEqual(report["loss_rate"]["point"], 0.40)
        self.assertEqual(report["samples"], 100)

    def test_focus_team_flips_the_perspective(self) -> None:
        self.assertAlmostEqual(aggregate(self.records, "B")["win_rate"]["point"], 0.40)

    def test_unknown_focus_team_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            aggregate(self.records, "Z")

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            aggregate([])

    def test_damage_share_is_computed_within_the_team(self) -> None:
        records = [record(index, "A", damage=(75, 40)) for index in range(20)]
        report = aggregate(records, "A")
        self.assertAlmostEqual(report["units"]["A/u"]["damage_share"]["mean"], 1.0)
        self.assertAlmostEqual(report["max_damage_share"], 1.0)

    def test_share_of_a_zero_damage_battle_is_zero_not_nan(self) -> None:
        records = [record(index, "draw", damage=(0, 0)) for index in range(5)]
        report = aggregate(records, "A")
        self.assertEqual(report["units"]["A/u"]["damage_share"]["mean"], 0.0)
        self.assertFalse(math.isnan(report["concentration"]["gini"]))

    def test_timeout_and_draw_rates(self) -> None:
        records = [record(index, "draw", timeout=True) for index in range(10)]
        report = aggregate(records, "A")
        self.assertEqual(report["draw_rate"], 1.0)
        self.assertEqual(report["timeout_rate"], 1.0)
        self.assertEqual(report["blowout_rate"], 0.0)

    def test_comeback_and_blowout_rates_use_decisive_battles(self) -> None:
        records = [record(i, "A", winner_was_behind=i < 5, winner_hp=0.9) for i in range(10)]
        report = aggregate(records, "A")
        self.assertAlmostEqual(report["comeback_rate"], 0.5)
        self.assertAlmostEqual(report["blowout_rate"], 1.0)

    def test_first_blood_split(self) -> None:
        records = [record(i, "A", first_death_team="B") for i in range(8)]
        records += [record(i + 8, "B", first_death_team="A") for i in range(2)]
        report = aggregate(records, "A")
        self.assertAlmostEqual(report["first_blood"]["focus_team_rate"], 0.8)
        self.assertAlmostEqual(report["first_blood"]["win_rate_with_first_blood"], 1.0)
        self.assertAlmostEqual(report["first_blood"]["win_rate_without_first_blood"], 0.0)

    def test_markdown_names_the_sample_size(self) -> None:
        text = render_markdown(aggregate(self.records, "A"))
        self.assertIn("100 battles", text)
        self.assertIn("Win rate", text)


class PathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = aggregate([record(i, "A") for i in range(10)], "A")

    def test_reads_a_nested_scalar(self) -> None:
        self.assertAlmostEqual(get_path(self.report, "win_rate.point"), 1.0)

    def test_reads_through_a_key_containing_a_slash(self) -> None:
        self.assertIsInstance(get_path(self.report, "units.A/u.damage_share.mean"), float)

    def test_unknown_path_raises(self) -> None:
        with self.assertRaises(KeyError):
            get_path(self.report, "win_rate.nope")


class PairedTests(unittest.TestCase):
    def test_paired_comparison_detects_a_consistent_shift(self) -> None:
        baseline = [record(i, "B") for i in range(200)]
        candidate = [record(i, "A" if i < 40 else "B") for i in range(200)]
        result = paired_compare(baseline, candidate, "A")
        self.assertEqual(result["paired_seeds"], 200)
        self.assertAlmostEqual(result["win_rate_delta"]["mean"], 0.20)
        self.assertEqual(result["outcome_flips"]["to_win"], 40)
        self.assertTrue(result["significant"])

    def test_identical_runs_are_not_significant(self) -> None:
        batch = [record(i, "A" if i % 2 else "B") for i in range(100)]
        result = paired_compare(batch, batch, "A")
        self.assertAlmostEqual(result["win_rate_delta"]["mean"], 0.0)
        self.assertFalse(result["significant"])

    def test_disjoint_seeds_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            paired_compare(
                [record(i, "A") for i in range(5)],
                [record(i + 100, "A") for i in range(5)],
                "A",
            )


if __name__ == "__main__":
    unittest.main()
