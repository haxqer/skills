#!/usr/bin/env python3

import unittest

from sim_engine import Battle, mitigate, simulate

DUEL = {
    "max_rounds": 30,
    "seconds_per_round": 2.0,
    "damage_model": "subtract",
    "teams": {
        "A": [{"id": "a", "hp": 100, "atk": 30, "def": 10, "speed": 100}],
        "B": [{"id": "b", "hp": 100, "atk": 20, "def": 10, "speed": 90}],
    },
}


def scenario(**overrides):
    import copy

    merged = copy.deepcopy(DUEL)
    merged.update(copy.deepcopy(overrides))
    return merged


class MitigationTests(unittest.TestCase):
    def test_subtract_keeps_a_damage_floor(self) -> None:
        self.assertAlmostEqual(mitigate(100, 40, "subtract", {}), 60)
        self.assertAlmostEqual(mitigate(100, 500, "subtract", {}), 5)

    def test_subtract_floor_is_configurable(self) -> None:
        self.assertAlmostEqual(mitigate(100, 500, "subtract", {"min_damage_fraction": 0.2}), 20)

    def test_ratio_halves_damage_at_the_constant(self) -> None:
        self.assertAlmostEqual(mitigate(100, 300, "ratio", {"defense_constant": 300}), 50)

    def test_ratio_rejects_a_non_positive_constant(self) -> None:
        with self.assertRaises(ValueError):
            mitigate(100, 10, "ratio", {"defense_constant": 0})

    def test_multiplicative_respects_the_cap(self) -> None:
        params = {"defense_coefficient": 0.001, "mitigation_cap": 0.75}
        self.assertAlmostEqual(mitigate(100, 2000, "multiplicative", params), 25)


class DeterminismTests(unittest.TestCase):
    def test_same_seed_reproduces_the_record(self) -> None:
        spec = scenario(damage_variance=0.2)
        spec["teams"]["A"][0]["crit_chance"] = 0.3
        first = simulate(spec, 7)
        second = simulate(spec, 7)
        self.assertEqual(first, second)

    def test_different_seeds_diverge_when_random(self) -> None:
        spec = scenario(damage_variance=0.3)
        spec["teams"]["A"][0]["accuracy"] = 0.6
        records = {simulate(spec, seed)["rounds"] for seed in range(20)}
        self.assertGreater(len(records), 1)

    def test_fully_deterministic_scenario_ignores_the_seed(self) -> None:
        spec = scenario()
        self.assertEqual(simulate(spec, 1)["rounds"], simulate(spec, 999)["rounds"])


class ResolutionTests(unittest.TestCase):
    def test_faster_unit_wins_the_mirror(self) -> None:
        spec = scenario()
        spec["teams"]["B"][0]["atk"] = 30
        record = simulate(spec, 0)
        self.assertEqual(record["winner"], "A")

    def test_duration_scales_with_seconds_per_round(self) -> None:
        record = simulate(scenario(seconds_per_round=4.0), 0)
        self.assertAlmostEqual(record["duration"], record["rounds"] * 4.0)

    def test_timeout_is_reported_when_nobody_dies(self) -> None:
        spec = scenario(max_rounds=3)
        spec["teams"]["A"][0]["atk"] = 1
        spec["teams"]["B"][0]["atk"] = 1
        record = simulate(spec, 0)
        self.assertTrue(record["timeout"])
        self.assertEqual(record["winner"], "draw")
        self.assertEqual(record["rounds"], 3)

    def test_zero_accuracy_never_lands_a_hit(self) -> None:
        spec = scenario(max_rounds=5)
        spec["teams"]["A"][0]["accuracy"] = 0.0
        record = simulate(spec, 3)
        self.assertEqual(record["units"]["A/a"]["hits"], 0)
        self.assertGreater(record["units"]["A/a"]["misses"], 0)
        self.assertEqual(record["units"]["B/b"]["damage_taken"], 0)

    def test_dodge_is_subtracted_from_accuracy(self) -> None:
        spec = scenario(max_rounds=5)
        spec["teams"]["B"][0]["dodge"] = 1.0
        record = simulate(spec, 3)
        self.assertEqual(record["units"]["A/a"]["hits"], 0)

    def test_overkill_is_tracked_separately_from_damage(self) -> None:
        spec = scenario()
        spec["teams"]["A"][0]["atk"] = 10000
        record = simulate(spec, 0)
        self.assertAlmostEqual(record["units"]["A/a"]["damage_dealt"], 100)
        self.assertGreater(record["units"]["A/a"]["overkill"], 0)

    def test_shield_absorbs_before_health(self) -> None:
        spec = scenario(max_rounds=2)
        spec["teams"]["B"][0]["skills"] = [
            {
                "id": "ward",
                "type": "buff",
                "targets": "self",
                "status": {"id": "ward", "duration": 5, "shield": 1000},
            }
        ]
        spec["teams"]["B"][0]["speed"] = 200
        record = simulate(spec, 0)
        self.assertEqual(record["units"]["B/b"]["damage_taken"], 0)
        self.assertGreater(record["units"]["B/b"]["damage_absorbed"], 0)

    def test_dot_kills_without_crediting_a_source(self) -> None:
        spec = scenario(max_rounds=10)
        spec["teams"]["A"][0]["atk"] = 0
        spec["teams"]["A"][0]["skills"] = [
            {
                "id": "poison",
                "type": "debuff",
                "targets": "enemy_single",
                "status": {"id": "poison", "duration": 20, "dot": 60},
            }
        ]
        spec["teams"]["B"][0]["atk"] = 0
        record = simulate(spec, 0)
        self.assertEqual(record["winner"], "A")
        self.assertEqual(record["units"]["A/a"]["damage_dealt"], 0)
        self.assertGreater(record["units"]["B/b"]["damage_taken"], 0)

    def test_stun_skips_the_action(self) -> None:
        spec = scenario(max_rounds=6)
        spec["teams"]["A"][0]["speed"] = 200
        spec["teams"]["A"][0]["skills"] = [
            {
                "id": "hammer",
                "type": "attack",
                "power": 0.1,
                "status": {"id": "stun", "duration": 9, "stun": True},
            }
        ]
        record = simulate(spec, 0)
        self.assertEqual(record["units"]["B/b"]["actions"], 0)

    def test_cooldown_blocks_consecutive_use(self) -> None:
        spec = scenario(max_rounds=4)
        spec["teams"]["A"][0]["skill_policy"] = "priority"
        spec["teams"]["A"][0]["skills"] = [
            {"id": "big", "type": "attack", "power": 0.1, "cooldown": 3, "priority": 5},
            {"id": "small", "type": "attack", "power": 0.1, "priority": 1},
        ]
        spec["teams"]["B"][0]["hp"] = 100000
        battle = Battle(spec, 0)
        battle.run()
        actor = battle.by_team["A"][0]
        self.assertEqual(actor.stats["actions"], 4)

    def test_resource_cost_gates_a_skill(self) -> None:
        spec = scenario(max_rounds=3)
        spec["teams"]["A"][0]["resource"] = 50
        spec["teams"]["A"][0]["resource_regen"] = 0
        spec["teams"]["A"][0]["skills"] = [
            {"id": "nova", "type": "attack", "power": 2.0, "cost": 50, "priority": 5},
            {"id": "poke", "type": "attack", "power": 0.1, "priority": 1},
        ]
        spec["teams"]["B"][0]["hp"] = 100000
        battle = Battle(spec, 0)
        battle.run()
        self.assertEqual(battle.by_team["A"][0].resource, 0)

    def test_heal_is_capped_by_missing_health(self) -> None:
        spec = scenario(max_rounds=4)
        spec["teams"]["A"] = [
            {"id": "medic", "hp": 100, "atk": 100, "def": 0, "speed": 10,
             "skills": [{"id": "mend", "type": "heal", "power": 10.0}]},
            {"id": "meat", "hp": 100, "atk": 0, "def": 0, "speed": 5},
        ]
        record = simulate(spec, 0)
        medic = record["units"]["A/medic"]
        self.assertGreater(medic["overhealing"], 0)
        self.assertLessEqual(medic["healing_done"], 200)

    def test_duplicate_ids_get_distinct_uids(self) -> None:
        spec = scenario()
        spec["teams"]["B"] = [{"id": "mob", "hp": 10, "atk": 1, "def": 0, "speed": 1, "count": 3}]
        record = simulate(spec, 0)
        self.assertIn("B/mob", record["units"])
        self.assertIn("B/mob#2", record["units"])
        self.assertIn("B/mob#3", record["units"])

    def test_comeback_flag_reflects_trailing_before_the_win(self) -> None:
        # B front-loads a limited resource, leads early, then falls off.
        spec = scenario(max_rounds=60)
        spec["teams"]["A"][0].update({"hp": 500, "atk": 20, "def": 0, "speed": 50})
        spec["teams"]["B"][0].update(
            {
                "hp": 600,
                "atk": 100,
                "def": 0,
                "speed": 120,
                "resource": 300,
                "resource_regen": 0,
                "skills": [
                    {"id": "burst", "type": "attack", "power": 1.0, "cost": 100, "priority": 5},
                    {"id": "poke", "type": "attack", "power": 0.05, "priority": 1},
                ],
            }
        )
        record = simulate(spec, 0)
        self.assertEqual(record["winner"], "A")
        self.assertTrue(record["winner_was_behind"])
        self.assertGreaterEqual(record["lead_flips"], 1)

    def test_uncontested_winner_is_not_flagged_as_a_comeback(self) -> None:
        spec = scenario()
        spec["teams"]["B"][0]["atk"] = 0
        record = simulate(spec, 0)
        self.assertEqual(record["winner"], "A")
        self.assertFalse(record["winner_was_behind"])
        self.assertEqual(record["lead_flips"], 0)


class ValidationTests(unittest.TestCase):
    def test_rejects_non_positive_health(self) -> None:
        spec = scenario()
        spec["teams"]["A"][0]["hp"] = 0
        with self.assertRaises(ValueError):
            simulate(spec, 0)

    def test_rejects_out_of_range_probability(self) -> None:
        spec = scenario()
        spec["teams"]["A"][0]["crit_chance"] = 1.5
        with self.assertRaises(ValueError):
            simulate(spec, 0)

    def test_rejects_unknown_damage_model(self) -> None:
        with self.assertRaises(ValueError):
            simulate(scenario(damage_model="magic"), 0)

    def test_rejects_wrong_team_count(self) -> None:
        spec = scenario()
        spec["teams"]["C"] = spec["teams"]["A"]
        with self.assertRaises(ValueError):
            simulate(spec, 0)

    def test_rejects_unknown_status_stat(self) -> None:
        spec = scenario()
        spec["teams"]["A"][0]["skills"] = [
            {"id": "x", "type": "buff", "targets": "self",
             "status": {"id": "x", "duration": 1, "stat_mults": {"luck": 2}}}
        ]
        with self.assertRaises(ValueError):
            simulate(spec, 0)


if __name__ == "__main__":
    unittest.main()
