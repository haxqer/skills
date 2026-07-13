#!/usr/bin/env python3

import io
import math
import unittest
from contextlib import redirect_stdout

from balance_calculator import (
    calculate_combat,
    calculate_curve,
    calculate_drop,
    calculate_economy,
    calculate_progression,
    calculate_proportion,
    calculate_rating,
    emit,
)


class CurveTests(unittest.TestCase):
    def test_linear_curve_uses_offset_from_first_row(self) -> None:
        result = calculate_curve("linear", 3, start_index=5, base=100, increment=25)
        self.assertEqual(result["rows"], [
            {"index": 5, "value": 100},
            {"index": 6, "value": 125},
            {"index": 7, "value": 150},
        ])

    def test_geometric_curve(self) -> None:
        result = calculate_curve("geometric", 3, base=100, rate=0.1)
        self.assertAlmostEqual(result["rows"][2]["value"], 121)

    def test_logistic_curve_handles_extreme_inputs(self) -> None:
        result = calculate_curve(
            "logistic",
            2,
            start_index=-1000,
            lower=0,
            upper=100,
            midpoint=0,
            steepness=100,
        )
        self.assertEqual(result["rows"][0]["value"], 0)


class CombatTests(unittest.TestCase):
    def test_expected_ttk_without_modifiers(self) -> None:
        result = calculate_combat(health=1000, damage=100, attack_rate=2)
        self.assertEqual(result["metrics"]["expected_dps"], 200)
        self.assertEqual(result["metrics"]["expected_ttk_seconds"], 5)
        self.assertEqual(result["metrics"]["normal_landed_hits_to_kill"], 10)

    def test_crit_flat_and_percentage_reduction_order(self) -> None:
        result = calculate_combat(
            health=1000,
            damage=100,
            attack_rate=1,
            accuracy=0.5,
            crit_chance=0.25,
            crit_multiplier=2,
            flat_reduction=20,
            damage_reduction=0.25,
        )
        expected_landed = 0.75 * 60 + 0.25 * 135
        self.assertAlmostEqual(result["metrics"]["expected_damage_per_landed_hit"], expected_landed)
        self.assertAlmostEqual(result["metrics"]["expected_dps"], expected_landed * 0.5)


class ProgressionTests(unittest.TestCase):
    def test_cost_income_and_cumulative_periods(self) -> None:
        result = calculate_progression(
            base_cost=100,
            cost_growth=0.1,
            count=3,
            income_per_period=50,
        )
        self.assertAlmostEqual(result["rows"][2]["cost"], 121)
        self.assertAlmostEqual(result["rows"][2]["cumulative_cost"], 331)
        self.assertAlmostEqual(result["rows"][2]["periods_for_step"], 2.42)
        self.assertAlmostEqual(result["rows"][2]["cumulative_periods"], 6.62)

    def test_rounding_uses_half_up_for_nonnegative_costs(self) -> None:
        result = calculate_progression(
            base_cost=105,
            cost_growth=0,
            count=1,
            round_to=10,
        )
        self.assertEqual(result["rows"][0]["cost"], 110)


class DropTests(unittest.TestCase):
    def test_geometric_distribution(self) -> None:
        result = calculate_drop(chance=0.02, attempts=[50])
        self.assertAlmostEqual(result["metrics"]["expected_attempts"], 50)
        self.assertEqual(result["metrics"]["attempts_by_quantile"]["p50"], 35)
        self.assertAlmostEqual(
            result["metrics"]["probability_by_attempt"]["50"],
            1 - 0.98**50,
        )

    def test_hard_pity_caps_tail_and_expectation(self) -> None:
        result = calculate_drop(chance=0.02, hard_pity=50, attempts=[49, 50])
        self.assertAlmostEqual(
            result["metrics"]["expected_attempts"],
            (1 - 0.98**50) / 0.02,
        )
        self.assertLessEqual(result["metrics"]["attempts_by_quantile"]["p99"], 50)
        self.assertEqual(result["metrics"]["probability_by_attempt"]["50"], 1)

    def test_p100_requires_a_guaranteed_maximum(self) -> None:
        with self.assertRaisesRegex(ValueError, "less than 1"):
            calculate_drop(chance=0.02, quantiles=[1])

        guaranteed = calculate_drop(chance=0.02, hard_pity=80, quantiles=[1])
        self.assertEqual(guaranteed["metrics"]["attempts_by_quantile"]["p100"], 80)

        always_drops = calculate_drop(chance=1, quantiles=[1])
        self.assertEqual(always_drops["metrics"]["attempts_by_quantile"]["p100"], 1)


class EconomyTests(unittest.TestCase):
    def test_goal_and_horizon(self) -> None:
        result = calculate_economy(
            source_per_period=1200,
            mandatory_sink_per_period=500,
            starting_balance=200,
            goal_cost=5000,
            horizon=10,
        )
        self.assertEqual(result["metrics"]["net_flow_per_period"], 700)
        self.assertEqual(result["metrics"]["periods_to_goal"], 7)
        self.assertEqual(result["metrics"]["balance_at_horizon"], 7200)
        self.assertTrue(math.isclose(result["metrics"]["mandatory_sink_coverage"], 5 / 12))

    def test_nonpositive_net_flow_has_no_goal_time(self) -> None:
        result = calculate_economy(
            source_per_period=100,
            mandatory_sink_per_period=100,
            starting_balance=0,
            goal_cost=500,
            horizon=10,
        )
        self.assertIsNone(result["metrics"]["periods_to_goal"])


class RatingTests(unittest.TestCase):
    def test_equal_ratings_and_update(self) -> None:
        result = calculate_rating(rating_a=1500, rating_b=1500, score_a=1, k_factor=32)
        self.assertEqual(result["metrics"]["expected_score_a"], 0.5)
        self.assertEqual(result["metrics"]["rating_delta_a"], 16)
        self.assertEqual(result["metrics"]["updated_rating_a"], 1516)
        self.assertEqual(result["metrics"]["updated_rating_b"], 1484)

    def test_four_hundred_point_gap(self) -> None:
        result = calculate_rating(rating_a=1200, rating_b=1600)
        self.assertAlmostEqual(result["metrics"]["expected_score_a"], 1 / 11)
        self.assertIsNone(result["metrics"]["updated_rating_a"])


class ProportionTests(unittest.TestCase):
    def test_wilson_interval_and_sample_plan(self) -> None:
        result = calculate_proportion(
            successes=50,
            trials=100,
            confidence=0.95,
            target_margin=0.05,
        )
        self.assertAlmostEqual(result["metrics"]["estimate"], 0.5)
        self.assertAlmostEqual(result["metrics"]["wilson_lower"], 0.4038315304)
        self.assertAlmostEqual(result["metrics"]["wilson_upper"], 0.5961684696)
        self.assertEqual(result["metrics"]["conservative_sample_size"], 385)

    def test_zero_success_interval_is_bounded(self) -> None:
        result = calculate_proportion(successes=0, trials=20)
        self.assertEqual(result["metrics"]["wilson_lower"], 0)
        self.assertGreater(result["metrics"]["wilson_upper"], 0)


class OutputTests(unittest.TestCase):
    def test_csv_output_removes_binary_float_noise(self) -> None:
        payload = calculate_progression(
            base_cost=100,
            cost_growth=0.1,
            count=3,
            income_per_period=50,
        )
        output = io.StringIO()
        with redirect_stdout(output):
            emit(payload, "csv")
        self.assertIn("2,110.0,210.0,50.0,2.2,4.2", output.getvalue())
        self.assertNotIn("0000000000001", output.getvalue())


if __name__ == "__main__":
    unittest.main()
