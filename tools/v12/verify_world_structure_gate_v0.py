#!/usr/bin/env python3
"""
Verify World Structure Gate (W0) for V12 replay_truth experiments (Research repo, stdlib only).

Purpose:
  - Fail-closed on evidence parsing errors (FAIL).
  - Produce an auditable verdict whether the chosen "world signal" is informative enough
    to test "world-coupling" hypotheses (PASS/NOT_MEASURABLE).

Exit codes (frozen):
  - 0: PASS or NOT_MEASURABLE (prints WARNING when NOT_MEASURABLE)
  - 2: FAIL
  - 1: ERROR
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return obj


def _pct(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    if q <= 0:
        return float(min(values))
    if q >= 1:
        return float(max(values))
    xs = sorted(values)
    # linear interpolation
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(xs[lo])
    w = pos - lo
    return float(xs[lo] * (1 - w) + xs[hi] * w)


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _compute_abs_log_returns(px: List[float], k: int) -> List[float]:
    out: List[float] = []
    if k <= 0:
        return out
    for i in range(k, len(px)):
        a = px[i - k]
        b = px[i]
        if a <= 0 or b <= 0:
            continue
        out.append(abs(math.log(b / a)))
    return out


def _stats(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0}
    m = mean(values)
    s = pstdev(values) if len(values) >= 2 else 0.0
    return {
        "count": len(values),
        "min": float(min(values)),
        "mean": float(m),
        "std": float(s),
        "p50": _pct(values, 0.50),
        "p90": _pct(values, 0.90),
        "p99": _pct(values, 0.99),
        "max": float(max(values)),
    }


def verify(
    market_snapshot_jsonl: Path,
    k_windows: List[int],
    p99_threshold: float,
    min_samples: int,
) -> Tuple[str, List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    if not market_snapshot_jsonl.exists():
        return "FAIL", [f"missing required file: {market_snapshot_jsonl}"], warnings, stats

    px: List[float] = []
    bad_px = 0
    total = 0
    try:
        for _ln, rec in _iter_jsonl(market_snapshot_jsonl):
            total += 1
            v = _safe_float(rec.get("last_px"))
            if v is None or v <= 0:
                bad_px += 1
                continue
            px.append(v)
    except Exception as e:
        return "FAIL", [f"market_snapshot.jsonl strict-jsonl failed: {e}"], warnings, stats

    stats["input"] = {
        "record_count": total,
        "last_px_valid_count": len(px),
        "last_px_invalid_count": bad_px,
    }

    if len(px) < max(k_windows) + 2:
        errors.append(f"insufficient valid last_px samples: {len(px)} for k_max={max(k_windows)}")
        return "FAIL", errors, warnings, stats

    per_k: Dict[str, Any] = {}
    primary_k = max(k_windows)
    primary_p99: Optional[float] = None

    for k in sorted(set(k_windows)):
        vals = _compute_abs_log_returns(px, k)
        per_k[str(k)] = _stats(vals)
        if k == primary_k:
            primary_p99 = per_k[str(k)].get("p99")

    stats["abs_log_return_by_k"] = per_k
    stats["primary_k"] = primary_k
    stats["primary_p99_threshold"] = p99_threshold
    stats["min_samples"] = min_samples

    # sample gate: ensure primary stats have enough samples
    primary_count = int(per_k[str(primary_k)].get("count", 0))
    if primary_count < min_samples:
        warnings.append(f"primary_k sample_count < min_samples: {primary_count} < {min_samples}")
        return "NOT_MEASURABLE", errors, warnings, stats

    if primary_p99 is None:
        warnings.append("primary_k p99 missing")
        return "NOT_MEASURABLE", errors, warnings, stats

    if float(primary_p99) < p99_threshold:
        warnings.append(
            f"world_structure_too_flat:last_px_abs_log_return_p99_lt_threshold "
            f"(p99={float(primary_p99):.10f} < {p99_threshold})"
        )
        return "NOT_MEASURABLE", errors, warnings, stats

    return "PASS", errors, warnings, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dataset_dir", default="", help="Replay dataset dir (contains market_snapshot.jsonl)")
    src.add_argument("--run_dir", default="", help="Run dir containing market_snapshot.jsonl")
    ap.add_argument("--k_windows", default="1,100,500", help="Comma-separated k windows for abs log returns")
    ap.add_argument(
        "--p99_threshold",
        type=float,
        default=0.001,
        help="Primary-k p99 threshold (default 0.001, approx 0.1 percent)",
    )
    ap.add_argument("--min_samples", type=int, default=1000, help="Minimum primary-k samples required (default 1000)")
    ap.add_argument("--output", default="", help="Optional report output path")
    args = ap.parse_args()

    k_windows: List[int] = []
    for part in args.k_windows.split(","):
        part = part.strip()
        if not part:
            continue
        k_windows.append(int(part))
    if not k_windows:
        print("ERROR: k_windows is empty", file=sys.stderr)
        return 1

    base_dir = Path(args.dataset_dir or args.run_dir).expanduser().resolve()
    if not base_dir.exists():
        print(f"ERROR: path not found: {base_dir}", file=sys.stderr)
        return 1

    market_snapshot_jsonl = base_dir / "market_snapshot.jsonl"
    verdict, errors, warnings, stats = verify(
        market_snapshot_jsonl=market_snapshot_jsonl,
        k_windows=k_windows,
        p99_threshold=args.p99_threshold,
        min_samples=args.min_samples,
    )

    report = {
        "tool": "verify_world_structure_gate_v0",
        "generated_at_utc": _ts_utc(),
        "input_path": str(base_dir),
        "market_snapshot_jsonl": str(market_snapshot_jsonl),
        "verdict": verdict,
        "k_windows": k_windows,
        "primary_k": stats.get("primary_k"),
        "p99_threshold": args.p99_threshold,
        "min_samples": args.min_samples,
        "stats": stats,
        "errors": errors,
        "warnings": warnings,
    }

    out_path = Path(args.output).expanduser().resolve() if args.output else None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))

    if verdict == "FAIL":
        return 2
    if verdict == "NOT_MEASURABLE":
        print("WARNING: verdict=NOT_MEASURABLE (world structure too flat / not enough samples)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


