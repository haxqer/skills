#!/usr/bin/env python3
"""Statistics and metric aggregation for batches of battle records.

This module never imports the engine. It turns a list of battle records into a
report whose every leaf is addressable by a dotted path, so the same numbers
drive convergence checks, tuning objectives, and regression diffs.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections.abc import Iterable, Sequence
from typing import Any

DEFAULT_CONFIDENCE = 0.95
BLOWOUT_THRESHOLD = 0.70
CLOSE_THRESHOLD = 0.20


def _z_score(confidence: float) -> float:
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    return statistics.NormalDist().inv_cdf(0.5 + confidence / 2.0)


def wilson_interval(
    successes: int, trials: int, confidence: float = DEFAULT_CONFIDENCE
) -> dict[str, float]:
    """Wilson score interval. Correct near 0 and 1 where the normal approximation is not."""
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("successes must be within [0, trials]")
    if trials == 0:
        return {"point": 0.0, "low": 0.0, "high": 1.0, "half_width": 0.5, "samples": 0}
    z = _z_score(confidence)
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2 * trials)) / denominator
    spread = (
        z
        / denominator
        * math.sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials))
    )
    low = max(0.0, center - spread)
    high = min(1.0, center + spread)
    return {
        "point": proportion,
        "low": low,
        "high": high,
        "half_width": (high - low) / 2.0,
        "samples": trials,
    }


def quantile(values: Sequence[float], probability: float) -> float:
    """Linear-interpolation quantile on already-collected samples."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[int(position)])
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def describe(values: Sequence[float], confidence: float = DEFAULT_CONFIDENCE) -> dict[str, float]:
    """Mean, dispersion, tails, and a mean confidence interval for a continuous metric."""
    if not values:
        return {
            "mean": 0.0,
            "sd": 0.0,
            "cv": 0.0,
            "p10": 0.0,
            "p50": 0.0,
            "p90": 0.0,
            "min": 0.0,
            "max": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "half_width": 0.0,
            "samples": 0,
        }
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    half_width = _z_score(confidence) * sd / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {
        "mean": mean,
        "sd": sd,
        "cv": sd / mean if mean else 0.0,
        "p10": quantile(values, 0.10),
        "p50": quantile(values, 0.50),
        "p90": quantile(values, 0.90),
        "min": float(min(values)),
        "max": float(max(values)),
        "ci_low": mean - half_width,
        "ci_high": mean + half_width,
        "half_width": half_width,
        "samples": len(values),
    }


def gini(values: Iterable[float]) -> float:
    """Concentration of a share vector. 0 means perfectly even, 1 means one contributor."""
    items = sorted(max(0.0, float(value)) for value in values)
    total = sum(items)
    if not items or total <= 0:
        return 0.0
    count = len(items)
    weighted = sum((index + 1) * value for index, value in enumerate(items))
    return (2 * weighted) / (count * total) - (count + 1) / count


def binary_entropy(probability: float) -> float:
    """Outcome uncertainty of a two-sided result, in bits. 1.0 at a coin flip."""
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -(
        probability * math.log2(probability) + (1 - probability) * math.log2(1 - probability)
    )


def effective_count(shares: Iterable[float]) -> float:
    """Perplexity of a share vector: how many contributors actually carry the outcome."""
    values = [max(0.0, float(share)) for share in shares]
    total = sum(values)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in values:
        proportion = value / total
        if proportion > 0:
            entropy -= proportion * math.log(proportion)
    return math.exp(entropy)


def _shares(amounts: dict[str, float]) -> dict[str, float]:
    total = sum(amounts.values())
    if total <= 0:
        return {key: 0.0 for key in amounts}
    return {key: value / total for key, value in amounts.items()}


def aggregate(
    records: Sequence[dict[str, Any]],
    focus_team: str | None = None,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, Any]:
    """Turn raw battle records into the full metric report."""
    if not records:
        raise ValueError("no records to aggregate")
    teams = sorted({unit["team"] for unit in records[0]["units"].values()})
    if focus_team is None:
        focus_team = teams[0]
    if focus_team not in teams:
        raise ValueError(f"focus_team {focus_team!r} is not one of {teams}")
    other_team = next(team for team in teams if team != focus_team)
    count = len(records)

    wins = sum(1 for record in records if record["winner"] == focus_team)
    losses = sum(1 for record in records if record["winner"] == other_team)
    draws = sum(1 for record in records if record["winner"] == "draw")
    timeouts = sum(1 for record in records if record["timeout"])

    decisive = [record for record in records if record["winner"] != "draw"]
    blowouts = sum(
        1 for record in decisive if record["winner_hp_fraction"] >= BLOWOUT_THRESHOLD
    )
    close = sum(1 for record in decisive if record["winner_hp_fraction"] <= CLOSE_THRESHOLD)
    comebacks = sum(1 for record in decisive if record.get("winner_was_behind"))

    first_blood_focus = [
        record for record in records if record.get("first_death_team") == other_team
    ]
    first_blood_against = [
        record for record in records if record.get("first_death_team") == focus_team
    ]

    unit_damage: dict[str, list[float]] = {}
    unit_share: dict[str, list[float]] = {}
    unit_taken_share: dict[str, list[float]] = {}
    unit_healing: dict[str, list[float]] = {}
    unit_healing_share: dict[str, list[float]] = {}
    unit_meta: dict[str, dict[str, Any]] = {}
    unit_survival: dict[str, list[float]] = {}
    unit_actions: dict[str, list[float]] = {}
    unit_hits: dict[str, list[float]] = {}
    unit_misses: dict[str, list[float]] = {}
    unit_crits: dict[str, list[float]] = {}
    unit_overkill: dict[str, list[float]] = {}
    unit_death_round: dict[str, list[float]] = {}

    for record in records:
        per_team_damage: dict[str, dict[str, float]] = {team: {} for team in teams}
        per_team_taken: dict[str, dict[str, float]] = {team: {} for team in teams}
        per_team_healing: dict[str, dict[str, float]] = {team: {} for team in teams}
        for uid, unit in record["units"].items():
            team = unit["team"]
            per_team_damage[team][uid] = float(unit["damage_dealt"])
            per_team_taken[team][uid] = float(unit["damage_taken"])
            per_team_healing[team][uid] = float(unit["healing_done"])
            unit_meta.setdefault(uid, {"team": team, "unit_id": unit["unit_id"], "role": unit["role"]})
            unit_damage.setdefault(uid, []).append(float(unit["damage_dealt"]))
            unit_healing.setdefault(uid, []).append(float(unit["healing_done"]))
            unit_survival.setdefault(uid, []).append(1.0 if unit["survived"] else 0.0)
            unit_actions.setdefault(uid, []).append(float(unit["actions"]))
            unit_hits.setdefault(uid, []).append(float(unit["hits"]))
            unit_misses.setdefault(uid, []).append(float(unit["misses"]))
            unit_crits.setdefault(uid, []).append(float(unit["crits"]))
            unit_overkill.setdefault(uid, []).append(float(unit["overkill"]))
            if unit["death_round"] is not None:
                unit_death_round.setdefault(uid, []).append(float(unit["death_round"]))
        for team in teams:
            for uid, share in _shares(per_team_damage[team]).items():
                unit_share.setdefault(uid, []).append(share)
            for uid, share in _shares(per_team_taken[team]).items():
                unit_taken_share.setdefault(uid, []).append(share)
            for uid, share in _shares(per_team_healing[team]).items():
                unit_healing_share.setdefault(uid, []).append(share)

    durations = [float(record["duration"]) for record in records]
    mean_duration = statistics.fmean(durations) if durations else 0.0

    units: dict[str, Any] = {}
    for uid, meta in sorted(unit_meta.items()):
        share_samples = unit_share.get(uid, [])
        share_stats = describe(share_samples, confidence)
        damage_stats = describe(unit_damage.get(uid, []), confidence)
        attempts = sum(unit_hits.get(uid, [])) + sum(unit_misses.get(uid, []))
        deaths = len(unit_death_round.get(uid, []))
        units[uid] = {
            "team": meta["team"],
            "unit_id": meta["unit_id"],
            "role": meta["role"],
            "damage_share": {
                "mean": share_stats["mean"],
                "low": share_stats["ci_low"],
                "high": share_stats["ci_high"],
                "p10": share_stats["p10"],
                "p90": share_stats["p90"],
            },
            "damage_taken_share": statistics.fmean(unit_taken_share.get(uid, [0.0])),
            "healing_share": statistics.fmean(unit_healing_share.get(uid, [0.0])),
            "damage_per_battle": damage_stats["mean"],
            "dps": damage_stats["mean"] / mean_duration if mean_duration else 0.0,
            "overkill_ratio": (
                statistics.fmean(unit_overkill.get(uid, [0.0]))
                / damage_stats["mean"]
                if damage_stats["mean"]
                else 0.0
            ),
            "healing_per_battle": statistics.fmean(unit_healing.get(uid, [0.0])),
            "survival_rate": statistics.fmean(unit_survival.get(uid, [0.0])),
            "actions_per_battle": statistics.fmean(unit_actions.get(uid, [0.0])),
            "hit_rate": sum(unit_hits.get(uid, [])) / attempts if attempts else 0.0,
            "crit_rate": (
                sum(unit_crits.get(uid, [])) / sum(unit_hits.get(uid, []))
                if sum(unit_hits.get(uid, []))
                else 0.0
            ),
            "death_rate": deaths / count,
            "mean_death_round": (
                statistics.fmean(unit_death_round[uid]) if uid in unit_death_round else None
            ),
        }

    focus_units = {uid: entry for uid, entry in units.items() if entry["team"] == focus_team}
    focus_shares = [entry["damage_share"]["mean"] for uid, entry in sorted(focus_units.items())]
    ordered_shares = sorted(focus_shares, reverse=True)
    win_rate = wilson_interval(wins, count, confidence)

    report: dict[str, Any] = {
        "focus_team": focus_team,
        "opponent_team": other_team,
        "samples": count,
        "converged": None,
        "win_rate": win_rate,
        "loss_rate": wilson_interval(losses, count, confidence),
        "draw_rate": draws / count,
        "timeout_rate": timeouts / count,
        "outcome_entropy": binary_entropy(win_rate["point"]),
        "rounds": describe([float(record["rounds"]) for record in records], confidence),
        "duration": describe(durations, confidence),
        "margin": describe([float(record["margin"]) for record in records], confidence),
        "lead_flips": describe([float(record["lead_flips"]) for record in records], confidence),
        "blowout_rate": blowouts / len(decisive) if decisive else 0.0,
        "close_rate": close / len(decisive) if decisive else 0.0,
        "comeback_rate": comebacks / len(decisive) if decisive else 0.0,
        "first_blood": {
            "focus_team_rate": len(first_blood_focus) / count,
            "win_rate_with_first_blood": (
                sum(1 for record in first_blood_focus if record["winner"] == focus_team)
                / len(first_blood_focus)
                if first_blood_focus
                else 0.0
            ),
            "win_rate_without_first_blood": (
                sum(1 for record in first_blood_against if record["winner"] == focus_team)
                / len(first_blood_against)
                if first_blood_against
                else 0.0
            ),
        },
        "concentration": {
            "gini": gini(focus_shares),
            "top1_share": ordered_shares[0] if ordered_shares else 0.0,
            "top3_share": sum(ordered_shares[:3]),
            "effective_contributors": effective_count(focus_shares),
            "roster_size": len(focus_shares),
        },
        "max_damage_share": max(focus_shares) if focus_shares else 0.0,
        "min_damage_share": min(focus_shares) if focus_shares else 0.0,
        "dead_weight": [
            uid
            for uid, entry in sorted(focus_units.items())
            if entry["damage_share"]["mean"] < 0.5 / max(1, len(focus_shares))
            and entry["healing_share"] < 0.10
        ],
        "units": units,
    }
    return report


def paired_compare(
    baseline: Sequence[dict[str, Any]],
    candidate: Sequence[dict[str, Any]],
    focus_team: str,
    confidence: float = DEFAULT_CONFIDENCE,
) -> dict[str, Any]:
    """Compare two variants on the seeds they share (common random numbers).

    Pairing removes the shared RNG noise, so a small real effect becomes visible
    at a sample size where the unpaired intervals would still overlap.
    """
    left = {record["seed"]: record for record in baseline}
    right = {record["seed"]: record for record in candidate}
    seeds = sorted(set(left) & set(right))
    if not seeds:
        raise ValueError("no shared seeds: rerun both variants with the same --seed-base")
    win_deltas = [
        (1.0 if right[seed]["winner"] == focus_team else 0.0)
        - (1.0 if left[seed]["winner"] == focus_team else 0.0)
        for seed in seeds
    ]
    round_deltas = [float(right[seed]["rounds"] - left[seed]["rounds"]) for seed in seeds]
    flipped_to_win = sum(1 for delta in win_deltas if delta > 0)
    flipped_to_loss = sum(1 for delta in win_deltas if delta < 0)
    return {
        "paired_seeds": len(seeds),
        "unpaired_baseline": len(left) - len(seeds),
        "unpaired_candidate": len(right) - len(seeds),
        "win_rate_delta": describe(win_deltas, confidence),
        "rounds_delta": describe(round_deltas, confidence),
        "outcome_flips": {"to_win": flipped_to_win, "to_loss": flipped_to_loss},
        "significant": _excludes_zero(describe(win_deltas, confidence)),
    }


def _excludes_zero(stats: dict[str, float]) -> bool:
    return stats["ci_low"] > 0.0 or stats["ci_high"] < 0.0


def bootstrap_interval(
    values: Sequence[float],
    resamples: int = 2000,
    confidence: float = DEFAULT_CONFIDENCE,
    seed: int = 0,
) -> dict[str, float]:
    """Deterministic percentile bootstrap for metrics whose mean interval is untrustworthy."""
    if not values:
        return {"point": 0.0, "low": 0.0, "high": 0.0}
    rng = random.Random(seed)
    count = len(values)
    means = []
    for _ in range(resamples):
        means.append(statistics.fmean(values[rng.randrange(count)] for _ in range(count)))
    tail = (1.0 - confidence) / 2.0
    return {
        "point": statistics.fmean(values),
        "low": quantile(means, tail),
        "high": quantile(means, 1.0 - tail),
    }


def get_path(report: dict[str, Any], path: str) -> Any:
    """Read a dotted path such as `win_rate.point` or `units.A/knight.damage_share.mean`."""
    current: Any = report
    remaining = path
    while remaining:
        if isinstance(current, dict):
            match = None
            for key in current:
                if remaining == key:
                    match = key
                    break
                if remaining.startswith(f"{key}."):
                    if match is None or len(key) > len(match):
                        match = key
            if match is None:
                raise KeyError(f"metric path not found: {path}")
            current = current[match]
            remaining = remaining[len(match) :].lstrip(".")
            continue
        if isinstance(current, list):
            head, _, remaining = remaining.partition(".")
            current = current[int(head)]
            continue
        raise KeyError(f"metric path not found: {path}")
    return current


def render_markdown(report: dict[str, Any]) -> str:
    """Human-readable summary. Always states sample size and convergence."""
    win = report["win_rate"]
    rounds = report["rounds"]
    duration = report["duration"]
    status = {True: "converged", False: "NOT CONVERGED", None: "convergence not checked"}[
        report.get("converged")
    ]
    lines = [
        f"# Simulation report - team {report['focus_team']} vs {report['opponent_team']}",
        "",
        f"Samples: {report['samples']} battles ({status})",
        "",
        "## Outcome",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Win rate | {win['point']:.4f} (95% CI {win['low']:.4f}-{win['high']:.4f}, "
        f"+/-{win['half_width']:.4f}) |",
        f"| Draw rate | {report['draw_rate']:.4f} |",
        f"| Timeout rate | {report['timeout_rate']:.4f} |",
        f"| Outcome entropy | {report['outcome_entropy']:.3f} bits |",
        f"| Blowout rate | {report['blowout_rate']:.4f} |",
        f"| Close rate | {report['close_rate']:.4f} |",
        f"| Comeback rate | {report['comeback_rate']:.4f} |",
        f"| First blood -> win | {report['first_blood']['win_rate_with_first_blood']:.4f} |",
        "",
        "## Battle length",
        "",
        "| Metric | Mean | CV | p10 | p50 | p90 | Max |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| Rounds | {rounds['mean']:.2f} | {rounds['cv']:.3f} | {rounds['p10']:.1f} | "
        f"{rounds['p50']:.1f} | {rounds['p90']:.1f} | {rounds['max']:.0f} |",
        f"| Seconds | {duration['mean']:.2f} | {duration['cv']:.3f} | {duration['p10']:.1f} | "
        f"{duration['p50']:.1f} | {duration['p90']:.1f} | {duration['max']:.1f} |",
        "",
        "## Contribution",
        "",
        "| Unit | Team | Dmg share | 95% CI | DPS | Taken | Heal share | Survival | Deaths |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for uid, unit in sorted(
        report["units"].items(), key=lambda item: (-item[1]["damage_share"]["mean"], item[0])
    ):
        share = unit["damage_share"]
        lines.append(
            f"| {uid} | {unit['team']} | {share['mean']:.3f} | "
            f"{share['low']:.3f}-{share['high']:.3f} | {unit['dps']:.1f} | "
            f"{unit['damage_taken_share']:.3f} | {unit['healing_share']:.3f} | "
            f"{unit['survival_rate']:.3f} | {unit['death_rate']:.3f} |"
        )
    concentration = report["concentration"]
    lines += [
        "",
        "## Roster health",
        "",
        f"- Damage gini: {concentration['gini']:.3f}",
        f"- Top-1 share: {concentration['top1_share']:.3f}",
        f"- Top-3 share: {concentration['top3_share']:.3f}",
        f"- Effective contributors: {concentration['effective_contributors']:.2f} "
        f"of {concentration['roster_size']}",
        f"- Dead weight: {', '.join(report['dead_weight']) or 'none'}",
    ]
    return "\n".join(lines)


def _load_records(path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload, {}
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"], payload.get("run", {})
    raise ValueError(f"{path} does not contain battle records")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate and compare battle records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    aggregate_parser = subparsers.add_parser("aggregate", help="summarise one batch of records")
    aggregate_parser.add_argument("records", help="records JSON produced by sim_runner.py")
    aggregate_parser.add_argument("--team", default=None, help="focus team (default: first team)")
    aggregate_parser.add_argument("--confidence", type=float, default=DEFAULT_CONFIDENCE)
    aggregate_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    aggregate_parser.add_argument("--out", default=None, help="write to a file instead of stdout")

    compare_parser = subparsers.add_parser(
        "compare", help="paired comparison of two batches sharing seeds"
    )
    compare_parser.add_argument("baseline", help="baseline records JSON")
    compare_parser.add_argument("candidate", help="candidate records JSON")
    compare_parser.add_argument("--team", default=None, help="focus team (default: first team)")
    compare_parser.add_argument("--confidence", type=float, default=DEFAULT_CONFIDENCE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "aggregate":
            records, run = _load_records(args.records)
            report = aggregate(records, args.team, args.confidence)
            if "converged" in run:
                report["converged"] = run["converged"]
            text = (
                json.dumps(report, indent=2, sort_keys=True)
                if args.format == "json"
                else render_markdown(report)
            )
            if args.out:
                with open(args.out, "w", encoding="utf-8") as handle:
                    handle.write(text + "\n")
            else:
                print(text)
            return 0
        baseline, _ = _load_records(args.baseline)
        candidate, _ = _load_records(args.candidate)
        team = args.team or sorted({u["team"] for u in baseline[0]["units"].values()})[0]
        result = paired_compare(baseline, candidate, team, args.confidence)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
