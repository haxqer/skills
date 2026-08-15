#!/usr/bin/env python3
"""Sensitivity ranking and constrained parameter search.

Both subcommands reuse one seed stream across every candidate (common random
numbers), so the differences they report are caused by the parameter change and
not by resampling noise. The search prefers the smallest change that satisfies
the targets, which is what makes a proposal shippable.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

from sim_engine import load_scenario
from sim_report import aggregate, get_path
from sim_runner import build_scenario, read_path, run_batch

DEFAULT_EVAL_BATTLES = 2000
DEFAULT_VERIFY_BATTLES = 10000


class Objective:
    """One scored requirement on an aggregated metric."""

    __slots__ = ("metric", "target", "tolerance", "minimum", "maximum", "scale", "weight")

    def __init__(self, spec: dict[str, Any]) -> None:
        if "metric" not in spec:
            raise ValueError("every objective needs a metric path")
        self.metric = str(spec["metric"])
        self.target = spec.get("target")
        self.tolerance = float(spec.get("tolerance", 0.0))
        self.minimum = spec.get("min")
        self.maximum = spec.get("max")
        if self.target is None and self.minimum is None and self.maximum is None:
            raise ValueError(f"objective {self.metric} needs target, min, or max")
        scale = float(spec.get("scale", 0.0))
        if scale <= 0:
            scale = max(self.tolerance, abs(float(self.target)) * 0.05) if self.target else 1.0
            scale = scale or 1.0
        self.scale = scale
        self.weight = float(spec.get("weight", 1.0))

    def violation(self, value: float) -> float:
        """Distance outside the acceptable band, in `scale` units. 0 means satisfied."""
        gap = 0.0
        if self.target is not None:
            gap = max(gap, abs(value - float(self.target)) - self.tolerance)
        if self.minimum is not None:
            gap = max(gap, float(self.minimum) - value)
        if self.maximum is not None:
            gap = max(gap, value - float(self.maximum))
        return max(0.0, gap) / self.scale

    def describe(self, value: float) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "value": value,
            "target": self.target,
            "tolerance": self.tolerance,
            "min": self.minimum,
            "max": self.maximum,
            "violation": self.violation(value),
            "satisfied": self.violation(value) <= 1e-12,
        }


class Tunable:
    """One searchable parameter with a legal range and grid."""

    __slots__ = ("path", "minimum", "maximum", "step", "baseline")

    def __init__(self, spec: dict[str, Any], baseline: float) -> None:
        self.path = str(spec["path"])
        self.baseline = float(baseline)
        self.minimum = float(spec.get("min", self.baseline * 0.5))
        self.maximum = float(spec.get("max", self.baseline * 1.5))
        if self.minimum > self.maximum:
            raise ValueError(f"{self.path}: min must not exceed max")
        step = float(spec.get("step", 0.0))
        if step <= 0:
            step = max((self.maximum - self.minimum) / 40.0, 1e-9)
        self.step = step

    def snap(self, value: float) -> float:
        clamped = min(self.maximum, max(self.minimum, value))
        steps = round((clamped - self.minimum) / self.step)
        snapped = self.minimum + steps * self.step
        snapped = min(self.maximum, max(self.minimum, snapped))
        return round(snapped, 9)

    @property
    def span(self) -> float:
        return max(self.maximum - self.minimum, 1e-9)


class Evaluator:
    """Runs the scenario under a candidate parameter vector and scores it."""

    def __init__(
        self,
        base_scenario: dict[str, Any],
        tunables: list[Tunable],
        objectives: list[Objective],
        focus_team: str | None,
        battles: int,
        seed_base: int,
        workers: int,
        change_penalty: float,
    ) -> None:
        self.base_scenario = base_scenario
        self.tunables = tunables
        self.objectives = objectives
        self.focus_team = focus_team
        self.battles = battles
        self.seed_base = seed_base
        self.workers = workers
        self.change_penalty = change_penalty
        self.cache: dict[tuple[float, ...], dict[str, Any]] = {}
        self.evaluations = 0

    def report_for(self, values: tuple[float, ...], battles: int | None = None) -> dict[str, Any]:
        overrides = [
            f"{tunable.path}={json.dumps(value)}"
            for tunable, value in zip(self.tunables, values)
        ]
        scenario = build_scenario(self.base_scenario, overrides)
        records = run_batch(
            scenario, battles or self.battles, seed_base=self.seed_base, workers=self.workers
        )
        return aggregate(records, self.focus_team)

    def score(self, values: tuple[float, ...]) -> dict[str, Any]:
        if values in self.cache:
            return self.cache[values]
        report = self.report_for(values)
        self.evaluations += 1
        result = self.assess(values, report)
        self.cache[values] = result
        return result

    def assess(self, values: tuple[float, ...], report: dict[str, Any]) -> dict[str, Any]:
        details = []
        violation = 0.0
        for objective in self.objectives:
            value = float(get_path(report, objective.metric))
            details.append(objective.describe(value))
            violation += objective.weight * objective.violation(value)
        change = sum(
            abs(value - tunable.baseline) / tunable.span
            for tunable, value in zip(self.tunables, values)
        ) / max(1, len(self.tunables))
        return {
            "values": list(values),
            "violation": violation,
            "change_cost": change,
            "objective": violation + self.change_penalty * change,
            "satisfied": all(item["satisfied"] for item in details),
            "metrics": details,
        }


PROBE_MULTIPLES = (8.0, 4.0, 2.0, 1.0)


def coordinate_descent(
    evaluator: Evaluator,
    max_passes: int = 12,
    shrink_floor: float = 0.125,
    probes: tuple[float, ...] = PROBE_MULTIPLES,
    start: tuple[float, ...] | None = None,
) -> dict[str, Any]:
    """Walk one axis at a time, shrinking the step when a full pass finds nothing.

    Each axis is probed at several step multiples. A single-step probe stalls on
    the flat spots that sampling noise creates in a simulated response surface;
    the longer probes step over them.
    """
    current = start or tuple(tunable.snap(tunable.baseline) for tunable in evaluator.tunables)
    best = evaluator.score(current)
    trace = [{"pass": 0, "values": list(current), "objective": best["objective"]}]
    multiplier = 1.0
    for pass_index in range(1, max_passes + 1):
        improved = False
        anchor = current
        for axis, tunable in enumerate(evaluator.tunables):
            for probe in probes:
                step = tunable.step * multiplier * probe
                for direction in (1, -1):
                    candidate_value = tunable.snap(current[axis] + direction * step)
                    if candidate_value == current[axis]:
                        continue
                    candidate = list(current)
                    candidate[axis] = candidate_value
                    scored = evaluator.score(tuple(candidate))
                    if scored["objective"] < best["objective"] - 1e-9:
                        best = scored
                        current = tuple(candidate)
                        improved = True
        if improved and len(evaluator.tunables) > 1:
            # Hooke-Jeeves pattern move: extrapolate along the whole pass to follow a
            # diagonal valley that single-axis steps can only crawl down.
            extrapolated = tuple(
                tunable.snap(value + (value - start))
                for tunable, value, start in zip(evaluator.tunables, current, anchor)
            )
            if extrapolated != current:
                scored = evaluator.score(extrapolated)
                if scored["objective"] < best["objective"] - 1e-9:
                    best = scored
                    current = extrapolated
        trace.append(
            {
                "pass": pass_index,
                "values": list(current),
                "objective": best["objective"],
                "violation": best["violation"],
                "step_multiplier": multiplier,
            }
        )
        if not improved:
            if multiplier <= shrink_floor:
                break
            multiplier /= 2.0
    return {"best": best, "trace": trace}


HALTON_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def _halton(index: int, base: int) -> float:
    """Deterministic low-discrepancy sequence. No RNG, so restarts are reproducible."""
    result = 0.0
    fraction = 1.0
    remaining = index
    while remaining > 0:
        fraction /= base
        result += fraction * (remaining % base)
        remaining //= base
    return result


def start_points(tunables: list[Tunable], restarts: int) -> list[tuple[float, ...]]:
    """Baseline first, then spread-out starts so one local basin cannot own the answer."""
    points = [tuple(tunable.snap(tunable.baseline) for tunable in tunables)]
    for index in range(1, max(1, restarts)):
        candidate = tuple(
            tunable.snap(
                tunable.minimum
                + _halton(index, HALTON_BASES[axis % len(HALTON_BASES)])
                * (tunable.maximum - tunable.minimum)
            )
            for axis, tunable in enumerate(tunables)
        )
        if candidate not in points:
            points.append(candidate)
    return points


def multi_start_search(
    evaluator: Evaluator, max_passes: int = 12, restarts: int = 4
) -> dict[str, Any]:
    """Descend from several starts and keep the best result.

    A single greedy descent on a noisy, multi-objective surface reliably finds a
    local basin and stops. Reporting that basin as "the answer" is how a tuning
    pass quietly ships a worse config than one that existed nearby.
    """
    runs = []
    for index, point in enumerate(start_points(evaluator.tunables, restarts)):
        outcome = coordinate_descent(evaluator, max_passes, start=point)
        runs.append({"start": list(point), "restart": index, **outcome})
    winner = min(runs, key=lambda run: run["best"]["objective"])
    return {
        "best": winner["best"],
        "trace": winner["trace"],
        "winning_restart": winner["restart"],
        "restarts": [
            {
                "restart": run["restart"],
                "start": run["start"],
                "objective": run["best"]["objective"],
                "values": run["best"]["values"],
                "satisfied": run["best"]["satisfied"],
            }
            for run in runs
        ],
    }


def sensitivity(evaluator: Evaluator, metrics: list[str], delta_steps: float = 2.0) -> list[dict]:
    """Rank tunables by how far a fixed nudge moves each tracked metric."""
    baseline_values = tuple(tunable.snap(tunable.baseline) for tunable in evaluator.tunables)
    baseline_report = evaluator.report_for(baseline_values)
    rows = []
    for axis, tunable in enumerate(evaluator.tunables):
        entry: dict[str, Any] = {"path": tunable.path, "baseline": baseline_values[axis]}
        for direction, label in ((1, "up"), (-1, "down")):
            candidate = list(baseline_values)
            candidate[axis] = tunable.snap(
                baseline_values[axis] + direction * tunable.step * delta_steps
            )
            entry[f"{label}_value"] = candidate[axis]
            if candidate[axis] == baseline_values[axis]:
                entry[f"{label}_deltas"] = {metric: 0.0 for metric in metrics}
                continue
            report = evaluator.report_for(tuple(candidate))
            entry[f"{label}_deltas"] = {
                metric: float(get_path(report, metric)) - float(get_path(baseline_report, metric))
                for metric in metrics
            }
        primary = metrics[0]
        entry["abs_effect"] = max(
            abs(entry["up_deltas"][primary]), abs(entry["down_deltas"][primary])
        )
        span = abs(entry["up_value"] - entry["down_value"]) or 1.0
        entry["elasticity"] = (
            (entry["up_deltas"][primary] - entry["down_deltas"][primary]) / span
        )
        rows.append(entry)
    rows.sort(key=lambda row: -row["abs_effect"])
    return rows


def load_plan(path: str, scenario: dict[str, Any]) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        plan = json.load(handle)
    if not isinstance(plan, dict):
        raise ValueError("plan file must contain a JSON object")
    tunable_specs = plan.get("tunables") or []
    if not tunable_specs:
        raise ValueError("plan needs at least one tunable")
    tunables = []
    for spec in tunable_specs:
        current = read_path(scenario, spec["path"])
        if not isinstance(current, (int, float)) or isinstance(current, bool):
            raise ValueError(f"tunable {spec['path']} does not point at a number")
        tunables.append(Tunable(spec, float(current)))
    objectives = [Objective(spec) for spec in plan.get("objectives") or []]
    plan["_tunables"] = tunables
    plan["_objectives"] = objectives
    return plan


def _build_evaluator(args: argparse.Namespace, battles_key: str) -> tuple[Evaluator, dict[str, Any]]:
    scenario = load_scenario(args.scenario)
    plan = load_plan(args.plan, scenario)
    workers = max(1, min(args.workers, os.cpu_count() or 1))
    evaluator = Evaluator(
        scenario,
        plan["_tunables"],
        plan["_objectives"],
        plan.get("focus_team"),
        int(plan.get(battles_key, DEFAULT_EVAL_BATTLES)),
        int(plan.get("seed_base", 0)),
        workers,
        float(plan.get("change_penalty", 0.25)),
    )
    return evaluator, plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank parameter sensitivity and search for fixes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("sensitivity", "rank tunables by their effect on tracked metrics"),
        ("search", "find the smallest change that satisfies the objectives"),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("scenario", help="path to a scenario JSON file")
        sub.add_argument("plan", help="path to a tuning plan JSON file")
        sub.add_argument("--workers", type=int, default=1)
        sub.add_argument("--out", default=None, help="write the JSON result here")

    subparsers.choices["sensitivity"].add_argument(
        "--metric", action="append", default=[], help="metric path (repeatable)"
    )
    subparsers.choices["search"].add_argument("--max-passes", type=int, default=12)
    subparsers.choices["search"].add_argument(
        "--restarts", type=int, default=4, help="max descent starts, baseline first; duplicates are dropped (default: 4)"
    )
    subparsers.choices["search"].add_argument(
        "--skip-verify", action="store_true", help="skip the high-sample confirmation run"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "sensitivity":
            evaluator, plan = _build_evaluator(args, "eval_battles")
            metrics = args.metric or [
                objective.metric for objective in plan["_objectives"]
            ] or ["win_rate.point"]
            result = {
                "battles_per_evaluation": evaluator.battles,
                "seed_base": evaluator.seed_base,
                "primary_metric": metrics[0],
                "rows": sensitivity(evaluator, metrics),
            }
        else:
            evaluator, plan = _build_evaluator(args, "eval_battles")
            outcome = multi_start_search(evaluator, args.max_passes, args.restarts)
            best = outcome["best"]
            proposal = [
                {
                    "path": tunable.path,
                    "baseline": tunable.baseline,
                    "proposed": value,
                    "delta": value - tunable.baseline,
                    "delta_pct": (
                        (value - tunable.baseline) / tunable.baseline
                        if tunable.baseline
                        else math.inf
                    ),
                }
                for tunable, value in zip(evaluator.tunables, best["values"])
            ]
            result = {
                "battles_per_evaluation": evaluator.battles,
                "evaluations": evaluator.evaluations,
                "seed_base": evaluator.seed_base,
                "proposal": proposal,
                "objective": best["objective"],
                "violation": best["violation"],
                "change_cost": best["change_cost"],
                "satisfied": best["satisfied"],
                "metrics": best["metrics"],
                "winning_restart": outcome["winning_restart"],
                "restarts": outcome["restarts"],
                "trace": outcome["trace"],
            }
            if not args.skip_verify:
                verify_battles = int(plan.get("verify_battles", DEFAULT_VERIFY_BATTLES))
                verify_seed = int(plan.get("verify_seed_base", evaluator.seed_base + 1_000_000))
                evaluator.seed_base = verify_seed
                report = evaluator.report_for(tuple(best["values"]), battles=verify_battles)
                verified = evaluator.assess(tuple(best["values"]), report)
                result["verification"] = {
                    "battles": verify_battles,
                    "seed_base": verify_seed,
                    "held_on_fresh_seeds": verified["satisfied"],
                    "metrics": verified["metrics"],
                    "win_rate": report["win_rate"],
                }
        text = json.dumps(result, indent=2, sort_keys=True)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
        else:
            print(text)
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
