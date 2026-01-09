#!/usr/bin/env python3
"""
V12 World Pressure calibration via EDoF-CR v0 (Research repo, stdlib only).

Fail-closed:
  - Requires decision_trace.jsonl and interaction_impedance.jsonl
  - Enforces strict implicit ordering join with line-by-line ts_utc equality
  - Requires numeric world_u and numeric decision fields

Computes:
  - action vector a_t = [interaction_intensity, post_gate_intensity, action_allowed]
  - rolling-window EDoF(t) via correlation-matrix eigenvalues participation ratio
  - EDoF-CR(t) = -(EDoF(t) - EDoF(t-1))
  - association: spearman(u_t, EDoF-CR(t)) and quantile deltas

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
    rx = _rankdata(x)
    ry = _rankdata(y)
    return _pearson(rx, ry)


def _matmul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    n = len(A)
    m = len(B[0])
    k = len(B)
    out = [[0.0 for _ in range(m)] for _ in range(n)]
    for i in range(n):
        for j in range(m):
            s = 0.0
            for t in range(k):
                s += A[i][t] * B[t][j]
            out[i][j] = s
    return out


def _transpose(A: List[List[float]]) -> List[List[float]]:
    return [list(row) for row in zip(*A)]


def _corr_matrix(X: List[List[float]]) -> List[List[float]]:
    """
    X: W x d
    Returns d_eff x d_eff correlation matrix where d_eff excludes zero-variance dimensions.

    Fail-closed notes:
      - Zero-variance dimensions are allowed and are dropped (they would contribute zero eigenvalues).
      - If all dimensions are zero-variance within a window => FAIL (cannot define correlation structure).
    """
    W = len(X)
    if W == 0:
        raise ValueError("empty window")
    d = len(X[0])
    # z-score per dimension
    cols = [[X[i][j] for i in range(W)] for j in range(d)]
    mu = [sum(c) / W for c in cols]
    var = []
    keep: List[int] = []
    for j in range(d):
        v = sum((cols[j][i] - mu[j]) ** 2 for i in range(W)) / max(1, W - 1)
        var.append(v)
        if v > 0:
            keep.append(j)
    if not keep:
        raise ValueError("all dimensions have zero variance in window (fail-closed)")

    Z = [[(X[i][j] - mu[j]) / math.sqrt(var[j]) for j in keep] for i in range(W)]
    # correlation = (Z^T Z)/(W-1)
    Zt = _transpose(Z)
    M = _matmul(Zt, Z)
    denom = max(1, W - 1)
    d2 = len(keep)
    return [[M[i][j] / denom for j in range(d2)] for i in range(d2)]


def _eigvals_sym_3x3(A: List[List[float]]) -> List[float]:
    """
    Eigenvalues of symmetric 3x3 via closed-form (robust enough for correlation matrices).
    Assumes A is symmetric.
    Returns 3 eigenvalues (non-negative for corr matrix, up to numerical drift).
    """
    a11, a12, a13 = A[0][0], A[0][1], A[0][2]
    a22, a23 = A[1][1], A[1][2]
    a33 = A[2][2]

    p1 = a12 * a12 + a13 * a13 + a23 * a23
    if p1 == 0:
        return [a11, a22, a33]

    q = (a11 + a22 + a33) / 3.0
    b11 = a11 - q
    b22 = a22 - q
    b33 = a33 - q
    p2 = b11 * b11 + b22 * b22 + b33 * b33 + 2.0 * p1
    p = math.sqrt(p2 / 6.0)

    # B = (1/p) * (A - qI)
    b12 = a12 / p
    b13 = a13 / p
    b23 = a23 / p
    B11 = b11 / p
    B22 = b22 / p
    B33 = b33 / p

    # det(B)/2
    detB = (
        B11 * (B22 * B33 - b23 * b23)
        - b12 * (b12 * B33 - b23 * b13)
        + b13 * (b12 * b23 - B22 * b13)
    )
    r = detB / 2.0
    # clamp
    if r <= -1:
        phi = math.pi / 3.0
    elif r >= 1:
        phi = 0.0
    else:
        phi = math.acos(r) / 3.0

    eig1 = q + 2.0 * p * math.cos(phi)
    eig3 = q + 2.0 * p * math.cos(phi + (2.0 * math.pi / 3.0))
    eig2 = 3.0 * q - eig1 - eig3
    return [eig1, eig2, eig3]


def _edof_from_corr(R: List[List[float]]) -> float:
    """
    Participation-ratio EDoF from correlation eigenvalues.
    Supports d_eff in {1,2,3}. Fail-closed otherwise.
    """
    d = len(R)
    if d == 1:
        lam2 = [1.0]
    elif d == 2:
        # symmetric 2x2 eigenvalues
        a, b = R[0][0], R[0][1]
        c = R[1][1]
        tr = a + c
        det = a * c - b * b
        disc = max(0.0, tr * tr - 4.0 * det)
        s = math.sqrt(disc)
        lam2 = [max(0.0, (tr + s) / 2.0), max(0.0, (tr - s) / 2.0)]
    elif d == 3:
        lam = _eigvals_sym_3x3(R)
        lam2 = [max(0.0, float(x)) for x in lam]
    else:
        raise ValueError(f"unsupported correlation dimension: {d} (fail-closed)")

    s1 = sum(lam2)
    s2 = sum(x * x for x in lam2)
    if s2 <= 0:
        raise ValueError("invalid eigenvalues (fail-closed)")
    return (s1 * s1) / s2


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


def _read_series(run_dir: Path) -> Tuple[List[str], List[float], List[List[float]]]:
    """
    Returns:
      ts_utc list (length N),
      world_u list (length N),
      action vectors list (length N, each length 3)
    """
    p_dec = run_dir / "decision_trace.jsonl"
    p_imp = run_dir / "interaction_impedance.jsonl"
    if not p_dec.exists():
        raise FileNotFoundError(f"missing required file: {p_dec}")
    if not p_imp.exists():
        raise FileNotFoundError(f"missing required file: {p_imp}")

    dec_ts: List[str] = []
    a: List[List[float]] = []
    for _ln, rec in _iter_jsonl(p_dec):
        ts = rec.get("ts_utc")
        if not isinstance(ts, str) or not ts:
            raise ValueError(f"missing/invalid ts_utc in {p_dec}")
        x1 = rec.get("interaction_intensity")
        x2 = rec.get("post_gate_intensity")
        al = rec.get("action_allowed")
        if not _is_num(x1) or not _is_num(x2) or not isinstance(al, bool):
            raise ValueError(f"missing/invalid decision fields in {p_dec} at ts_utc={ts}")
        dec_ts.append(ts)
        a.append([float(x1), float(x2), 1.0 if al else 0.0])

    imp_ts: List[str] = []
    u: List[float] = []
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
        u.append(float(uu))

    if len(dec_ts) != len(imp_ts):
        raise ValueError(f"record count mismatch (fail-closed): decision={len(dec_ts)} impedance={len(imp_ts)}")
    for i, (t1, t2) in enumerate(zip(dec_ts, imp_ts)):
        if t1 != t2:
            raise ValueError(f"ts_utc mismatch at line {i}: decision={t1} impedance={t2} (fail-closed)")

    return dec_ts, u, a


def _compute_edof_series(a: List[List[float]], W: int) -> List[Optional[float]]:
    n = len(a)
    out: List[Optional[float]] = [None] * n
    for t in range(W - 1, n):
        X = a[t - W + 1 : t + 1]
        R = _corr_matrix(X)
        ed = _edof_from_corr(R)
        out[t] = float(ed)
    return out


def _compute_edof_cr(edof: List[Optional[float]]) -> List[Optional[float]]:
    n = len(edof)
    out: List[Optional[float]] = [None] * n
    prev = None
    for i in range(n):
        cur = edof[i]
        if cur is None or prev is None:
            prev = cur
            continue
        out[i] = -(cur - prev)
        prev = cur
    return out


def _segment_eval(u: List[float], x: List[float], seg: int) -> Dict[str, Any]:
    rhos: List[float] = []
    deltas: List[float] = []
    n = len(u)
    for start in range(0, n, seg):
        end = min(n, start + seg)
        uu = u[start:end]
        xx = x[start:end]
        if len(uu) < 10:
            continue
        rho = _spearman(uu, xx)
        if rho is None or not math.isfinite(rho):
            continue
        qd = _quantile_delta(uu, xx, q=0.10)
        rhos.append(float(rho))
        deltas.append(float(qd["delta"]))
    return {
        "segment_size": seg,
        "segments": len(rhos),
        "rho": _stats(rhos),
        "delta": _stats(deltas),
    }


def _evaluate_one(run_dir: Path, W: int, thresholds: Thresholds, seg_sizes: List[int]) -> Dict[str, Any]:
    ts, u_all, a = _read_series(run_dir)
    edof = _compute_edof_series(a, W=W)
    edof_cr = _compute_edof_cr(edof)

    # filter valid ticks
    u: List[float] = []
    x: List[float] = []
    for uu, xx in zip(u_all, edof_cr):
        if xx is None:
            continue
        u.append(float(uu))
        x.append(float(xx))
    if len(u) < 100:
        raise ValueError("too few valid ticks after windowing (fail-closed)")

    rho = _spearman(u, x)
    if rho is None or not math.isfinite(rho):
        raise ValueError("spearman undefined (fail-closed)")
    qd = _quantile_delta(u, x, q=0.10)

    seg_reports = [_segment_eval(u, x, seg=s) for s in seg_sizes]

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
        "tool": "calibrate_world_pressure_edof_cr_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "inputs": {
            "W": W,
            "records": len(ts),
            "join": "implicit_ordering_with_ts_utc_equality",
            "decision_trace": str(run_dir / "decision_trace.jsonl"),
            "interaction_impedance": str(run_dir / "interaction_impedance.jsonl"),
        },
        "series_stats": {
            "world_u": _stats(u_all),
            "edof": _stats([x for x in edof if x is not None]),
            "edof_cr": _stats(x),
        },
        "eval": {
            "spearman_rho_u_vs_edof_cr": rho,
            "quantile_delta_edof_cr_hi_minus_lo": qd,
            "segment_reports": seg_reports,
        },
        "checks": checks,
        "verdict": verdict,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--W", type=int, default=200)
    ap.add_argument("--rho_min", type=float, default=0.15)
    ap.add_argument("--delta_min", type=float, default=1e-4)
    ap.add_argument("--rho_seg_min", type=float, default=0.10)
    ap.add_argument("--delta_seg_min", type=float, default=1e-4)
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
            rep = _evaluate_one(run_dir, W=int(args.W), thresholds=thresholds, seg_sizes=seg_sizes)
            per_run.append(rep)
            (out_dir / f"per_run_{run_dir.name}.json").write_text(
                json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception as e:
            failures.append({"run_dir": str(run_dir), "error": str(e)})

    verdict = "PASS" if failures == [] and per_run and all(r["verdict"] == "PASS" for r in per_run) else "FAIL"
    agg = {
        "tool": "calibrate_world_pressure_edof_cr_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {
            "run_dirs_file": str(Path(args.run_dirs_file).expanduser().resolve()),
            "run_dirs_count": len(run_dirs),
            "W": int(args.W),
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
        "notes": "Do-or-die BTC single-world calibration for continuous world-pressure readout via EDoF-CR.",
    }
    (out_dir / "aggregate.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

