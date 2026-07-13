#!/usr/bin/env python3
"""Deterministic baseline calculators for common game-balance models."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections.abc import Iterable
from statistics import NormalDist
from typing import Any


def _require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def _require_probability(name: str, value: float, *, allow_zero: bool = True) -> None:
    _require_finite(name, value)
    lower_ok = value >= 0 if allow_zero else value > 0
    if not lower_ok or value > 1:
        bracket = "[0, 1]" if allow_zero else "(0, 1]"
        raise ValueError(f"{name} must be in {bracket}")


def calculate_curve(
    kind: str,
    count: int,
    start_index: int = 1,
    **parameters: float,
) -> dict[str, Any]:
    if count < 1:
        raise ValueError("count must be at least 1")

    rows: list[dict[str, float | int]] = []
    for offset in range(count):
        index = start_index + offset
        if kind == "linear":
            base = parameters["base"]
            increment = parameters["increment"]
            value = base + increment * offset
            formula = "base + increment * offset"
        elif kind == "geometric":
            base = parameters["base"]
            rate = parameters["rate"]
            if 1 + rate < 0:
                raise ValueError("geometric rate must be at least -1")
            value = base * (1 + rate) ** offset
            formula = "base * (1 + rate) ** offset"
        elif kind == "power":
            scale = parameters["scale"]
            exponent = parameters["exponent"]
            x = index + parameters["offset"]
            if x < 0 and not float(exponent).is_integer():
                raise ValueError("power curve base cannot be negative for a fractional exponent")
            if x == 0 and exponent < 0:
                raise ValueError("power curve base cannot be zero for a negative exponent")
            value = scale * x**exponent
            formula = "scale * (index + offset) ** exponent"
        elif kind == "logistic":
            lower = parameters["lower"]
            upper = parameters["upper"]
            midpoint = parameters["midpoint"]
            steepness = parameters["steepness"]
            z = steepness * (index - midpoint)
            if z >= 0:
                logistic_fraction = 1 / (1 + math.exp(-z))
            else:
                exp_z = math.exp(z)
                logistic_fraction = exp_z / (1 + exp_z)
            value = lower + (upper - lower) * logistic_fraction
            formula = "lower + (upper - lower) / (1 + exp(-steepness * (index - midpoint)))"
        else:
            raise ValueError(f"unsupported curve kind: {kind}")

        _require_finite("curve value", value)
        rows.append({"index": index, "value": value})

    return {
        "command": "curve",
        "kind": kind,
        "formula": formula,
        "parameters": parameters,
        "rows": rows,
    }


def _round_to_step(value: float, step: float) -> float:
    if step == 0:
        return value
    return math.floor(value / step + 0.5) * step


def calculate_progression(
    *,
    base_cost: float,
    cost_growth: float,
    count: int,
    start_index: int = 1,
    income_per_period: float | None = None,
    income_growth: float = 0.0,
    round_to: float = 0.0,
) -> dict[str, Any]:
    for name, value in (
        ("base_cost", base_cost),
        ("cost_growth", cost_growth),
        ("income_growth", income_growth),
        ("round_to", round_to),
    ):
        _require_finite(name, value)
    if count < 1:
        raise ValueError("count must be at least 1")
    if base_cost < 0 or round_to < 0 or cost_growth < -1:
        raise ValueError("base_cost and round_to cannot be negative; cost_growth must be at least -1")
    if income_per_period is not None:
        _require_finite("income_per_period", income_per_period)
        if income_per_period <= 0:
            raise ValueError("income_per_period must be positive")
        if income_growth <= -1 and count > 1:
            raise ValueError("income_growth must be greater than -1 when count is greater than 1")

    rows: list[dict[str, float | int | None]] = []
    cumulative_cost = 0.0
    cumulative_periods = 0.0
    for offset in range(count):
        raw_cost = base_cost * (1 + cost_growth) ** offset
        cost = _round_to_step(raw_cost, round_to)
        cumulative_cost += cost

        if income_per_period is None:
            income = None
            periods = None
            cumulative_period_value = None
        else:
            income = income_per_period * (1 + income_growth) ** offset
            periods = cost / income
            cumulative_periods += periods
            cumulative_period_value = cumulative_periods

        rows.append({
            "index": start_index + offset,
            "cost": cost,
            "cumulative_cost": cumulative_cost,
            "income_per_period": income,
            "periods_for_step": periods,
            "cumulative_periods": cumulative_period_value,
        })

    return {
        "command": "progression",
        "model": "geometric step cost with optional geometric income",
        "inputs": {
            "base_cost": base_cost,
            "cost_growth": cost_growth,
            "count": count,
            "start_index": start_index,
            "income_per_period": income_per_period,
            "income_growth": income_growth,
            "round_to": round_to,
        },
        "rows": rows,
    }


def calculate_combat(
    *,
    health: float,
    damage: float,
    attack_rate: float,
    accuracy: float = 1.0,
    crit_chance: float = 0.0,
    crit_multiplier: float = 1.0,
    flat_reduction: float = 0.0,
    damage_reduction: float = 0.0,
) -> dict[str, Any]:
    for name, value in (
        ("health", health),
        ("damage", damage),
        ("attack_rate", attack_rate),
        ("crit_multiplier", crit_multiplier),
        ("flat_reduction", flat_reduction),
    ):
        _require_finite(name, value)
    if health <= 0 or damage < 0 or attack_rate <= 0 or crit_multiplier < 0 or flat_reduction < 0:
        raise ValueError("health and attack_rate must be positive; damage and reductions cannot be negative")
    _require_probability("accuracy", accuracy)
    _require_probability("crit_chance", crit_chance)
    _require_probability("damage_reduction", damage_reduction)

    normal_on_hit = max(0.0, damage - flat_reduction) * (1 - damage_reduction)
    crit_on_hit = max(0.0, damage * crit_multiplier - flat_reduction) * (1 - damage_reduction)
    expected_landed_hit = (1 - crit_chance) * normal_on_hit + crit_chance * crit_on_hit
    expected_damage_per_attempt = accuracy * expected_landed_hit
    expected_dps = attack_rate * expected_damage_per_attempt

    return {
        "command": "combat",
        "calculation_order": "crit -> flat_reduction -> percentage_reduction -> accuracy -> attack_rate",
        "inputs": {
            "health": health,
            "damage": damage,
            "attack_rate": attack_rate,
            "accuracy": accuracy,
            "crit_chance": crit_chance,
            "crit_multiplier": crit_multiplier,
            "flat_reduction": flat_reduction,
            "damage_reduction": damage_reduction,
        },
        "metrics": {
            "normal_damage_on_landed_hit": normal_on_hit,
            "critical_damage_on_landed_hit": crit_on_hit,
            "expected_damage_per_landed_hit": expected_landed_hit,
            "expected_damage_per_attack_attempt": expected_damage_per_attempt,
            "expected_dps": expected_dps,
            "expected_ttk_seconds": health / expected_dps if expected_dps > 0 else None,
            "normal_landed_hits_to_kill": math.ceil(health / normal_on_hit) if normal_on_hit > 0 else None,
            "critical_landed_hits_to_kill": math.ceil(health / crit_on_hit) if crit_on_hit > 0 else None,
        },
    }


def _geometric_quantile(chance: float, quantile: float, hard_pity: int | None) -> int:
    if chance == 1:
        return 1
    if quantile == 1:
        if hard_pity is None:
            raise ValueError("quantiles must be less than 1 without hard_pity")
        return hard_pity
    natural_attempt = math.ceil(math.log1p(-quantile) / math.log1p(-chance))
    return min(natural_attempt, hard_pity) if hard_pity is not None else natural_attempt


def calculate_drop(
    *,
    chance: float,
    hard_pity: int | None = None,
    attempts: Iterable[int] = (1, 10, 50, 100),
    quantiles: Iterable[float] = (0.5, 0.9, 0.95, 0.99),
    cost_per_attempt: float = 0.0,
) -> dict[str, Any]:
    _require_probability("chance", chance, allow_zero=False)
    _require_finite("cost_per_attempt", cost_per_attempt)
    if hard_pity is not None and hard_pity < 1:
        raise ValueError("hard_pity must be at least 1")
    if cost_per_attempt < 0:
        raise ValueError("cost_per_attempt cannot be negative")

    attempt_list = list(attempts)
    if not attempt_list or any(attempt < 1 for attempt in attempt_list):
        raise ValueError("attempts must contain positive integers")
    quantile_list = list(quantiles)
    for quantile in quantile_list:
        _require_probability("quantile", quantile, allow_zero=False)

    if hard_pity is None:
        expected_attempts = 1 / chance
    else:
        expected_attempts = (1 - (1 - chance) ** hard_pity) / chance

    probability_by_attempt: dict[str, float] = {}
    for attempt in attempt_list:
        if hard_pity is not None and attempt >= hard_pity:
            probability = 1.0
        else:
            probability = 1 - (1 - chance) ** attempt
        probability_by_attempt[str(attempt)] = probability

    attempts_by_quantile = {
        f"p{quantile * 100:g}": _geometric_quantile(chance, quantile, hard_pity)
        for quantile in quantile_list
    }

    return {
        "command": "drop",
        "model": "independent chance per attempt with optional hard guarantee",
        "inputs": {
            "chance": chance,
            "hard_pity": hard_pity,
            "cost_per_attempt": cost_per_attempt,
        },
        "metrics": {
            "expected_attempts": expected_attempts,
            "expected_cost": expected_attempts * cost_per_attempt,
            "attempts_by_quantile": attempts_by_quantile,
            "probability_by_attempt": probability_by_attempt,
            "maximum_attempts": hard_pity,
        },
    }


def calculate_economy(
    *,
    source_per_period: float,
    mandatory_sink_per_period: float,
    starting_balance: float,
    goal_cost: float,
    horizon: int,
) -> dict[str, Any]:
    for name, value in (
        ("source_per_period", source_per_period),
        ("mandatory_sink_per_period", mandatory_sink_per_period),
        ("starting_balance", starting_balance),
        ("goal_cost", goal_cost),
    ):
        _require_finite(name, value)
    if source_per_period < 0 or mandatory_sink_per_period < 0 or goal_cost < 0:
        raise ValueError("sources, sinks, and goal_cost cannot be negative")
    if horizon < 0:
        raise ValueError("horizon cannot be negative")

    net_flow = source_per_period - mandatory_sink_per_period
    if starting_balance >= goal_cost:
        periods_to_goal: int | None = 0
    elif net_flow > 0:
        periods_to_goal = math.ceil((goal_cost - starting_balance) / net_flow)
    else:
        periods_to_goal = None

    return {
        "command": "economy",
        "inputs": {
            "source_per_period": source_per_period,
            "mandatory_sink_per_period": mandatory_sink_per_period,
            "starting_balance": starting_balance,
            "goal_cost": goal_cost,
            "horizon": horizon,
        },
        "metrics": {
            "net_flow_per_period": net_flow,
            "mandatory_sink_coverage": (
                mandatory_sink_per_period / source_per_period if source_per_period > 0 else None
            ),
            "periods_to_goal": periods_to_goal,
            "balance_at_horizon": starting_balance + net_flow * horizon,
        },
    }


def calculate_rating(
    *,
    rating_a: float,
    rating_b: float,
    scale: float = 400.0,
    score_a: float | None = None,
    k_factor: float = 32.0,
) -> dict[str, Any]:
    for name, value in (
        ("rating_a", rating_a),
        ("rating_b", rating_b),
        ("scale", scale),
        ("k_factor", k_factor),
    ):
        _require_finite(name, value)
    if scale <= 0 or k_factor < 0:
        raise ValueError("scale must be positive and k_factor cannot be negative")
    if score_a is not None:
        _require_probability("score_a", score_a)

    exponent = (rating_b - rating_a) / scale
    if exponent > 308:
        expected_a = 0.0
    elif exponent < -308:
        expected_a = 1.0
    else:
        expected_a = 1 / (1 + 10**exponent)

    if score_a is None:
        delta_a = None
        updated_a = None
        updated_b = None
    else:
        delta_a = k_factor * (score_a - expected_a)
        updated_a = rating_a + delta_a
        updated_b = rating_b - delta_a

    return {
        "command": "rating",
        "model": "Elo-style two-player expectation and zero-sum update",
        "inputs": {
            "rating_a": rating_a,
            "rating_b": rating_b,
            "scale": scale,
            "score_a": score_a,
            "k_factor": k_factor,
        },
        "metrics": {
            "expected_score_a": expected_a,
            "expected_score_b": 1 - expected_a,
            "rating_delta_a": delta_a,
            "updated_rating_a": updated_a,
            "updated_rating_b": updated_b,
        },
    }


def calculate_proportion(
    *,
    successes: int,
    trials: int,
    confidence: float = 0.95,
    target_margin: float | None = None,
) -> dict[str, Any]:
    if trials < 1 or successes < 0 or successes > trials:
        raise ValueError("trials must be positive and successes must be between 0 and trials")
    _require_probability("confidence", confidence, allow_zero=False)
    if confidence == 1:
        raise ValueError("confidence must be less than 1")
    if target_margin is not None:
        _require_probability("target_margin", target_margin, allow_zero=False)
        if target_margin == 1:
            raise ValueError("target_margin must be less than 1")

    estimate = successes / trials
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    z_squared = z**2
    denominator = 1 + z_squared / trials
    center = (estimate + z_squared / (2 * trials)) / denominator
    half_width = (
        z
        / denominator
        * math.sqrt(estimate * (1 - estimate) / trials + z_squared / (4 * trials**2))
    )
    conservative_sample_size = (
        math.ceil(z_squared * 0.25 / target_margin**2) if target_margin is not None else None
    )

    return {
        "command": "proportion",
        "model": "Wilson score interval and conservative independent-sample planning",
        "inputs": {
            "successes": successes,
            "trials": trials,
            "confidence": confidence,
            "target_margin": target_margin,
        },
        "metrics": {
            "estimate": estimate,
            "z_value": z,
            "wilson_lower": max(0.0, center - half_width),
            "wilson_upper": min(1.0, center + half_width),
            "wilson_half_width": half_width,
            "conservative_sample_size": conservative_sample_size,
        },
        "warning": "Adjust sample planning for clustering, repeated players, multiple comparisons, and experiment design.",
    }


def _flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            rows.extend(_flatten(child, path))
    else:
        rows.append((prefix, value))
    return rows


def _normalize_output_numbers(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_output_numbers(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_normalize_output_numbers(child) for child in value]
    if isinstance(value, float) and math.isfinite(value):
        return float(f"{value:.15g}")
    return value


def emit(payload: dict[str, Any], output_format: str) -> None:
    payload = _normalize_output_numbers(payload)
    if output_format == "json":
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return

    writer = csv.writer(sys.stdout)
    if payload.get("command") in {"curve", "progression"}:
        fieldnames = list(payload["rows"][0].keys())
        writer.writerow(fieldnames)
        for row in payload["rows"]:
            writer.writerow([row[field] for field in fieldnames])
    else:
        writer.writerow(["field", "value"])
        writer.writerows(_flatten(payload))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    curve = subparsers.add_parser("curve", help="Generate a linear, geometric, power, or logistic curve")
    curve.add_argument("--kind", choices=("linear", "geometric", "power", "logistic"), required=True)
    curve.add_argument("--count", type=int, required=True)
    curve.add_argument("--start-index", type=int, default=1)
    curve.add_argument("--base", type=float)
    curve.add_argument("--increment", type=float)
    curve.add_argument("--rate", type=float)
    curve.add_argument("--scale", type=float)
    curve.add_argument("--exponent", type=float)
    curve.add_argument("--offset", type=float, default=0.0)
    curve.add_argument("--lower", type=float)
    curve.add_argument("--upper", type=float)
    curve.add_argument("--midpoint", type=float)
    curve.add_argument("--steepness", type=float)

    progression = subparsers.add_parser(
        "progression",
        help="Generate geometric upgrade costs and optional time-to-step",
    )
    progression.add_argument("--base-cost", type=float, required=True)
    progression.add_argument("--cost-growth", type=float, required=True)
    progression.add_argument("--count", type=int, required=True)
    progression.add_argument("--start-index", type=int, default=1)
    progression.add_argument("--income-per-period", type=float)
    progression.add_argument("--income-growth", type=float, default=0.0)
    progression.add_argument("--round-to", type=float, default=0.0)

    combat = subparsers.add_parser("combat", help="Calculate expected damage throughput and TTK")
    combat.add_argument("--health", type=float, required=True)
    combat.add_argument("--damage", type=float, required=True)
    combat.add_argument("--attack-rate", type=float, required=True)
    combat.add_argument("--accuracy", type=float, default=1.0)
    combat.add_argument("--crit-chance", type=float, default=0.0)
    combat.add_argument("--crit-multiplier", type=float, default=1.0)
    combat.add_argument("--flat-reduction", type=float, default=0.0)
    combat.add_argument("--damage-reduction", type=float, default=0.0)

    drop = subparsers.add_parser("drop", help="Calculate independent drop odds and hard pity")
    drop.add_argument("--chance", type=float, required=True)
    drop.add_argument("--hard-pity", type=int)
    drop.add_argument("--attempts", nargs="+", type=int, default=[1, 10, 50, 100])
    drop.add_argument("--quantiles", nargs="+", type=float, default=[0.5, 0.9, 0.95, 0.99])
    drop.add_argument("--cost-per-attempt", type=float, default=0.0)

    economy = subparsers.add_parser("economy", help="Calculate a one-currency stock-flow baseline")
    economy.add_argument("--source-per-period", type=float, required=True)
    economy.add_argument("--mandatory-sink-per-period", type=float, required=True)
    economy.add_argument("--starting-balance", type=float, required=True)
    economy.add_argument("--goal-cost", type=float, required=True)
    economy.add_argument("--horizon", type=int, required=True)

    rating = subparsers.add_parser("rating", help="Calculate Elo-style expected score and update")
    rating.add_argument("--rating-a", type=float, required=True)
    rating.add_argument("--rating-b", type=float, required=True)
    rating.add_argument("--scale", type=float, default=400.0)
    rating.add_argument("--score-a", type=float)
    rating.add_argument("--k-factor", type=float, default=32.0)

    proportion = subparsers.add_parser(
        "proportion",
        help="Calculate a Wilson interval and conservative sample size",
    )
    proportion.add_argument("--successes", type=int, required=True)
    proportion.add_argument("--trials", type=int, required=True)
    proportion.add_argument("--confidence", type=float, default=0.95)
    proportion.add_argument("--target-margin", type=float)

    return parser


def _curve_parameters(args: argparse.Namespace) -> dict[str, float]:
    required_by_kind = {
        "linear": ("base", "increment"),
        "geometric": ("base", "rate"),
        "power": ("scale", "exponent", "offset"),
        "logistic": ("lower", "upper", "midpoint", "steepness"),
    }
    names = required_by_kind[args.kind]
    missing = [name for name in names if getattr(args, name) is None]
    if missing:
        options = ", ".join(f"--{name.replace('_', '-')}" for name in missing)
        raise ValueError(f"{args.kind} curve requires {options}")
    parameters = {name: getattr(args, name) for name in names}
    for name, value in parameters.items():
        _require_finite(name, value)
    return parameters


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "curve":
            payload = calculate_curve(
                args.kind,
                args.count,
                args.start_index,
                **_curve_parameters(args),
            )
        elif args.command == "progression":
            payload = calculate_progression(
                base_cost=args.base_cost,
                cost_growth=args.cost_growth,
                count=args.count,
                start_index=args.start_index,
                income_per_period=args.income_per_period,
                income_growth=args.income_growth,
                round_to=args.round_to,
            )
        elif args.command == "combat":
            payload = calculate_combat(
                health=args.health,
                damage=args.damage,
                attack_rate=args.attack_rate,
                accuracy=args.accuracy,
                crit_chance=args.crit_chance,
                crit_multiplier=args.crit_multiplier,
                flat_reduction=args.flat_reduction,
                damage_reduction=args.damage_reduction,
            )
        elif args.command == "drop":
            payload = calculate_drop(
                chance=args.chance,
                hard_pity=args.hard_pity,
                attempts=args.attempts,
                quantiles=args.quantiles,
                cost_per_attempt=args.cost_per_attempt,
            )
        elif args.command == "economy":
            payload = calculate_economy(
                source_per_period=args.source_per_period,
                mandatory_sink_per_period=args.mandatory_sink_per_period,
                starting_balance=args.starting_balance,
                goal_cost=args.goal_cost,
                horizon=args.horizon,
            )
        elif args.command == "rating":
            payload = calculate_rating(
                rating_a=args.rating_a,
                rating_b=args.rating_b,
                scale=args.scale,
                score_a=args.score_a,
                k_factor=args.k_factor,
            )
        else:
            payload = calculate_proportion(
                successes=args.successes,
                trials=args.trials,
                confidence=args.confidence,
                target_margin=args.target_margin,
            )
    except (KeyError, OverflowError, ValueError) as exc:
        parser.error(str(exc))

    emit(payload, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
