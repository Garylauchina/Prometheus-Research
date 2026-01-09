#!/usr/bin/env python3
"""
V12 World Pressure calibration via Gate Transfer Function (Suppression) v0.

Fail-closed:
  - Requires decision_trace.jsonl and interaction_impedance.jsonl
  - Enforces strict implicit ordering join with line-by-line ts_utc equality
  - suppression(t) must be within [0,1] (tolerance 1e-9)

Outputs:
  - per-run JSON reports
  - aggregate JSON report

Exit codes:
  - 0: PASS (all runs)
  - 2: FAIL (any run fails thresholds) or evidence violation
"""

from __future__ import annotations

import argparse
import json
import math
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
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
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
    return _pearson(_rankdata(x), _rankdata(y))


def _quantile_delta(u: List[float], x: List[float], q: float = 0.10) -> Dict[str, Any]:
    u_sorted = sorted(u)
    lo_thr = _percentile(u_sorted, q)
    hi_thr = _percentile(u_sorted, 1.0 - q)
    lo = [xi for ui, xi in zip(u, x) if ui <= lo_thr]
    hi = [xi for ui, xi in zip(u, x) if ui >= hi_thr]
    if not lo or not hi:
        raise ValueError("empty quantile buckets (fail-closed)")
    return {
        "q": q,
        "lo_thr": lo_thr,
        "hi_thr": hi_thr,
        "lo_count": len(lo),
        "hi_count": len(hi),
        "mean_x_lo": sum(lo) / len(lo),
        "mean_x_hi": sum(hi) / len(hi),
        "delta": (sum(hi) / len(hi)) - (sum(lo) / len(lo)),
    }


@dataclass
class Thresholds:
    rho_min: float
    delta_min: float
    rho_seg_min: float
    delta_seg_min: float


def _read_series(run_dir: Path) -> Tuple[List[float], List[float]]:
    """
    Returns:
      u_t list (for ticks with interaction_intensity>0),
      suppression_t list
    Enforces implicit ordering join with ts_utc equality.
    """
    p_dec = run_dir / "decision_trace.jsonl"
    p_imp = run_dir / "interaction_impedance.jsonl"
    if not p_dec.exists():
        raise FileNotFoundError(f"missing required file: {p_dec}")
    if not p_imp.exists():
        raise FileNotFoundError(f"missing required file: {p_imp}")

    dec_ts: List[str] = []
    inter: List[float] = []
    post: List[float] = []
    for _ln, rec in _iter_jsonl(p_dec):
        ts = rec.get("ts_utc")
        if not isinstance(ts, str) or not ts:
            raise ValueError(f"missing/invalid ts_utc in {p_dec}")
        ii = rec.get("interaction_intensity")
        pi = rec.get("post_gate_intensity")
        if not _is_num(ii) or not _is_num(pi):
            raise ValueError(f"missing/invalid intensity fields in {p_dec} at ts_utc={ts}")
        dec_ts.append(ts)
        inter.append(float(ii))
        post.append(float(pi))

    imp_ts: List[str] = []
    u_all: List[float] = []
    for _ln, rec in _iter_jsonl(p_imp):
        ts = rec.get("ts_utc")
        if not isinstance(ts, str) or not ts:
            raise ValueError(f"missing/invalid ts_utc in {p_imp}")
        metrics = rec.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"missing metrics in {p_imp} at ts_utc={ts}")
        uu = metrics.get("world_u")
        if not _is_num(uu):
            raise ValueError(f"missing/invalid metrics.world_u in {p_imp} at ts_utc={ts}")
        imp_ts.append(ts)
        u_all.append(float(uu))

    if len(dec_ts) != len(imp_ts):
        raise ValueError(f"record count mismatch (fail-closed): decision={len(dec_ts)} impedance={len(imp_ts)}")
    for i, (t1, t2) in enumerate(zip(dec_ts, imp_ts)):
        if t1 != t2:
            raise ValueError(f"ts_utc mismatch at line {i}: decision={t1} impedance={t2} (fail-closed)")

    u: List[float] = []
    s: List[float] = []
    for uu, ii, pi in zip(u_all, inter, post):
        if ii <= 0:
            continue
        sup = 1.0 - (pi / ii)
        if sup < -1e-9 or sup > 1.0 + 1e-9:
            raise ValueError(f"suppression out of range (fail-closed): {sup}")
        sup = min(1.0, max(0.0, sup))
        u.append(float(uu))
        s.append(float(sup))
    if len(u) < 100:
        raise ValueError("too few ticks with interaction_intensity>0 (fail-closed)")
    return u, s


def _segment_eval(u: List[float], x: List[float], seg: int) -> Dict[str, Any]:
    rhos: List[float] = []
    deltas: List[float] = []
    n = len(u)
    for start in range(0, n, seg):
        end = min(n, start + seg)
        uu = u[start:end]
        xx = x[start:end]
        if len(uu) < 50:
            continue
        rho = _spearman(uu, xx)
        if rho is None or not math.isfinite(rho):
            continue
        qd = _quantile_delta(uu, xx, q=0.10)
        rhos.append(float(rho))
        deltas.append(float(qd["delta"]))
    return {"segment_size": seg, "segments": len(rhos), "rho": _stats(rhos), "delta": _stats(deltas)}


def _evaluate_one(run_dir: Path, thresholds: Thresholds, seg_sizes: List[int]) -> Dict[str, Any]:
    u, s = _read_series(run_dir)
    rho = _spearman(u, s)
    if rho is None or not math.isfinite(rho):
        raise ValueError("spearman undefined (fail-closed)")
    qd = _quantile_delta(u, s, q=0.10)
    seg_reports = [_segment_eval(u, s, seg=x) for x in seg_sizes]

    checks: List[Dict[str, Any]] = []
    checks.append({"name": "sign", "pass": (rho > 0.0 and qd["delta"] > 0.0), "rho": rho, "delta": qd["delta"]})
    checks.append(
        {
            "name": "min_effect",
            "pass": (rho >= thresholds.rho_min and qd["delta"] >= thresholds.delta_min),
            "rho_min": thresholds.rho_min,
            "delta_min": thresholds.delta_min,
            "rho": rho,
            "delta": qd["delta"],
        }
    )
    for sr in seg_reports:
        rho_p50 = sr["rho"].get("p50")
        delta_p50 = sr["delta"].get("p50")
        ok = (
            _is_num(rho_p50)
            and _is_num(delta_p50)
            and float(rho_p50) >= thresholds.rho_seg_min
            and float(delta_p50) >= thresholds.delta_seg_min
        )
        checks.append(
            {
                "name": f"epoch_robustness_seg_{sr['segment_size']}",
                "pass": ok,
                "rho_p50": rho_p50,
                "delta_p50": delta_p50,
                "rho_seg_min": thresholds.rho_seg_min,
                "delta_seg_min": thresholds.delta_seg_min,
            }
        )

    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    return {
        "tool": "calibrate_world_pressure_gate_transfer_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "inputs": {
            "join": "implicit_ordering_with_ts_utc_equality",
            "decision_trace": str(run_dir / "decision_trace.jsonl"),
            "interaction_impedance": str(run_dir / "interaction_impedance.jsonl"),
        },
        "series_stats": {"world_u": _stats(u), "suppression": _stats(s)},
        "eval": {"spearman_rho_u_vs_suppression": rho, "quantile_delta_hi_minus_lo": qd, "segment_reports": seg_reports},
        "checks": checks,
        "verdict": verdict,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--rho_min", type=float, default=0.15)
    ap.add_argument("--delta_min", type=float, default=0.02)
    ap.add_argument("--rho_seg_min", type=float, default=0.10)
    ap.add_argument("--delta_seg_min", type=float, default=0.015)
    ap.add_argument("--segments", default="1000,5000,10000")
    args = ap.parse_args()

    run_dirs: List[str] = []
    for ln in Path(args.run_dirs_file).expanduser().read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            run_dirs.append(s)
    if not run_dirs:
        raise SystemExit("empty run_dirs_file")

    seg_sizes = [int(x.strip()) for x in args.segments.split(",") if x.strip()]
    if not seg_sizes:
        raise SystemExit("empty segments")

    thresholds = Thresholds(
        rho_min=float(args.rho_min),
        delta_min=float(args.delta_min),
        rho_seg_min=float(args.rho_seg_min),
        delta_seg_min=float(args.delta_seg_min),
    )

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    per_run: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        try:
            rep = _evaluate_one(run_dir, thresholds=thresholds, seg_sizes=seg_sizes)
            per_run.append(rep)
            (out_dir / f"per_run_{run_dir.name}.json").write_text(
                json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception as e:
            failures.append({"run_dir": str(run_dir), "error": str(e)})

    verdict = "PASS" if failures == [] and per_run and all(r["verdict"] == "PASS" for r in per_run) else "FAIL"
    agg = {
        "tool": "calibrate_world_pressure_gate_transfer_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {
            "run_dirs_file": str(Path(args.run_dirs_file).expanduser().resolve()),
            "run_dirs_count": len(run_dirs),
            "thresholds": {
                "rho_min": thresholds.rho_min,
                "delta_min": thresholds.delta_min,
                "rho_seg_min": thresholds.rho_seg_min,
                "delta_seg_min": thresholds.delta_seg_min,
            },
            "segments": seg_sizes,
        },
        "per_run_verdicts": [{"run_dir": r["run_dir"], "verdict": r["verdict"]} for r in per_run],
        "failures": failures,
        "verdict": verdict,
        "notes": "Do-or-die BTC single-world calibration for continuous world-pressure gauge via suppression(t).",
    }
    (out_dir / "aggregate.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

