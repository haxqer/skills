#!/usr/bin/env python3
"""Deterministic, data-driven combat simulator used as the tuning substrate.

The engine turns a JSON scenario into a reproducible battle record. Given the
same scenario and the same seed it always produces the same record, which is
what makes paired comparison, convergence testing, and regression diffing
meaningful.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from typing import Any

DAMAGE_MODELS = ("subtract", "ratio", "multiplicative")
TARGET_MODES = (
    "enemy_single",
    "enemy_all",
    "enemy_random",
    "ally_lowest_hp_pct",
    "ally_all",
    "self",
)
TARGET_POLICIES = (
    "lowest_hp",
    "lowest_hp_pct",
    "highest_hp",
    "highest_atk",
    "lowest_def",
    "first",
    "random",
)
SKILL_POLICIES = ("priority", "weighted_random", "cycle", "max_damage")
STACK_RULES = ("refresh", "stack", "ignore")
SKILL_TYPES = ("attack", "heal", "buff", "debuff")

BASIC_ATTACK: dict[str, Any] = {
    "id": "basic_attack",
    "type": "attack",
    "power": 1.0,
    "targets": "enemy_single",
}


def _require_finite(name: str, value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return float(value)


def _require_probability(name: str, value: Any) -> float:
    number = _require_finite(name, value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {number}")
    return number


def _require_choice(name: str, value: Any, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {value!r}")
    return str(value)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class Skill:
    """A resolved skill definition with validated defaults."""

    __slots__ = (
        "id",
        "type",
        "power",
        "flat",
        "hits",
        "cooldown",
        "cost",
        "targets",
        "target_policy",
        "priority",
        "weight",
        "status",
        "cooldown_left",
    )

    def __init__(self, spec: dict[str, Any], owner_id: str, default_policy: str) -> None:
        if "id" not in spec:
            raise ValueError(f"{owner_id}: every skill needs an id")
        self.id = str(spec["id"])
        label = f"{owner_id}.{self.id}"
        self.type = _require_choice(f"{label}.type", spec.get("type", "attack"), SKILL_TYPES)
        self.power = _require_finite(f"{label}.power", spec.get("power", 1.0))
        self.flat = _require_finite(f"{label}.flat", spec.get("flat", 0.0))
        self.hits = int(spec.get("hits", 1))
        if self.hits < 1:
            raise ValueError(f"{label}.hits must be at least 1")
        self.cooldown = int(spec.get("cooldown", 0))
        if self.cooldown < 0:
            raise ValueError(f"{label}.cooldown must not be negative")
        self.cost = _require_finite(f"{label}.cost", spec.get("cost", 0.0))
        if self.cost < 0:
            raise ValueError(f"{label}.cost must not be negative")
        default_targets = "ally_lowest_hp_pct" if self.type == "heal" else "enemy_single"
        if self.type == "buff":
            default_targets = "self"
        self.targets = _require_choice(
            f"{label}.targets", spec.get("targets", default_targets), TARGET_MODES
        )
        self.target_policy = _require_choice(
            f"{label}.target_policy", spec.get("target_policy", default_policy), TARGET_POLICIES
        )
        self.priority = _require_finite(f"{label}.priority", spec.get("priority", 0.0))
        self.weight = _require_finite(f"{label}.weight", spec.get("weight", 1.0))
        if self.weight < 0:
            raise ValueError(f"{label}.weight must not be negative")
        self.status = _validate_status(spec.get("status"), label)
        self.cooldown_left = 0


def _validate_status(spec: Any, label: str) -> dict[str, Any] | None:
    if spec is None:
        return None
    if not isinstance(spec, dict):
        raise ValueError(f"{label}.status must be an object")
    status: dict[str, Any] = {
        "id": str(spec.get("id", f"{label}.status")),
        "duration": int(spec.get("duration", 1)),
        "dot": _require_finite(f"{label}.status.dot", spec.get("dot", 0.0)),
        "dot_power": _require_finite(f"{label}.status.dot_power", spec.get("dot_power", 0.0)),
        "shield": _require_finite(f"{label}.status.shield", spec.get("shield", 0.0)),
        "stun": bool(spec.get("stun", False)),
        "stack_rule": _require_choice(
            f"{label}.status.stack_rule", spec.get("stack_rule", "refresh"), STACK_RULES
        ),
        "max_stacks": int(spec.get("max_stacks", 1)),
        "stat_mults": {},
    }
    if status["duration"] < 1:
        raise ValueError(f"{label}.status.duration must be at least 1")
    if status["max_stacks"] < 1:
        raise ValueError(f"{label}.status.max_stacks must be at least 1")
    mults = spec.get("stat_mults", {})
    if not isinstance(mults, dict):
        raise ValueError(f"{label}.status.stat_mults must be an object")
    for stat_name, value in mults.items():
        if stat_name not in ("atk", "def", "speed", "accuracy", "dodge", "crit_chance"):
            raise ValueError(f"{label}.status.stat_mults has unknown stat {stat_name!r}")
        status["stat_mults"][stat_name] = _require_finite(
            f"{label}.status.stat_mults.{stat_name}", value
        )
    return status


class Unit:
    """Runtime state for one combatant."""

    __slots__ = (
        "uid",
        "unit_id",
        "team",
        "role",
        "index",
        "base",
        "max_hp",
        "hp",
        "resource",
        "max_resource",
        "resource_regen",
        "crit_mult",
        "skills",
        "skill_policy",
        "target_policy",
        "statuses",
        "cycle_index",
        "alive",
        "death_round",
        "stats",
    )

    def __init__(self, spec: dict[str, Any], team: str, uid: str, index: int) -> None:
        self.uid = uid
        self.unit_id = str(spec.get("id", uid))
        self.team = team
        self.role = str(spec.get("role", ""))
        self.index = index
        self.max_hp = _require_finite(f"{uid}.hp", spec.get("hp", 0.0))
        if self.max_hp <= 0:
            raise ValueError(f"{uid}.hp must be positive")
        self.hp = self.max_hp
        self.base = {
            "atk": _require_finite(f"{uid}.atk", spec.get("atk", 0.0)),
            "def": _require_finite(f"{uid}.def", spec.get("def", 0.0)),
            "speed": _require_finite(f"{uid}.speed", spec.get("speed", 100.0)),
            "accuracy": _require_probability(f"{uid}.accuracy", spec.get("accuracy", 1.0)),
            "dodge": _require_probability(f"{uid}.dodge", spec.get("dodge", 0.0)),
            "crit_chance": _require_probability(
                f"{uid}.crit_chance", spec.get("crit_chance", 0.0)
            ),
        }
        self.crit_mult = _require_finite(f"{uid}.crit_mult", spec.get("crit_mult", 1.5))
        self.max_resource = _require_finite(f"{uid}.resource", spec.get("resource", 0.0))
        self.resource = self.max_resource
        self.resource_regen = _require_finite(
            f"{uid}.resource_regen", spec.get("resource_regen", 0.0)
        )
        self.target_policy = _require_choice(
            f"{uid}.target_policy", spec.get("target_policy", "lowest_hp"), TARGET_POLICIES
        )
        self.skill_policy = _require_choice(
            f"{uid}.skill_policy", spec.get("skill_policy", "priority"), SKILL_POLICIES
        )
        skill_specs = spec.get("skills") or [BASIC_ATTACK]
        if not isinstance(skill_specs, list) or not skill_specs:
            raise ValueError(f"{uid}.skills must be a non-empty list")
        self.skills = [Skill(item, uid, self.target_policy) for item in skill_specs]
        self.statuses: list[dict[str, Any]] = []
        self.cycle_index = 0
        self.alive = True
        self.death_round: int | None = None
        self.stats = {
            "damage_dealt": 0.0,
            "overkill": 0.0,
            "damage_taken": 0.0,
            "damage_absorbed": 0.0,
            "healing_done": 0.0,
            "overhealing": 0.0,
            "actions": 0,
            "hits": 0,
            "misses": 0,
            "crits": 0,
            "kills": 0,
        }

    def stat(self, name: str) -> float:
        value = self.base[name]
        for status in self.statuses:
            mult = status["stat_mults"].get(name)
            if mult is not None:
                value *= mult
        if name in ("accuracy", "dodge", "crit_chance"):
            return _clamp(value, 0.0, 1.0)
        return max(0.0, value)

    @property
    def hp_fraction(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0

    @property
    def stunned(self) -> bool:
        return any(status["stun"] for status in self.statuses)

    @property
    def shield(self) -> float:
        return sum(status["shield"] for status in self.statuses)


def _expand_units(team: str, specs: Any) -> list[Unit]:
    if not isinstance(specs, list) or not specs:
        raise ValueError(f"team {team!r} must contain a non-empty list of units")
    units: list[Unit] = []
    seen: dict[str, int] = {}
    for spec in specs:
        if not isinstance(spec, dict):
            raise ValueError(f"team {team!r} contains a non-object unit entry")
        count = int(spec.get("count", 1))
        if count < 1:
            raise ValueError(f"team {team!r} unit count must be at least 1")
        base_id = str(spec.get("id", f"unit{len(units)}"))
        for _ in range(count):
            seen[base_id] = seen.get(base_id, 0) + 1
            suffix = "" if seen[base_id] == 1 else f"#{seen[base_id]}"
            uid = f"{team}/{base_id}{suffix}"
            units.append(Unit(spec, team, uid, len(units)))
    return units


def mitigate(raw: float, defense: float, model: str, params: dict[str, Any]) -> float:
    """Apply one of the three standard mitigation curves."""
    if model == "subtract":
        floor_fraction = float(params.get("min_damage_fraction", 0.05))
        return max(raw * floor_fraction, raw - defense)
    if model == "ratio":
        constant = float(params.get("defense_constant", 100.0))
        if constant <= 0:
            raise ValueError("defense_constant must be positive")
        return raw * constant / (constant + max(0.0, defense))
    coefficient = float(params.get("defense_coefficient", 0.001))
    cap = float(params.get("mitigation_cap", 0.75))
    return raw * (1.0 - _clamp(defense * coefficient, 0.0, cap))


class Battle:
    """One seeded battle between two teams."""

    def __init__(self, scenario: dict[str, Any], seed: int) -> None:
        self.scenario = scenario
        self.seed = int(seed)
        self.rng = random.Random(self.seed)
        self.max_rounds = int(scenario.get("max_rounds", 50))
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")
        self.seconds_per_round = _require_finite(
            "seconds_per_round", scenario.get("seconds_per_round", 1.0)
        )
        self.damage_model = _require_choice(
            "damage_model", scenario.get("damage_model", "subtract"), DAMAGE_MODELS
        )
        self.model_params = scenario.get("damage_model_params", {}) or {}
        self.damage_variance = _require_probability(
            "damage_variance", scenario.get("damage_variance", 0.0)
        )
        teams = scenario.get("teams")
        if not isinstance(teams, dict) or len(teams) != 2:
            raise ValueError("scenario.teams must be an object with exactly two teams")
        self.team_names = list(teams.keys())
        self.units: list[Unit] = []
        for team in self.team_names:
            self.units.extend(_expand_units(team, teams[team]))
        self.by_team = {
            team: [unit for unit in self.units if unit.team == team] for team in self.team_names
        }
        self.round = 0
        self.first_death: tuple[str, int] | None = None
        self.lead_flips = 0
        self.trailed: set[str] = set()
        self.trace: list[str] = []
        self.record_trace = bool(scenario.get("trace", False))

    # -- helpers ---------------------------------------------------------

    def _living(self, team: str) -> list[Unit]:
        return [unit for unit in self.by_team[team] if unit.alive]

    def _enemies_of(self, unit: Unit) -> list[Unit]:
        other = self.team_names[0] if unit.team == self.team_names[1] else self.team_names[1]
        return self._living(other)

    def _team_hp_fraction(self, team: str) -> float:
        total = sum(unit.max_hp for unit in self.by_team[team])
        current = sum(max(0.0, unit.hp) for unit in self.by_team[team])
        return current / total if total > 0 else 0.0

    def _log(self, message: str) -> None:
        if self.record_trace:
            self.trace.append(f"r{self.round}: {message}")

    # -- selection -------------------------------------------------------

    def _pick_target(self, candidates: list[Unit], policy: str) -> Unit:
        if policy == "random":
            return candidates[self.rng.randrange(len(candidates))]
        if policy == "first":
            return candidates[0]
        keys = {
            "lowest_hp": lambda unit: (unit.hp, unit.index),
            "lowest_hp_pct": lambda unit: (unit.hp_fraction, unit.index),
            "highest_hp": lambda unit: (-unit.hp, unit.index),
            "highest_atk": lambda unit: (-unit.stat("atk"), unit.index),
            "lowest_def": lambda unit: (unit.stat("def"), unit.index),
        }
        return min(candidates, key=keys[policy])

    def _resolve_targets(self, actor: Unit, skill: Skill) -> list[Unit]:
        if skill.targets == "self":
            return [actor]
        if skill.targets in ("enemy_single", "enemy_all", "enemy_random"):
            pool = self._enemies_of(actor)
            if not pool:
                return []
            if skill.targets == "enemy_all":
                return pool
            if skill.targets == "enemy_random":
                return [pool[self.rng.randrange(len(pool))]]
            return [self._pick_target(pool, skill.target_policy)]
        pool = self._living(actor.team)
        if not pool:
            return []
        if skill.targets == "ally_all":
            return pool
        return [self._pick_target(pool, "lowest_hp_pct")]

    def _has_targets(self, actor: Unit, skill: Skill) -> bool:
        """Availability check that never consumes randomness."""
        if skill.targets == "self":
            return True
        if skill.targets.startswith("enemy"):
            return bool(self._enemies_of(actor))
        return bool(self._living(actor.team))

    def _usable(self, actor: Unit) -> list[Skill]:
        usable = []
        for skill in actor.skills:
            if skill.cooldown_left > 0 or skill.cost > actor.resource:
                continue
            if not self._has_targets(actor, skill):
                continue
            usable.append(skill)
        return usable

    def _estimate_damage(self, actor: Unit, skill: Skill) -> float:
        if skill.type != "attack":
            return 0.0
        targets = self._resolve_targets(actor, skill)
        if not targets:
            return 0.0
        raw = actor.stat("atk") * skill.power + skill.flat
        total = 0.0
        for target in targets:
            per_hit = mitigate(raw, target.stat("def"), self.damage_model, self.model_params)
            total += min(target.hp, per_hit * skill.hits)
        return total

    def _choose_skill(self, actor: Unit) -> Skill | None:
        usable = self._usable(actor)
        if not usable:
            return None
        policy = actor.skill_policy
        if policy == "priority":
            # max() keeps the first maximal element, so ties fall back to declaration order.
            return max(usable, key=lambda skill: skill.priority)
        if policy == "cycle":
            chosen = usable[actor.cycle_index % len(usable)]
            actor.cycle_index += 1
            return chosen
        if policy == "max_damage":
            scored = [(self._estimate_damage(actor, skill), -i) for i, skill in enumerate(usable)]
            best_index = -max(scored)[1]
            return usable[best_index]
        total_weight = sum(skill.weight for skill in usable)
        if total_weight <= 0:
            return usable[0]
        roll = self.rng.random() * total_weight
        cumulative = 0.0
        for skill in usable:
            cumulative += skill.weight
            if roll < cumulative:
                return skill
        return usable[-1]

    # -- resolution ------------------------------------------------------

    def _apply_status(self, target: Unit, template: dict[str, Any]) -> None:
        if template["stack_rule"] == "ignore" and any(
            status["id"] == template["id"] for status in target.statuses
        ):
            return
        existing = [status for status in target.statuses if status["id"] == template["id"]]
        if template["stack_rule"] == "refresh" and existing:
            existing[0]["remaining"] = template["duration"]
            return
        if len(existing) >= template["max_stacks"]:
            oldest = min(existing, key=lambda status: status["remaining"])
            oldest["remaining"] = template["duration"]
            return
        instance = dict(template)
        instance["stat_mults"] = dict(template["stat_mults"])
        instance["remaining"] = template["duration"]
        target.statuses.append(instance)

    def _deal_damage(self, source: Unit | None, target: Unit, amount: float) -> None:
        if amount <= 0 or not target.alive:
            return
        absorbed = 0.0
        remaining = amount
        for status in target.statuses:
            if status["shield"] <= 0 or remaining <= 0:
                continue
            used = min(status["shield"], remaining)
            status["shield"] -= used
            remaining -= used
            absorbed += used
        applied = min(target.hp, remaining)
        overkill = remaining - applied
        target.hp -= applied
        target.stats["damage_taken"] += applied
        target.stats["damage_absorbed"] += absorbed
        if source is not None:
            source.stats["damage_dealt"] += applied
            source.stats["overkill"] += overkill
        if target.hp <= 0:
            target.hp = 0.0
            target.alive = False
            target.death_round = self.round
            target.statuses.clear()
            if source is not None:
                source.stats["kills"] += 1
            if self.first_death is None:
                self.first_death = (target.team, self.round)
            self._log(f"{target.uid} dies")

    def _resolve_attack(self, actor: Unit, skill: Skill, targets: list[Unit]) -> None:
        raw_base = actor.stat("atk") * skill.power + skill.flat
        for target in targets:
            for _ in range(skill.hits):
                if not target.alive or not actor.alive:
                    break
                hit_chance = _clamp(actor.stat("accuracy") - target.stat("dodge"), 0.0, 1.0)
                if self.rng.random() >= hit_chance:
                    actor.stats["misses"] += 1
                    self._log(f"{actor.uid} misses {target.uid}")
                    continue
                actor.stats["hits"] += 1
                raw = raw_base
                if self.rng.random() < actor.stat("crit_chance"):
                    raw *= actor.crit_mult
                    actor.stats["crits"] += 1
                if self.damage_variance > 0:
                    low = 1.0 - self.damage_variance
                    high = 1.0 + self.damage_variance
                    raw *= low + (high - low) * self.rng.random()
                damage = mitigate(raw, target.stat("def"), self.damage_model, self.model_params)
                self._deal_damage(actor, target, damage)
                if skill.status is not None and target.alive:
                    self._apply_status(target, skill.status)

    def _resolve_heal(self, actor: Unit, skill: Skill, targets: list[Unit]) -> None:
        amount = actor.stat("atk") * skill.power + skill.flat
        for target in targets:
            missing = target.max_hp - target.hp
            healed = min(missing, amount)
            target.hp += healed
            actor.stats["healing_done"] += healed
            actor.stats["overhealing"] += amount - healed
            if skill.status is not None:
                self._apply_status(target, skill.status)

    def _take_turn(self, actor: Unit) -> None:
        actor.resource = min(actor.max_resource, actor.resource + actor.resource_regen)
        for skill in actor.skills:
            if skill.cooldown_left > 0:
                skill.cooldown_left -= 1
        if actor.stunned:
            self._log(f"{actor.uid} is stunned")
            return
        skill = self._choose_skill(actor)
        if skill is None:
            return
        targets = self._resolve_targets(actor, skill)
        if not targets:
            return
        actor.resource -= skill.cost
        skill.cooldown_left = skill.cooldown
        actor.stats["actions"] += 1
        self._log(f"{actor.uid} uses {skill.id} on {','.join(t.uid for t in targets)}")
        if skill.type == "attack":
            self._resolve_attack(actor, skill, targets)
        elif skill.type == "heal":
            self._resolve_heal(actor, skill, targets)
        else:
            if skill.status is not None:
                for target in targets:
                    self._apply_status(target, skill.status)

    def _tick_statuses(self, actor: Unit) -> None:
        expired = []
        for status in actor.statuses:
            dot = status["dot"] + status["dot_power"] * actor.max_hp
            if dot > 0:
                self._deal_damage(None, actor, dot)
                if not actor.alive:
                    return
            status["remaining"] -= 1
            if status["remaining"] <= 0:
                expired.append(status)
        for status in expired:
            actor.statuses.remove(status)

    def _finished(self) -> bool:
        return any(not self._living(team) for team in self.team_names)

    # -- main loop -------------------------------------------------------

    def run(self) -> dict[str, Any]:
        leader = self._current_leader()
        while self.round < self.max_rounds and not self._finished():
            self.round += 1
            order = sorted(
                (unit for unit in self.units if unit.alive),
                key=lambda unit: (-unit.stat("speed"), unit.team, unit.index),
            )
            for actor in order:
                if not actor.alive or self._finished():
                    continue
                self._tick_statuses(actor)
                if not actor.alive:
                    continue
                self._take_turn(actor)
            new_leader = self._current_leader()
            if new_leader == "tie":
                continue
            self.trailed.update(team for team in self.team_names if team != new_leader)
            # Only a change between two real leaders is a flip; the opening tie is not.
            if leader not in ("tie", new_leader):
                self.lead_flips += 1
            leader = new_leader
        return self._result()

    def _current_leader(self) -> str:
        fractions = {team: self._team_hp_fraction(team) for team in self.team_names}
        first, second = self.team_names
        if abs(fractions[first] - fractions[second]) < 1e-9:
            return "tie"
        return first if fractions[first] > fractions[second] else second

    def _result(self) -> dict[str, Any]:
        alive = {team: bool(self._living(team)) for team in self.team_names}
        first, second = self.team_names
        timeout = alive[first] and alive[second]
        if alive[first] and not alive[second]:
            winner = first
        elif alive[second] and not alive[first]:
            winner = second
        else:
            winner = "draw"
        fractions = {team: self._team_hp_fraction(team) for team in self.team_names}
        margin = abs(fractions[first] - fractions[second])
        units: dict[str, Any] = {}
        for unit in self.units:
            entry = {
                "team": unit.team,
                "unit_id": unit.unit_id,
                "role": unit.role,
                "survived": unit.alive,
                "death_round": unit.death_round,
                "hp_fraction": unit.hp_fraction,
            }
            entry.update(unit.stats)
            units[unit.uid] = entry
        return {
            "seed": self.seed,
            "winner": winner,
            "timeout": timeout,
            "rounds": self.round,
            "duration": self.round * self.seconds_per_round,
            "team_hp_fraction": fractions,
            "margin": margin,
            "first_death_team": self.first_death[0] if self.first_death else None,
            "first_death_round": self.first_death[1] if self.first_death else None,
            "lead_flips": self.lead_flips,
            "winner_was_behind": winner in self.trailed,
            "winner_hp_fraction": fractions.get(winner, 0.0) if winner != "draw" else 0.0,
            "units": units,
            "trace": self.trace if self.record_trace else None,
        }


def simulate(scenario: dict[str, Any], seed: int) -> dict[str, Any]:
    """Run one battle and return its record."""
    return Battle(scenario, seed).run()


def load_scenario(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        scenario = json.load(handle)
    if not isinstance(scenario, dict):
        raise ValueError("scenario file must contain a JSON object")
    return scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a single seeded battle and print its record.",
        epilog="Use sim_runner.py for batches; this entry point is for inspecting one battle.",
    )
    parser.add_argument("scenario", help="path to a scenario JSON file")
    parser.add_argument("--seed", type=int, default=0, help="random seed (default: 0)")
    parser.add_argument("--trace", action="store_true", help="record a per-action trace")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scenario = load_scenario(args.scenario)
        if args.trace:
            scenario = {**scenario, "trace": True}
        record = simulate(scenario, args.seed)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    json.dump(record, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
