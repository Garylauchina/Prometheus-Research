#!/usr/bin/env python3
"""
V12 Local Reachability summary report v0 (Research repo, stdlib only).

Descriptive only:
  - feasible_ratio distribution
  - per-account Δfeasible_ratio (first difference over tick_index)

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
    s = sum(xs2)
    mean = s / len(xs2)
    return {
        "count": len(xs2),
        "min": xs2[0],
        "p50": _percentile(xs2, 0.50),
        "p90": _percentile(xs2, 0.90),
        "p99": _percentile(xs2, 0.99),
        "max": xs2[-1],
        "mean": mean,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--output_json", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    p = run_dir / "local_reachability.jsonl"
    if not p.exists():
        raise SystemExit(f"missing: {p}")

    fr_all: List[float] = []
    fr_by_account: Dict[str, List[Tuple[int, float]]] = {}

    for _ln, rec in _iter_jsonl(p):
        aid = rec.get("account_id_hash")
        ti = rec.get("tick_index")
        nb = rec.get("neighborhood")
        if not (isinstance(aid, str) and isinstance(ti, int) and isinstance(nb, dict)):
            continue
        fr = nb.get("feasible_ratio")
        if not _is_num(fr):
            continue
        frf = float(fr)
        fr_all.append(frf)
        fr_by_account.setdefault(aid, []).append((int(ti), frf))

    deltas: List[float] = []
    for aid, seq in fr_by_account.items():
        seq2 = sorted(seq, key=lambda x: x[0])
        prev = None
        for _ti, fr in seq2:
            if prev is not None:
                deltas.append(fr - prev)
            prev = fr

    report = {
        "tool": "summarize_local_reachability_report_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "local_reachability_jsonl": str(p),
        "feasible_ratio": _stats(fr_all),
        "delta_feasible_ratio": _stats(deltas),
        "notes": "Descriptive only. No thresholds, no verdict.",
    }

    out = Path(args.output_json).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

