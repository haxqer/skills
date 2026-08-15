#!/usr/bin/env python3
"""Regression gate: compare a candidate report against a baseline and thresholds.

Exit codes: 0 all checks passed, 1 tool error, 2 at least one threshold violated.
That separation lets the gate run unattended without hiding real failures.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import Any

from sim_report import get_path


def load_thresholds(path: str) -> list[dict[str, Any]]:
    """Read the acceptance table. Blank cells mean "no bound on this side"."""
    rows: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as handle:
        for line_number, raw in enumerate(csv.DictReader(handle), start=2):
            metric = (raw.get("metric") or "").strip()
            if not metric or metric.startswith("#"):
                continue
            entry: dict[str, Any] = {"metric": metric, "note": (raw.get("note") or "").strip()}
            for key in ("min", "max", "max_delta", "max_delta_pct"):
                value = (raw.get(key) or "").strip()
                if not value:
                    entry[key] = None
                    continue
                try:
                    entry[key] = float(value)
                except ValueError as error:
                    raise ValueError(
                        f"{path}:{line_number}: {key} must be numeric, got {value!r}"
                    ) from error
            rows.append(entry)
    if not rows:
        raise ValueError(f"{path} contains no threshold rows")
    return rows


def _load_report(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or "win_rate" not in payload:
        raise ValueError(f"{path} is not an aggregated report; run sim_report.py aggregate first")
    return payload


def evaluate(
    candidate: dict[str, Any],
    thresholds: list[dict[str, Any]],
    baseline: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Score every threshold row and explain each failure."""
    results = []
    for rule in thresholds:
        entry: dict[str, Any] = {"metric": rule["metric"], "note": rule["note"]}
        try:
            value = float(get_path(candidate, rule["metric"]))
        except (KeyError, TypeError, ValueError):
            entry.update({"status": "missing", "reasons": ["metric not present in report"]})
            results.append(entry)
            continue
        entry["candidate"] = value
        reasons: list[str] = []
        if rule["min"] is not None and value < rule["min"]:
            reasons.append(f"{value:.6g} < min {rule['min']:.6g}")
        if rule["max"] is not None and value > rule["max"]:
            reasons.append(f"{value:.6g} > max {rule['max']:.6g}")
        if baseline is not None:
            try:
                before = float(get_path(baseline, rule["metric"]))
            except (KeyError, TypeError, ValueError):
                before = None
            if before is not None:
                entry["baseline"] = before
                entry["delta"] = value - before
                if rule["max_delta"] is not None and abs(value - before) > rule["max_delta"]:
                    reasons.append(
                        f"delta {value - before:+.6g} exceeds max_delta {rule['max_delta']:.6g}"
                    )
                if rule["max_delta_pct"] is not None and before:
                    change = abs(value - before) / abs(before)
                    entry["delta_pct"] = (value - before) / before
                    if change > rule["max_delta_pct"]:
                        reasons.append(
                            f"relative delta {change:.4f} exceeds "
                            f"max_delta_pct {rule['max_delta_pct']:.4f}"
                        )
        entry["reasons"] = reasons
        entry["status"] = "fail" if reasons else "pass"
        results.append(entry)
    return results


def render_markdown(results: list[dict[str, Any]], candidate_meta: dict[str, Any]) -> str:
    failures = [row for row in results if row["status"] != "pass"]
    header = "PASS" if not failures else f"FAIL ({len(failures)} of {len(results)})"
    lines = [
        f"# Regression gate: {header}",
        "",
        f"Candidate samples: {candidate_meta.get('samples', 'unknown')} "
        f"(converged: {candidate_meta.get('converged')})",
        "",
        "| Metric | Baseline | Candidate | Delta | Status | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in results:
        baseline = row.get("baseline")
        delta = row.get("delta")
        lines.append(
            "| {metric} | {baseline} | {candidate} | {delta} | {status} | {reason} |".format(
                metric=row["metric"],
                baseline="-" if baseline is None else f"{baseline:.6g}",
                candidate="-" if row.get("candidate") is None else f"{row['candidate']:.6g}",
                delta="-" if delta is None else f"{delta:+.6g}",
                status=row["status"],
                reason="; ".join(row.get("reasons") or []) or row.get("note") or "",
            )
        )
    if candidate_meta.get("converged") is False:
        lines += ["", "**Candidate run did not converge; treat every verdict above as provisional.**"]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a candidate report against acceptance thresholds and a baseline."
    )
    parser.add_argument("candidate", help="aggregated report JSON for the candidate build")
    parser.add_argument("thresholds", help="acceptance thresholds CSV")
    parser.add_argument("--baseline", default=None, help="aggregated report JSON for the baseline")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        candidate = _load_report(args.candidate)
        baseline = _load_report(args.baseline) if args.baseline else None
        thresholds = load_thresholds(args.thresholds)
        results = evaluate(candidate, thresholds, baseline)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    meta = {"samples": candidate.get("samples"), "converged": candidate.get("converged")}
    if args.format == "json":
        print(json.dumps({"meta": meta, "results": results}, indent=2, sort_keys=True))
    else:
        print(render_markdown(results, meta))
    return 2 if any(row["status"] != "pass" for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
