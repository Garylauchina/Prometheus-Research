#!/usr/bin/env python3
"""
V12.3 Tick loop verifier (Research repo, stdlib only).

This verifies a tick-loop run_dir produces a replayable market_snapshot sequence:
  - required files exist
  - strict JSONL
  - market_snapshot passes minimal sequence integrity:
      * ts_utc monotonic non-decreasing (no backward)
      * snapshot_id unique
      * inst_id constant and equals BTC-USDT-SWAP
      * length >= min_ticks
  - run_manifest.run_kind == "production" (tick loop is mainline driver)

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
        raise ValueError("run_manifest.json must be an object")
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


def _parse_iso_utc(ts: str) -> datetime:
    # Accept both 'Z' and '+00:00'
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _check_required_files(run_dir: Path, required: List[str]) -> List[str]:
    return [name for name in required if not (run_dir / name).exists()]


def verify(run_dir: Path, min_ticks: int, max_backward_ms: int) -> Tuple[str, List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    required = ["run_manifest.json", "okx_api_calls.jsonl", "errors.jsonl", "market_snapshot.jsonl"]
    missing = _check_required_files(run_dir, required)
    if missing:
        errors.extend([f"missing required file: {x}" for x in missing])
        return "FAIL", errors, warnings, stats

    try:
        manifest = _read_json(run_dir / "run_manifest.json")
    except Exception as e:
        return "FAIL", [f"run_manifest.json invalid: {e}"], warnings, stats

    rk = manifest.get("run_kind")
    if rk != "production":
        errors.append(f"run_manifest.run_kind must be 'production' for tick loop, got {rk!r}")

    # strict jsonl for api_calls/errors (we only count here)
    try:
        stats["okx_api_calls_count"] = _count_jsonl(run_dir / "okx_api_calls.jsonl")
    except Exception as e:
        errors.append(f"okx_api_calls.jsonl strict-jsonl failed: {e}")
    try:
        stats["errors_count"] = _count_jsonl(run_dir / "errors.jsonl")
    except Exception as e:
        errors.append(f"errors.jsonl strict-jsonl failed: {e}")

    # snapshot sequence checks
    snapshot_ids = set()
    tick = 0
    prev_ts: Optional[datetime] = None
    backward_count = 0
    inst_id_bad = 0

    try:
        for line_no, rec in _iter_jsonl(run_dir / "market_snapshot.jsonl"):
            tick += 1
            sid = rec.get("snapshot_id")
            if not isinstance(sid, str) or not sid:
                errors.append(f"market_snapshot.snapshot_id missing/invalid at line {line_no}")
            else:
                if sid in snapshot_ids:
                    errors.append(f"duplicate snapshot_id at line {line_no}: {sid}")
                snapshot_ids.add(sid)

            inst = rec.get("inst_id")
            if inst != "BTC-USDT-SWAP":
                inst_id_bad += 1

            ts = rec.get("ts_utc")
            if not isinstance(ts, str) or not ts:
                errors.append(f"market_snapshot.ts_utc missing/invalid at line {line_no}")
                continue
            try:
                cur_ts = _parse_iso_utc(ts)
            except Exception:
                errors.append(f"market_snapshot.ts_utc not isoformat at line {line_no}: {ts!r}")
                continue

            if prev_ts is not None:
                delta_ms = int((cur_ts - prev_ts).total_seconds() * 1000)
                if delta_ms < -max_backward_ms:
                    backward_count += 1
                    errors.append(f"ts_utc went backward by {delta_ms}ms at line {line_no}")
            prev_ts = cur_ts
    except Exception as e:
        errors.append(f"market_snapshot.jsonl strict-jsonl failed: {e}")

    stats["tick_count"] = tick
    stats["unique_snapshot_id_count"] = len(snapshot_ids)
    stats["inst_id_bad_count"] = inst_id_bad
    stats["ts_backward_count"] = backward_count

    if tick < min_ticks:
        errors.append(f"tick_count < min_ticks: {tick} < {min_ticks}")

    if inst_id_bad > 0:
        errors.append(f"inst_id not BTC-USDT-SWAP for {inst_id_bad} record(s)")

    if errors:
        return "FAIL", errors, warnings, stats

    # Optional: if many errors.jsonl records exist, we can downgrade to NOT_MEASURABLE
    # v0 conservative: errors_count > 0 -> NOT_MEASURABLE (evidence valid but degraded)
    if stats.get("errors_count", 0) > 0:
        warnings.append("errors.jsonl non-empty: degraded run (NOT_MEASURABLE)")
        return "NOT_MEASURABLE", errors, warnings, stats

    return "PASS", errors, warnings, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Tick loop run_dir to verify")
    ap.add_argument("--min_ticks", type=int, default=60, help="Minimum tick count required for PASS")
    ap.add_argument("--max_backward_ms", type=int, default=0, help="Allowed backward time drift (ms)")
    ap.add_argument("--output", default="", help="Optional report output path")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1

    verdict, errors, warnings, stats = verify(run_dir, args.min_ticks, args.max_backward_ms)

    report = {
        "tool": "verify_tick_loop_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "verdict": verdict,
        "min_ticks": args.min_ticks,
        "max_backward_ms": args.max_backward_ms,
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
        print("WARNING: verdict=NOT_MEASURABLE (evidence valid but degraded)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


