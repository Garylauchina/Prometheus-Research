#!/usr/bin/env python3
"""
V12 Local Reachability calibration — World pressure association (single-world) v0.

Fail-closed:
  - Requires interaction_impedance.jsonl with metrics.world_u
  - Requires local_reachability.jsonl with neighborhood.feasible_ratio and tick_index
  - Requires strict 1:1 join on tick_index for all ticks (0..N-1)

Outputs:
  - per-run JSON report
  - aggregate JSON report (3 runs expected but tool supports N>=1)

No external deps (stdlib only).
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


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


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _percentile(xs: List[float], q: float) -> float:
    if not xs:
        return float("nan")
    xs2 = sorted(xs)
    if q <= 0:
        return xs2[0]
    if q >= 1:
        return xs2[-1]
    i = (len(xs2) - 1) * q
    lo = int(math.floor(i))
    hi = int(math.ceil(i))
    if lo == hi:
        return xs2[lo]
    w = i - lo
    return xs2[lo] * (1.0 - w) + xs2[hi] * w


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


def _rankdata(xs: List[float]) -> List[float]:
    """
    Average ranks for ties, 1..n.
    """
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        # average rank for ties
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(x: List[float], y: List[float]) -> Optional[float]:
    n = len(x)
    if n == 0 or n != len(y):
        return None
    mx = sum(x) / n
    my = sum(y) / n
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    if vx <= 0 or vy <= 0:
        return None
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return cov / math.sqrt(vx * vy)


def _spearman(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) != len(y) or not x:
        return None
    rx = _rankdata(x)
    ry = _rankdata(y)
    return _pearson(rx, ry)


def _read_world_u_by_tick(path: Path) -> Dict[int, float]:
    """
    Prefer explicit tick_index if present; otherwise fall back to strict implicit ordering (0..N-1).
    Fail-closed semantics:
      - If any record has tick_index, then all must, and must match implicit order.
      - If none have tick_index, we still require strict contiguous implicit order.
    """
    out: Dict[int, float] = {}
    saw_tick_index = False
    saw_missing_tick_index = False
    implicit_i = 0
    for _ln, rec in _iter_jsonl(path):
        ti = rec.get("tick_index")
        if ti is None:
            saw_missing_tick_index = True
            ti_int = implicit_i
        else:
            saw_tick_index = True
            if not _is_int(ti):
                raise ValueError(f"invalid tick_index type in {path}: {type(ti)}")
            ti_int = int(ti)
            if ti_int != implicit_i:
                raise ValueError(
                    f"tick_index does not match implicit ordering in {path}: got {ti_int} expected {implicit_i}"
                )

        metrics = rec.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"missing metrics object in {path} at tick_index={ti_int}")
        u = metrics.get("world_u")
        if not _is_num(u):
            raise ValueError(f"missing/invalid metrics.world_u in {path} at tick_index={ti_int}")

        out[implicit_i] = float(u)
        implicit_i += 1

    if saw_tick_index and saw_missing_tick_index:
        raise ValueError(f"inconsistent presence of tick_index in {path} (fail-closed)")
    return out


def _read_fr_by_tick(path: Path) -> Dict[int, float]:
    """
    local_reachability.jsonl is required to have tick_index; we also enforce that it matches implicit ordering.
    This gives us a strict, auditable alignment to implicit (0..N-1) ordering.
    """
    out: Dict[int, float] = {}
    implicit_i = 0
    for _ln, rec in _iter_jsonl(path):
        ti = rec.get("tick_index")
        if ti is None:
            raise ValueError(f"missing tick_index in {path} (fail-closed)")
        if not _is_int(ti):
            raise ValueError(f"invalid tick_index type in {path}: {type(ti)}")
        ti_int = int(ti)
        if ti_int != implicit_i:
            raise ValueError(
                f"tick_index does not match implicit ordering in {path}: got {ti_int} expected {implicit_i}"
            )
        nb = rec.get("neighborhood")
        if not isinstance(nb, dict):
            raise ValueError(f"missing neighborhood object in {path} at tick_index={ti_int}")
        fr = nb.get("feasible_ratio")
        if not _is_num(fr):
            raise ValueError(f"missing/invalid neighborhood.feasible_ratio in {path} at tick_index={ti_int}")
        out[implicit_i] = float(fr)
        implicit_i += 1
    return out


def _aligned_series(u_by: Dict[int, float], fr_by: Dict[int, float]) -> Tuple[List[float], List[float]]:
    if not u_by or not fr_by:
        raise ValueError("empty series (fail-closed)")
    keys_u = set(u_by.keys())
    keys_fr = set(fr_by.keys())
    if keys_u != keys_fr:
        missing_u = sorted(keys_fr - keys_u)
        missing_fr = sorted(keys_u - keys_fr)
        raise ValueError(f"tick_index mismatch (fail-closed). missing_u={missing_u[:5]} missing_fr={missing_fr[:5]}")
    ks = sorted(keys_u)
    # require contiguous 0..N-1 for strictness
    if ks[0] != 0 or ks[-1] != len(ks) - 1:
        raise ValueError(f"tick_index not contiguous 0..N-1 (fail-closed): min={ks[0]} max={ks[-1]} n={len(ks)}")
    u = [u_by[k] for k in ks]
    fr = [fr_by[k] for k in ks]
    return u, fr


def _quantile_delta(u: List[float], fr: List[float], q: float = 0.10) -> Dict[str, Any]:
    n = len(u)
    if n == 0 or n != len(fr):
        raise ValueError("invalid lengths for quantile_delta")
    # compute thresholds by percentile on u
    u_sorted = sorted(u)
    lo_thr = _percentile(u_sorted, q)
    hi_thr = _percentile(u_sorted, 1.0 - q)
    lo = [fr_i for u_i, fr_i in zip(u, fr) if u_i <= lo_thr]
    hi = [fr_i for u_i, fr_i in zip(u, fr) if u_i >= hi_thr]
    if not lo or not hi:
        raise ValueError("empty quantile buckets (fail-closed)")
    delta = (sum(lo) / len(lo)) - (sum(hi) / len(hi))
    return {
        "q": q,
        "lo_thr": lo_thr,
        "hi_thr": hi_thr,
        "lo_count": len(lo),
        "hi_count": len(hi),
        "mean_fr_lo": sum(lo) / len(lo),
        "mean_fr_hi": sum(hi) / len(hi),
        "delta": delta,
    }


def _windowed_eval(u: List[float], fr: List[float], window: int) -> Dict[str, Any]:
    n = len(u)
    if window <= 0 or window > n:
        raise ValueError("invalid window")
    rhos: List[float] = []
    deltas: List[float] = []
    for start in range(0, n, window):
        end = min(n, start + window)
        uu = u[start:end]
        ff = fr[start:end]
        y = [1.0 - x for x in ff]
        rho = _spearman(uu, y)
        if rho is None or not math.isfinite(rho):
            continue
        qd = _quantile_delta(uu, ff, q=0.10)
        rhos.append(float(rho))
        deltas.append(float(qd["delta"]))
    return {
        "window": window,
        "segments": len(rhos),
        "rho": _stats(rhos),
        "delta": _stats(deltas),
    }


@dataclass
class Thresholds:
    rho_min: float
    delta_min: float
    rho_win_min: float
    delta_win_min: float


def _evaluate_one(run_dir: Path, thresholds: Thresholds, windows: List[int]) -> Dict[str, Any]:
    p_imp = run_dir / "interaction_impedance.jsonl"
    p_lr = run_dir / "local_reachability.jsonl"
    if not p_imp.exists():
        raise FileNotFoundError(f"missing required file: {p_imp}")
    if not p_lr.exists():
        raise FileNotFoundError(f"missing required file: {p_lr}")

    u_by = _read_world_u_by_tick(p_imp)
    fr_by = _read_fr_by_tick(p_lr)
    u, fr = _aligned_series(u_by, fr_by)
    y = [1.0 - x for x in fr]

    rho = _spearman(u, y)
    if rho is None or not math.isfinite(rho):
        raise ValueError("spearman undefined (fail-closed)")
    qd = _quantile_delta(u, fr, q=0.10)

    win_reports = [_windowed_eval(u, fr, w) for w in windows]

    # pass/fail checks
    checks: List[Dict[str, Any]] = []
    checks.append(
        {
            "name": "full_series_sign",
            "pass": (rho > 0.0 and qd["delta"] > 0.0),
            "rho": rho,
            "delta": qd["delta"],
        }
    )
    checks.append(
        {
            "name": "full_series_thresholds",
            "pass": (rho >= thresholds.rho_min and qd["delta"] >= thresholds.delta_min),
            "rho_min": thresholds.rho_min,
            "delta_min": thresholds.delta_min,
            "rho": rho,
            "delta": qd["delta"],
        }
    )
    # epoch robustness: require per-window p50 >= threshold and sign positive on p50
    for wr in win_reports:
        rho_p50 = wr["rho"].get("p50")
        delta_p50 = wr["delta"].get("p50")
        ok = (
            _is_num(rho_p50)
            and _is_num(delta_p50)
            and float(rho_p50) >= thresholds.rho_win_min
            and float(delta_p50) >= thresholds.delta_win_min
        )
        checks.append(
            {
                "name": f"epoch_robustness_window_{wr['window']}",
                "pass": ok,
                "rho_p50": rho_p50,
                "delta_p50": delta_p50,
                "rho_win_min": thresholds.rho_win_min,
                "delta_win_min": thresholds.delta_win_min,
            }
        )

    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    return {
        "tool": "calibrate_local_reachability_world_pressure_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "inputs": {
            "interaction_impedance_jsonl": str(p_imp),
            "local_reachability_jsonl": str(p_lr),
            "records": len(u),
        },
        "series": {
            "world_u": _stats(u),
            "feasible_ratio": _stats(fr),
        },
        "eval": {
            "spearman_rho_u_vs_(1-fr)": rho,
            "quantile_delta_fr_lo_minus_hi": qd,
            "windowed": win_reports,
        },
        "checks": checks,
        "verdict": verdict,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--rho_min", type=float, default=0.15)
    ap.add_argument("--delta_min", type=float, default=0.02)
    ap.add_argument("--rho_win_min", type=float, default=0.10)
    ap.add_argument("--delta_win_min", type=float, default=0.015)
    ap.add_argument("--windows", default="1000,5000,10000")
    args = ap.parse_args()

    run_dirs: List[str] = []
    for ln in Path(args.run_dirs_file).expanduser().read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            run_dirs.append(s)
    if not run_dirs:
        raise SystemExit("empty run_dirs_file")

    windows: List[int] = []
    for part in args.windows.split(","):
        p = part.strip()
        if p:
            windows.append(int(p))
    if not windows:
        raise SystemExit("empty windows")

    thresholds = Thresholds(
        rho_min=float(args.rho_min),
        delta_min=float(args.delta_min),
        rho_win_min=float(args.rho_win_min),
        delta_win_min=float(args.delta_win_min),
    )

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    per_run_reports: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        try:
            rep = _evaluate_one(run_dir, thresholds, windows)
            per_run_reports.append(rep)
            (out_dir / f"per_run_{run_dir.name}.json").write_text(
                json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception as e:
            failures.append({"run_dir": str(run_dir), "error": str(e)})

    # aggregate
    rhos = [float(r["eval"]["spearman_rho_u_vs_(1-fr)"]) for r in per_run_reports if _is_num(r["eval"]["spearman_rho_u_vs_(1-fr)"])]
    deltas = [float(r["eval"]["quantile_delta_fr_lo_minus_hi"]["delta"]) for r in per_run_reports if _is_num(r["eval"]["quantile_delta_fr_lo_minus_hi"]["delta"])]
    verdict = "PASS" if failures == [] and per_run_reports and all(r["verdict"] == "PASS" for r in per_run_reports) else "FAIL"

    agg = {
        "tool": "calibrate_local_reachability_world_pressure_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {
            "run_dirs_file": str(Path(args.run_dirs_file).expanduser().resolve()),
            "run_dirs_count": len(run_dirs),
            "thresholds": {
                "rho_min": thresholds.rho_min,
                "delta_min": thresholds.delta_min,
                "rho_win_min": thresholds.rho_win_min,
                "delta_win_min": thresholds.delta_win_min,
            },
            "windows": windows,
        },
        "aggregate": {
            "rho_stats": _stats(rhos),
            "delta_stats": _stats(deltas),
            "per_run_verdicts": [{"run_dir": r["run_dir"], "verdict": r["verdict"]} for r in per_run_reports],
        },
        "failures": failures,
        "verdict": verdict,
        "notes": "Do-or-die calibration for single-world association u_t -> (1-feasible_ratio_t).",
    }
    (out_dir / "aggregate.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

