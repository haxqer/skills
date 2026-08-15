#!/usr/bin/env python3

import copy
import json
import os
import tempfile
import unittest

from sim_diff import evaluate, load_thresholds
from sim_diff import main as diff_main
from sim_report import aggregate
from sim_runner import (
    DEFAULT_BATTLES,
    DEFAULT_MAX_BATTLES,
    apply_override,
    build_scenario,
    parse_override,
    read_path,
    run_batch,
    run_until_converged,
)
from sim_search import (
    Evaluator,
    Objective,
    Tunable,
    coordinate_descent,
    load_plan,
    multi_start_search,
    sensitivity,
    start_points,
)

SCENARIO = {
    "max_rounds": 40,
    "seconds_per_round": 1.0,
    "damage_model": "subtract",
    "damage_variance": 0.2,
    "teams": {
        "A": [
            {"id": "a1", "hp": 400, "atk": 40, "def": 10, "speed": 100, "accuracy": 0.9,
             "skills": [{"id": "hit", "type": "attack", "power": 1.0}]},
            {"id": "a2", "hp": 300, "atk": 30, "def": 10, "speed": 95, "accuracy": 0.9},
        ],
        "B": [{"id": "b1", "hp": 900, "atk": 45, "def": 10, "speed": 98, "accuracy": 0.9}],
    },
}


class OverrideTests(unittest.TestCase):
    def test_parse_override_reads_json_values(self) -> None:
        self.assertEqual(parse_override("teams.A.0.atk=120"), ("teams.A.0.atk", 120))
        self.assertEqual(parse_override("damage_model=\"ratio\""), ("damage_model", "ratio"))
        self.assertEqual(parse_override("damage_model=ratio"), ("damage_model", "ratio"))

    def test_parse_override_requires_an_equals_sign(self) -> None:
        with self.assertRaises(ValueError):
            parse_override("teams.A.0.atk")

    def test_apply_override_walks_lists_and_dicts(self) -> None:
        scenario = copy.deepcopy(SCENARIO)
        apply_override(scenario, "teams.A.0.skills.0.power", 1.5)
        self.assertEqual(scenario["teams"]["A"][0]["skills"][0]["power"], 1.5)

    def test_apply_override_rejects_unknown_keys(self) -> None:
        with self.assertRaises(KeyError):
            apply_override(copy.deepcopy(SCENARIO), "teams.A.0.luck", 1)

    def test_apply_override_rejects_out_of_range_indexes(self) -> None:
        with self.assertRaises(KeyError):
            apply_override(copy.deepcopy(SCENARIO), "teams.A.9.atk", 1)

    def test_scale_multiplies_the_current_value(self) -> None:
        scenario = build_scenario(SCENARIO, [], ["teams.A.0.atk=2"])
        self.assertAlmostEqual(read_path(scenario, "teams.A.0.atk"), 80)

    def test_scale_rejects_non_numeric_targets(self) -> None:
        with self.assertRaises(ValueError):
            build_scenario(SCENARIO, [], ["damage_model=2"])

    def test_build_scenario_does_not_mutate_the_base(self) -> None:
        build_scenario(SCENARIO, ["teams.A.0.atk=999"])
        self.assertEqual(SCENARIO["teams"]["A"][0]["atk"], 40)


class BatchTests(unittest.TestCase):
    def test_seeds_are_contiguous_from_the_base(self) -> None:
        records = run_batch(SCENARIO, 5, seed_base=100)
        self.assertEqual([r["seed"] for r in records], [100, 101, 102, 103, 104])

    def test_same_seed_base_reproduces_the_batch(self) -> None:
        self.assertEqual(run_batch(SCENARIO, 20, 7), run_batch(SCENARIO, 20, 7))

    def test_parallel_matches_serial(self) -> None:
        self.assertEqual(run_batch(SCENARIO, 24, 0, workers=1), run_batch(SCENARIO, 24, 0, workers=2))

    def test_zero_battles_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_batch(SCENARIO, 0)

    def test_common_random_numbers_pair_the_variants(self) -> None:
        left = run_batch(SCENARIO, 50, 0)
        right = run_batch(build_scenario(SCENARIO, ["teams.B.0.hp=901"]), 50, 0)
        self.assertEqual([r["seed"] for r in left], [r["seed"] for r in right])


class DefaultsTests(unittest.TestCase):
    def test_reporting_floor_is_ten_thousand_battles(self) -> None:
        self.assertEqual(DEFAULT_BATTLES, 10000)
        self.assertGreaterEqual(DEFAULT_MAX_BATTLES, DEFAULT_BATTLES)

    def test_cli_defaults_match_the_floor(self) -> None:
        from sim_runner import build_parser

        args = build_parser().parse_args(["scenario.json"])
        self.assertEqual(args.battles, DEFAULT_BATTLES)
        self.assertEqual(args.min_battles, DEFAULT_BATTLES)
        self.assertEqual(args.max_battles, DEFAULT_MAX_BATTLES)

    def test_search_verifies_at_or_above_the_floor(self) -> None:
        from sim_search import DEFAULT_VERIFY_BATTLES

        self.assertGreaterEqual(DEFAULT_VERIFY_BATTLES, DEFAULT_BATTLES)


class ConvergenceTests(unittest.TestCase):
    def test_reports_not_converged_when_the_cap_binds(self) -> None:
        records, run = run_until_converged(
            SCENARIO, "A", target_half_width=0.001, min_battles=50, max_battles=100
        )
        self.assertFalse(run["converged"])
        self.assertEqual(run["battles"], 100)
        self.assertEqual(len(records), 100)
        self.assertGreater(run["win_rate_half_width"], run["target_half_width"])

    def test_stops_once_the_interval_is_tight_enough(self) -> None:
        records, run = run_until_converged(
            SCENARIO, "A", target_half_width=0.20, min_battles=50, max_battles=4000
        )
        self.assertTrue(run["converged"])
        self.assertLessEqual(run["win_rate_half_width"], 0.20)
        self.assertLess(len(records), 4000)

    def test_rejects_an_inverted_battle_range(self) -> None:
        with self.assertRaises(ValueError):
            run_until_converged(SCENARIO, "A", 0.05, min_battles=500, max_battles=100)


class ObjectiveTests(unittest.TestCase):
    def test_target_band_has_no_violation_inside_the_tolerance(self) -> None:
        objective = Objective({"metric": "win_rate.point", "target": 0.5, "tolerance": 0.02,
                               "scale": 0.02})
        self.assertEqual(objective.violation(0.51), 0.0)
        self.assertAlmostEqual(objective.violation(0.56), 2.0)

    def test_max_constraint_only_penalises_above(self) -> None:
        objective = Objective({"metric": "max_damage_share", "max": 0.4, "scale": 0.05})
        self.assertEqual(objective.violation(0.30), 0.0)
        self.assertAlmostEqual(objective.violation(0.45), 1.0)

    def test_min_constraint_only_penalises_below(self) -> None:
        objective = Objective({"metric": "x", "min": 2.0, "scale": 1.0})
        self.assertEqual(objective.violation(3.0), 0.0)
        self.assertAlmostEqual(objective.violation(1.0), 1.0)

    def test_objective_needs_a_bound(self) -> None:
        with self.assertRaises(ValueError):
            Objective({"metric": "x"})


class TunableTests(unittest.TestCase):
    def test_snap_clamps_and_grids(self) -> None:
        tunable = Tunable({"path": "p", "min": 100, "max": 200, "step": 25}, 150)
        self.assertEqual(tunable.snap(151), 150)
        self.assertEqual(tunable.snap(163), 175)
        self.assertEqual(tunable.snap(1000), 200)
        self.assertEqual(tunable.snap(-5), 100)

    def test_inverted_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Tunable({"path": "p", "min": 10, "max": 1}, 5)


class SearchTests(unittest.TestCase):
    def _evaluator(self, objectives, tunables, change_penalty=0.0):
        return Evaluator(
            SCENARIO,
            [Tunable(spec, read_path(SCENARIO, spec["path"])) for spec in tunables],
            [Objective(spec) for spec in objectives],
            "A",
            120,
            0,
            1,
            change_penalty,
        )

    def test_search_moves_win_rate_toward_the_target(self) -> None:
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.05, "scale": 0.05}]
        tunables = [{"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 10}]
        evaluator = self._evaluator(objectives, tunables)
        start = evaluator.score((900.0,))
        outcome = coordinate_descent(evaluator, max_passes=30)
        self.assertLess(outcome["best"]["objective"], start["objective"])
        self.assertTrue(outcome["best"]["satisfied"])

    def test_search_reports_an_unsatisfiable_grid_instead_of_faking_success(self) -> None:
        # No multiple of 50 in this range lands inside the +/-0.05 band around 0.5.
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.05, "scale": 0.05}]
        tunables = [{"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50}]
        outcome = coordinate_descent(self._evaluator(objectives, tunables), max_passes=10)
        self.assertFalse(outcome["best"]["satisfied"])
        self.assertGreater(outcome["best"]["violation"], 0.0)

    def test_search_is_reproducible(self) -> None:
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.05, "scale": 0.05}]
        tunables = [{"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50}]
        first = coordinate_descent(self._evaluator(objectives, tunables), 6)["best"]["values"]
        second = coordinate_descent(self._evaluator(objectives, tunables), 6)["best"]["values"]
        self.assertEqual(first, second)

    def test_change_penalty_keeps_a_satisfied_baseline_still(self) -> None:
        objectives = [{"metric": "win_rate.point", "min": 0.0, "scale": 1.0}]
        tunables = [{"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50}]
        outcome = coordinate_descent(self._evaluator(objectives, tunables, 1.0), 6)
        self.assertEqual(outcome["best"]["values"], [900.0])
        self.assertEqual(outcome["best"]["change_cost"], 0.0)

    def test_evaluator_caches_repeated_points(self) -> None:
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.5, "scale": 0.5}]
        tunables = [{"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50}]
        evaluator = self._evaluator(objectives, tunables)
        evaluator.score((900.0,))
        evaluator.score((900.0,))
        self.assertEqual(evaluator.evaluations, 1)

    def test_start_points_begin_at_the_baseline_and_spread(self) -> None:
        tunables = [
            Tunable({"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50}, 900),
            Tunable({"path": "teams.A.0.atk", "min": 20, "max": 60, "step": 5}, 40),
        ]
        points = start_points(tunables, 4)
        self.assertEqual(points[0], (900.0, 40.0))
        self.assertEqual(len(set(points)), len(points))
        for point in points:
            self.assertTrue(300 <= point[0] <= 1500)
            self.assertTrue(20 <= point[1] <= 60)

    def test_start_points_are_deterministic(self) -> None:
        tunables = [Tunable({"path": "p", "min": 0, "max": 100, "step": 1}, 50)]
        self.assertEqual(start_points(tunables, 6), start_points(tunables, 6))

    def test_multi_start_never_loses_to_the_baseline_descent(self) -> None:
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.02, "scale": 0.02}]
        tunables = [
            {"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50},
            {"path": "teams.A.0.atk", "min": 20, "max": 80, "step": 5},
        ]
        single = coordinate_descent(self._evaluator(objectives, tunables), 6)["best"]
        multi = multi_start_search(self._evaluator(objectives, tunables), 6, restarts=4)
        self.assertLessEqual(multi["best"]["objective"], single["objective"] + 1e-9)
        # Halton points that snap onto the same grid cell are deduplicated.
        self.assertTrue(1 <= len(multi["restarts"]) <= 4)
        self.assertIn(multi["winning_restart"], range(len(multi["restarts"])))

    def test_multi_start_is_reproducible(self) -> None:
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.02, "scale": 0.02}]
        tunables = [{"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 50}]
        first = multi_start_search(self._evaluator(objectives, tunables), 5, 3)["best"]["values"]
        second = multi_start_search(self._evaluator(objectives, tunables), 5, 3)["best"]["values"]
        self.assertEqual(first, second)

    def test_sensitivity_ranks_by_absolute_effect(self) -> None:
        objectives = [{"metric": "win_rate.point", "target": 0.5, "tolerance": 0.02, "scale": 0.02}]
        tunables = [
            {"path": "teams.B.0.hp", "min": 300, "max": 1500, "step": 200},
            {"path": "teams.A.1.speed", "min": 90, "max": 100, "step": 1},
        ]
        rows = sensitivity(self._evaluator(objectives, tunables), ["win_rate.point"])
        self.assertEqual(rows[0]["path"], "teams.B.0.hp")
        self.assertGreaterEqual(rows[0]["abs_effect"], rows[1]["abs_effect"])
        self.assertLess(rows[0]["elasticity"], 0)


class PlanTests(unittest.TestCase):
    def test_plan_rejects_a_non_numeric_tunable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "plan.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "objectives": [{"metric": "win_rate.point", "target": 0.5}],
                        "tunables": [{"path": "damage_model"}],
                    },
                    handle,
                )
            with self.assertRaises(ValueError):
                load_plan(path, SCENARIO)

    def test_plan_requires_a_tunable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "plan.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"objectives": []}, handle)
            with self.assertRaises(ValueError):
                load_plan(path, SCENARIO)


class DiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.report = aggregate(run_batch(SCENARIO, 100, 0), "A")

    def _thresholds(self, text: str, name: str = "thresholds.csv") -> str:
        path = os.path.join(self.directory.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def _report_file(self, name: str, report) -> str:
        path = os.path.join(self.directory.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle)
        return path

    def test_absolute_bounds_are_checked(self) -> None:
        rules = load_thresholds(
            self._thresholds("metric,min,max,max_delta,max_delta_pct,note\nwin_rate.point,0,1,,,ok\n")
        )
        self.assertEqual(evaluate(self.report, rules)[0]["status"], "pass")

    def test_violation_explains_itself(self) -> None:
        rules = load_thresholds(
            self._thresholds(
                "metric,min,max,max_delta,max_delta_pct,note\nwin_rate.point,0.99,,,,too high\n"
            )
        )
        result = evaluate(self.report, rules)[0]
        self.assertEqual(result["status"], "fail")
        self.assertIn("min", result["reasons"][0])

    def test_missing_metric_is_flagged_not_crashed(self) -> None:
        rules = load_thresholds(
            self._thresholds("metric,min,max,max_delta,max_delta_pct,note\nnope.nope,0,1,,,\n")
        )
        self.assertEqual(evaluate(self.report, rules)[0]["status"], "missing")

    def test_delta_bound_uses_the_baseline(self) -> None:
        candidate = aggregate(run_batch(build_scenario(SCENARIO, ["teams.B.0.hp=200"]), 100, 0), "A")
        rules = load_thresholds(
            self._thresholds(
                "metric,min,max,max_delta,max_delta_pct,note\nwin_rate.point,,,0.01,,drift\n"
            )
        )
        result = evaluate(candidate, rules, self.report)[0]
        self.assertEqual(result["status"], "fail")
        self.assertIn("max_delta", result["reasons"][0])

    def test_empty_threshold_file_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            load_thresholds(self._thresholds("metric,min,max,max_delta,max_delta_pct,note\n"))

    def test_non_numeric_threshold_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            load_thresholds(
                self._thresholds("metric,min,max,max_delta,max_delta_pct,note\nwin_rate.point,low,,,,\n")
            )

    def test_cli_exit_codes_separate_failure_from_error(self) -> None:
        report_path = self._report_file("candidate.json", self.report)
        passing = self._thresholds(
            "metric,min,max,max_delta,max_delta_pct,note\nwin_rate.point,0,1,,,\n", "pass.csv"
        )
        failing = self._thresholds(
            "metric,min,max,max_delta,max_delta_pct,note\nwin_rate.point,0.999,,,,\n", "fail.csv"
        )
        self.assertEqual(diff_main([report_path, passing, "--format", "json"]), 0)
        self.assertEqual(diff_main([report_path, failing, "--format", "json"]), 2)
        self.assertEqual(diff_main(["missing.json", passing]), 1)


if __name__ == "__main__":
    unittest.main()
