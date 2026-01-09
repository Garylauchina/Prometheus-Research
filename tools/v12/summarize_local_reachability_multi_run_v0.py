#!/usr/bin/env python3
"""
V12 Local Reachability multi-run summary v0 (Research repo, stdlib only).

Purpose:
  - Aggregate descriptive stats across multiple run_dirs that contain local_reachability.jsonl
  - Produce:
      * per-run feasible_ratio stats
      * aggregate distribution of per-run means (not a verdict)

No thresholds, no pass/fail.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            s = raw.strip()
            if not s:
                continue
            obj = json.loads(s)
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be an object at {path} line {line_no}")
            yield line_no, obj


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _percentile(xs: List[float], q: float) -> float:
    if not xs:
        return float("nan")
    if q <= 0:
        return xs[0]
    if q >= 1:
        return xs[-1]
    i = (len(xs) - 1) * q
    lo = int(math.floor(i))
    hi = int(math.ceil(i))
    if lo == hi:
        return xs[lo]
    w = i - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def _stats(xs: List[float]) -> Dict[str, Any]:
    if not xs:
        return {"count": 0}
    xs2 = sorted(xs)
    mean = sum(xs2) / len(xs2)
    return {
        "count": len(xs2),
        "min": xs2[0],
        "p50": _percentile(xs2, 0.50),
        "p90": _percentile(xs2, 0.90),
        "p99": _percentile(xs2, 0.99),
        "max": xs2[-1],
        "mean": mean,
    }


def _read_run_feasible_ratios(run_dir: Path) -> List[float]:
    p = run_dir / "local_reachability.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"missing local_reachability.jsonl: {p}")

    fr: List[float] = []
    for _ln, rec in _iter_jsonl(p):
        nb = rec.get("neighborhood")
        if not isinstance(nb, dict):
            continue
        x = nb.get("feasible_ratio")
        if not _is_num(x):
            continue
        fr.append(float(x))
    return fr


def _parse_run_dirs_arg(s: str) -> List[str]:
    out: List[str] = []
    for part in s.split(","):
        p = part.strip()
        if p:
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs", default="", help="comma-separated run_dir paths")
    ap.add_argument("--run_dirs_file", default="", help="text file with one run_dir per line")
    ap.add_argument("--output_json", required=True)
    args = ap.parse_args()

    run_dirs: List[str] = []
    if args.run_dirs:
        run_dirs.extend(_parse_run_dirs_arg(str(args.run_dirs)))
    if args.run_dirs_file:
        p = Path(args.run_dirs_file).expanduser().resolve()
        lines = p.read_text(encoding="utf-8").splitlines()
        for ln in lines:
            s = ln.strip()
            if s and not s.startswith("#"):
                run_dirs.append(s)

    if not run_dirs:
        raise SystemExit("no run_dirs provided")

    per_run: List[Dict[str, Any]] = []
    per_run_means: List[float] = []
    failures: List[Dict[str, Any]] = []

    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        try:
            fr = _read_run_feasible_ratios(run_dir)
            st = _stats(fr)
            per_run.append(
                {
                    "run_dir": str(run_dir),
                    "local_reachability_jsonl": str(run_dir / "local_reachability.jsonl"),
                    "feasible_ratio": st,
                }
            )
            if st.get("count", 0) > 0 and _is_num(st.get("mean")):
                per_run_means.append(float(st["mean"]))
        except Exception as e:
            failures.append({"run_dir": str(run_dir), "error": str(e)})

    report = {
        "tool": "summarize_local_reachability_multi_run_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {"run_dirs_count": len(run_dirs), "run_dirs": run_dirs},
        "per_run": per_run,
        "aggregate": {"per_run_mean_feasible_ratio": _stats(per_run_means)},
        "failures": failures,
        "notes": "Descriptive only. No thresholds, no verdict. Failures are reported but not treated as PASS/FAIL here.",
    }

    out = Path(args.output_json).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

