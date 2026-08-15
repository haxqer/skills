#!/usr/bin/env python3
"""Batch runner: seeds, parallelism, sequential convergence, scenario overrides.

Seeds are derived from `--seed-base` so two variants run over the identical
random stream (common random numbers). Results are always sorted by seed, so
the output is byte-identical regardless of worker scheduling.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from typing import Any

from sim_engine import load_scenario, simulate
from sim_report import DEFAULT_CONFIDENCE, aggregate, render_markdown, wilson_interval

DEFAULT_BATTLES = 10000
DEFAULT_MAX_BATTLES = 200000
CHUNK = 1000

_WORKER_SCENARIO: dict[str, Any] | None = None


def _init_worker(scenario: dict[str, Any]) -> None:
    global _WORKER_SCENARIO
    _WORKER_SCENARIO = scenario


def _run_seed(seed: int) -> dict[str, Any]:
    assert _WORKER_SCENARIO is not None
    return simulate(_WORKER_SCENARIO, seed)


def parse_override(text: str) -> tuple[str, Any]:
    """Parse `path=value`. The value is JSON, falling back to a bare string."""
    if "=" not in text:
        raise ValueError(f"override must look like path=value, got {text!r}")
    path, _, raw = text.partition("=")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    return path.strip(), value


def apply_override(scenario: dict[str, Any], path: str, value: Any) -> None:
    """Set a dotted path in place. Integer segments index into lists.

    Example: `teams.A.0.atk=115` or `teams.B.0.skills.1.power=1.4`.
    """
    segments = path.split(".")
    current: Any = scenario
    for segment in segments[:-1]:
        current = _descend(current, segment, path)
    last = segments[-1]
    if isinstance(current, list):
        index = _as_index(last, path)
        if not 0 <= index < len(current):
            raise KeyError(f"index out of range in override path {path!r}")
        current[index] = value
    elif isinstance(current, dict):
        if last not in current:
            raise KeyError(f"unknown key {last!r} in override path {path!r}")
        current[last] = value
    else:
        raise KeyError(f"cannot set {last!r} on a scalar in override path {path!r}")


def read_path(scenario: dict[str, Any], path: str) -> Any:
    current: Any = scenario
    for segment in path.split("."):
        current = _descend(current, segment, path)
    return current


def _as_index(segment: str, path: str) -> int:
    try:
        return int(segment)
    except ValueError as error:
        raise KeyError(f"expected a list index in override path {path!r}, got {segment!r}") from error


def _descend(current: Any, segment: str, path: str) -> Any:
    if isinstance(current, list):
        index = _as_index(segment, path)
        if not 0 <= index < len(current):
            raise KeyError(f"index out of range in override path {path!r}")
        return current[index]
    if isinstance(current, dict):
        if segment not in current:
            raise KeyError(f"unknown key {segment!r} in override path {path!r}")
        return current[segment]
    raise KeyError(f"cannot descend into a scalar at {segment!r} in override path {path!r}")


def build_scenario(
    base: dict[str, Any],
    overrides: list[str] | None = None,
    scales: list[str] | None = None,
) -> dict[str, Any]:
    """Return a copy of the scenario with absolute and relative edits applied."""
    scenario = deepcopy(base)
    for item in overrides or []:
        path, value = parse_override(item)
        apply_override(scenario, path, value)
    for item in scales or []:
        path, factor = parse_override(item)
        current = read_path(scenario, path)
        if not isinstance(current, (int, float)) or isinstance(current, bool):
            raise ValueError(f"cannot scale non-numeric value at {path!r}")
        apply_override(scenario, path, current * float(factor))
    return scenario


def run_batch(
    scenario: dict[str, Any],
    battles: int,
    seed_base: int = 0,
    workers: int = 1,
) -> list[dict[str, Any]]:
    """Run `battles` seeded battles and return records sorted by seed."""
    if battles < 1:
        raise ValueError("battles must be at least 1")
    seeds = [seed_base + index for index in range(battles)]
    if workers <= 1:
        return [simulate(scenario, seed) for seed in seeds]
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init_worker, initargs=(scenario,)
    ) as pool:
        records = list(pool.map(_run_seed, seeds, chunksize=max(1, len(seeds) // (workers * 4))))
    records.sort(key=lambda record: record["seed"])
    return records


def run_until_converged(
    scenario: dict[str, Any],
    focus_team: str | None,
    target_half_width: float,
    min_battles: int,
    max_battles: int,
    seed_base: int = 0,
    workers: int = 1,
    confidence: float = DEFAULT_CONFIDENCE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Add samples until the win-rate interval is tight enough or the cap is hit.

    Returns the records plus a run summary. `converged` is False when the cap was
    reached first; report that state instead of quoting the point estimate alone.
    """
    if max_battles < min_battles:
        raise ValueError("max_battles must be at least min_battles")
    records: list[dict[str, Any]] = []
    while len(records) < max_battles:
        remaining = max_battles - len(records)
        step = min(remaining, max(CHUNK, min_battles - len(records)))
        records.extend(
            run_batch(scenario, step, seed_base=seed_base + len(records), workers=workers)
        )
        if len(records) < min_battles:
            continue
        team = focus_team or sorted({u["team"] for u in records[0]["units"].values()})[0]
        wins = sum(1 for record in records if record["winner"] == team)
        interval = wilson_interval(wins, len(records), confidence)
        if interval["half_width"] <= target_half_width:
            return records, {
                "converged": True,
                "battles": len(records),
                "win_rate_half_width": interval["half_width"],
                "target_half_width": target_half_width,
                "seed_base": seed_base,
            }
    team = focus_team or sorted({u["team"] for u in records[0]["units"].values()})[0]
    wins = sum(1 for record in records if record["winner"] == team)
    interval = wilson_interval(wins, len(records), confidence)
    return records, {
        "converged": interval["half_width"] <= target_half_width,
        "battles": len(records),
        "win_rate_half_width": interval["half_width"],
        "target_half_width": target_half_width,
        "seed_base": seed_base,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a scenario many times and emit records plus an aggregated report."
    )
    parser.add_argument("scenario", help="path to a scenario JSON file")
    parser.add_argument(
        "--battles", type=int, default=DEFAULT_BATTLES, help=f"default: {DEFAULT_BATTLES}"
    )
    parser.add_argument("--seed-base", type=int, default=0, help="first seed (default: 0)")
    parser.add_argument("--team", default=None, help="focus team (default: first team)")
    parser.add_argument(
        "--target-half-width",
        type=float,
        default=None,
        help="enable sequential sampling until the win-rate CI half-width is this small",
    )
    parser.add_argument("--min-battles", type=int, default=DEFAULT_BATTLES)
    parser.add_argument("--max-battles", type=int, default=DEFAULT_MAX_BATTLES)
    parser.add_argument("--confidence", type=float, default=DEFAULT_CONFIDENCE)
    parser.add_argument(
        "--workers", type=int, default=1, help="worker processes (default: 1, deterministic)"
    )
    parser.add_argument("--set", action="append", default=[], metavar="PATH=VALUE")
    parser.add_argument("--scale", action="append", default=[], metavar="PATH=FACTOR")
    parser.add_argument("--records-out", default=None, help="write raw records JSON here")
    parser.add_argument("--report-out", default=None, help="write the aggregated report JSON here")
    parser.add_argument("--format", choices=("json", "markdown", "none"), default="markdown")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        base = load_scenario(args.scenario)
        scenario = build_scenario(base, args.set, args.scale)
        workers = max(1, min(args.workers, os.cpu_count() or 1))
        if args.target_half_width is not None:
            records, run = run_until_converged(
                scenario,
                args.team,
                args.target_half_width,
                args.min_battles,
                args.max_battles,
                seed_base=args.seed_base,
                workers=workers,
                confidence=args.confidence,
            )
        else:
            records = run_batch(scenario, args.battles, args.seed_base, workers)
            run = {"converged": None, "battles": len(records), "seed_base": args.seed_base}
        run["scenario"] = args.scenario
        run["overrides"] = list(args.set)
        run["scales"] = list(args.scale)
        report = aggregate(records, args.team, args.confidence)
        report["converged"] = run["converged"]
        report["run"] = run
        if args.records_out:
            with open(args.records_out, "w", encoding="utf-8") as handle:
                json.dump({"run": run, "records": records}, handle, sort_keys=True)
        if args.report_out:
            with open(args.report_out, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, sort_keys=True)
        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True))
        elif args.format == "markdown":
            print(render_markdown(report))
            if run["converged"] is False:
                print(
                    f"\n**NOT CONVERGED**: win-rate half-width "
                    f"{run['win_rate_half_width']:.4f} > target "
                    f"{run['target_half_width']:.4f} after {run['battles']} battles. "
                    "Raise --max-battles or loosen the target before quoting this number."
                )
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
