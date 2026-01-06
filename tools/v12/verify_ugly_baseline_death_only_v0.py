#!/usr/bin/env python3
"""
Verify V12 ugly baseline (death-only) run_dir evidence (stdlib only).

Exit codes (frozen):
  - 0: PASS or NOT_MEASURABLE (prints WARNING when NOT_MEASURABLE)
  - 2: FAIL
  - 1: ERROR
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return obj


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            s = raw.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path} line {line_no}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be an object at {path} line {line_no}")
            yield line_no, obj


def _count_jsonl(path: Path) -> int:
    n = 0
    for _ln, _rec in _iter_jsonl(path):
        n += 1
    return n


def verify(run_dir: Path, steps_target: int) -> Tuple[str, List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    required = ["run_manifest.json", "errors.jsonl", "life_tick_summary.jsonl", "life_run_summary.json"]
    missing = [x for x in required if not (run_dir / x).exists()]
    if missing:
        errors.extend([f"missing required file: {x}" for x in missing])
        return "FAIL", errors, warnings, stats

    # strict jsonl for errors
    try:
        stats["errors_count"] = _count_jsonl(run_dir / "errors.jsonl")
    except Exception as e:
        errors.append(f"errors.jsonl strict-jsonl failed: {e}")

    # load life_run_summary.json
    try:
        s = _read_json(run_dir / "life_run_summary.json")
    except Exception as e:
        errors.append(f"life_run_summary.json invalid: {e}")
        s = {}

    # Required summary keys
    for k in ["agent_count", "energy_init_E0", "delta_per_tick", "steps_target", "steps_actual", "extinction_tick", "verdict", "reason_codes"]:
        if k not in s:
            errors.append(f"life_run_summary missing key: {k}")

    # Hard v0 constants
    if "delta_per_tick" in s and s.get("delta_per_tick") != -1:
        errors.append(f"delta_per_tick must be -1 for v0, got {s.get('delta_per_tick')!r}")
    if "steps_target" in s and s.get("steps_target") != steps_target:
        warnings.append(f"steps_target in summary differs from verifier arg: {s.get('steps_target')!r} vs {steps_target}")

    # Validate tick summary sequence
    tick_count = 0
    prev_tick_id: Optional[int] = None
    prev_alive: Optional[int] = None
    extinction_tick_first: Optional[int] = None

    try:
        for line_no, rec in _iter_jsonl(run_dir / "life_tick_summary.jsonl"):
            tick_count += 1
            tid = rec.get("tick_id")
            alive = rec.get("alive_count")
            dead_cum = rec.get("dead_count_cum")
            extinct = rec.get("extinct")

            if not isinstance(tid, int) or tid <= 0:
                errors.append(f"tick_id must be positive int at line {line_no}")
                continue
            if prev_tick_id is None:
                if tid != 1:
                    errors.append(f"first tick_id must be 1, got {tid} at line {line_no}")
            else:
                if tid != prev_tick_id + 1:
                    errors.append(f"tick_id must increase by 1: prev={prev_tick_id} cur={tid} at line {line_no}")
            prev_tick_id = tid

            if not isinstance(alive, int) or alive < 0:
                errors.append(f"alive_count must be int>=0 at line {line_no}")
            if not isinstance(dead_cum, int) or dead_cum < 0:
                errors.append(f"dead_count_cum must be int>=0 at line {line_no}")
            if not isinstance(extinct, bool):
                errors.append(f"extinct must be bool at line {line_no}")

            if isinstance(alive, int):
                if prev_alive is not None and alive > prev_alive:
                    errors.append(f"alive_count must be non-increasing (line {line_no}: {prev_alive} -> {alive})")
                prev_alive = alive

                if extinction_tick_first is None and alive == 0:
                    extinction_tick_first = tid

                if extinction_tick_first is not None:
                    # After extinction, must remain extinct and alive==0
                    if alive != 0:
                        errors.append(f"alive_count must remain 0 after extinction (line {line_no})")
                    if extinct is not True:
                        errors.append(f"extinct must be true after extinction (line {line_no})")
    except Exception as e:
        errors.append(f"life_tick_summary.jsonl strict-jsonl failed: {e}")

    stats["tick_count"] = tick_count
    stats["extinction_tick_first"] = extinction_tick_first

    # steps_actual constraints
    steps_actual = s.get("steps_actual")
    if isinstance(steps_actual, int):
        if steps_actual != tick_count:
            warnings.append(f"steps_actual != tick_count: {steps_actual} vs {tick_count}")
        if steps_actual < steps_target:
            errors.append(f"steps_actual < steps_target: {steps_actual} < {steps_target}")
    else:
        errors.append("steps_actual must be int in life_run_summary")

    # extinction_tick consistency
    ext_sum = s.get("extinction_tick")
    if ext_sum is None:
        # If we observed extinction in ticks but summary says null, that's inconsistent.
        if extinction_tick_first is not None:
            errors.append(f"extinction_tick is null but extinction observed at tick {extinction_tick_first}")
    elif isinstance(ext_sum, int):
        if extinction_tick_first is None:
            errors.append(f"extinction_tick={ext_sum} but no extinction observed in tick summary")
        elif ext_sum != extinction_tick_first:
            errors.append(f"extinction_tick mismatch: summary={ext_sum} observed={extinction_tick_first}")
    else:
        errors.append("extinction_tick must be int|null")

    # Verdict sanity
    v = s.get("verdict")
    if v is not None and v not in ("PASS", "NOT_MEASURABLE", "FAIL"):
        errors.append(f"life_run_summary.verdict invalid: {v!r}")

    if errors:
        return "FAIL", errors, warnings, stats
    if warnings:
        return "NOT_MEASURABLE", errors, warnings, stats
    return "PASS", errors, warnings, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Ugly baseline run_dir")
    ap.add_argument("--steps_target", type=int, default=5000, help="Expected steps_target (v0 default 5000)")
    ap.add_argument("--output", default="", help="Optional report output path")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1

    verdict, errors, warnings, stats = verify(run_dir, args.steps_target)
    report = {
        "tool": "verify_ugly_baseline_death_only_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "verdict": verdict,
        "steps_target": args.steps_target,
        "stats": stats,
        "errors": errors,
        "warnings": warnings,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))

    if verdict == "FAIL":
        return 2
    if verdict == "NOT_MEASURABLE":
        print("WARNING: verdict=NOT_MEASURABLE (evidence valid but degraded/inconsistent metadata)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


