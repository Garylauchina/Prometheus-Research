#!/usr/bin/env python3
"""
V12 World Pressure boundary detector v0 (Research repo, stdlib only).

Changepoint detector (frozen by pre-reg):
  - Greedy binary segmentation on u_t with SSE cost + penalty beta.
  - Enforces min_segment_len and max_changepoints.

Fail-closed:
  - Requires <RUN_DIR>/interaction_impedance.jsonl
  - Requires each record has ts_utc and metrics.world_u (number)
  - Requires N >= 1000

Outputs:
  - per-run JSON report: changepoints, segment stats, R2, checks
  - aggregate JSON report: cross-seed consistency checks

Exit codes:
  - 0: PASS (all runs + cross-seed checks)
  - 2: FAIL (any check fails or evidence invalid)
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


def _mean(xs: List[float]) -> float:
    return sum(xs) / max(1, len(xs))


def _std(xs: List[float]) -> float:
    n = len(xs)
    if n <= 1:
        return 0.0
    m = _mean(xs)
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return math.sqrt(max(0.0, v))


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


def _median(xs: List[float]) -> float:
    return _percentile(xs, 0.5)


def _read_world_u(run_dir: Path) -> Tuple[List[str], List[float]]:
    p = run_dir / "interaction_impedance.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"missing required file: {p}")
    ts: List[str] = []
    u: List[float] = []
    for _ln, rec in _iter_jsonl(p):
        t = rec.get("ts_utc")
        if not isinstance(t, str) or not t:
            raise ValueError(f"missing/invalid ts_utc in {p}")
        metrics = rec.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"missing metrics object in {p} at ts_utc={t}")
        uu = metrics.get("world_u")
        if not _is_num(uu):
            raise ValueError(f"missing/invalid metrics.world_u in {p} at ts_utc={t}")
        ts.append(t)
        u.append(float(uu))
    if len(u) < 1000:
        raise ValueError(f"N < 1000 (fail-closed): N={len(u)}")
    return ts, u


@dataclass
class DetectorParams:
    min_segment_len: int
    max_changepoints: int
    beta: float


def _prefix_sums(u: List[float]) -> Tuple[List[float], List[float]]:
    s1 = [0.0]
    s2 = [0.0]
    for x in u:
        s1.append(s1[-1] + x)
        s2.append(s2[-1] + x * x)
    return s1, s2


def _sse(s1: List[float], s2: List[float], i: int, j: int) -> float:
    n = j - i
    if n <= 0:
        return 0.0
    sum1 = s1[j] - s1[i]
    sum2 = s2[j] - s2[i]
    return max(0.0, sum2 - (sum1 * sum1) / n)


def _best_split(
    s1: List[float], s2: List[float], i: int, j: int, p: DetectorParams
) -> Tuple[Optional[int], float]:
    """
    Returns (k, gain) where gain = SSE(i,j) - (SSE(i,k)+SSE(k,j)+beta).
    If no valid split => (None, 0).
    """
    if j - i < 2 * p.min_segment_len:
        return None, 0.0
    base = _sse(s1, s2, i, j)
    best_gain = 0.0
    best_k = None
    lo = i + p.min_segment_len
    hi = j - p.min_segment_len
    for k in range(lo, hi + 1):
        c = _sse(s1, s2, i, k) + _sse(s1, s2, k, j) + p.beta
        gain = base - c
        if gain > best_gain:
            best_gain = gain
            best_k = k
    return best_k, best_gain


def _binary_segmentation(u: List[float], p: DetectorParams) -> List[int]:
    s1, s2 = _prefix_sums(u)
    segments: List[Tuple[int, int]] = [(0, len(u))]
    cps: List[int] = []
    for _ in range(p.max_changepoints):
        best = (None, 0.0, None)  # (seg_idx, gain, k)
        for idx, (i, j) in enumerate(segments):
            k, gain = _best_split(s1, s2, i, j, p)
            if k is not None and gain > best[1]:
                best = (idx, gain, k)
        seg_idx, gain, k = best
        if seg_idx is None or k is None or gain <= 0.0:
            break
        # split the chosen segment
        i, j = segments[seg_idx]
        left = (i, k)
        right = (k, j)
        segments = segments[:seg_idx] + [left, right] + segments[seg_idx + 1 :]
        cps.append(k)
    return sorted(set(cps))


def _segments_from_cps(n: int, cps: List[int]) -> List[Tuple[int, int]]:
    pts = [0] + [c for c in cps if 0 < c < n] + [n]
    out = []
    for a, b in zip(pts, pts[1:]):
        if a < b:
            out.append((a, b))
    return out


def _segment_stats(u: List[float], segs: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, j in segs:
        xs = u[i:j]
        out.append(
            {
                "i": i,
                "j": j,
                "len": j - i,
                "mean": _mean(xs),
                "std": _std(xs),
                "min": min(xs) if xs else None,
                "max": max(xs) if xs else None,
            }
        )
    return out


def _evaluate_one(run_dir: Path, params: DetectorParams) -> Dict[str, Any]:
    ts, u = _read_world_u(run_dir)
    n = len(u)
    s1, s2 = _prefix_sums(u)
    cps = _binary_segmentation(u, params)
    segs = _segments_from_cps(n, cps)
    sse0 = _sse(s1, s2, 0, n)
    ssek = sum(_sse(s1, s2, i, j) for i, j in segs)
    R2 = 0.0 if sse0 <= 0 else (1.0 - (ssek / sse0))

    stdu = _std(u)
    jumps: List[float] = []
    # adjacent mean jumps
    seg_stats = _segment_stats(u, segs)
    for a, b in zip(seg_stats, seg_stats[1:]):
        jumps.append(abs(float(b["mean"]) - float(a["mean"])))
    med_jump = _median(jumps) if jumps else 0.0

    checks: List[Dict[str, Any]] = []
    checks.append({"name": "cp_count>=1", "pass": len(cps) >= 1, "cp_count": len(cps)})
    checks.append({"name": "R2>=0.05", "pass": R2 >= 0.05, "R2": R2})
    checks.append(
        {
            "name": "median_jump>=0.05*std",
            "pass": (stdu > 0 and med_jump >= 0.05 * stdu),
            "median_jump": med_jump,
            "std_u": stdu,
            "threshold": 0.05 * stdu,
        }
    )
    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    return {
        "tool": "detect_world_pressure_boundaries_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "inputs": {
            "interaction_impedance_jsonl": str(run_dir / "interaction_impedance.jsonl"),
            "N": n,
            "params": {
                "min_segment_len": params.min_segment_len,
                "max_changepoints": params.max_changepoints,
                "beta": params.beta,
            },
        },
        "output": {
            "changepoints": cps,
            "changepoints_normalized": [c / n for c in cps],
            "segments": seg_stats,
            "SSE0": sse0,
            "SSEk": ssek,
            "R2": R2,
            "median_adjacent_mean_jump": med_jump,
            "std_u": stdu,
        },
        "checks": checks,
        "verdict": verdict,
    }


def _std_vals(xs: List[float]) -> float:
    return _std(xs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--min_segment_len", type=int, default=200)
    ap.add_argument("--max_changepoints", type=int, default=10)
    ap.add_argument("--beta", type=float, default=0.5)
    ap.add_argument("--pos_std_max", type=float, default=0.05, help="max std of normalized cp positions across runs")
    args = ap.parse_args()

    run_dirs: List[str] = []
    for ln in Path(args.run_dirs_file).expanduser().read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            run_dirs.append(s)
    if not run_dirs:
        raise SystemExit("empty run_dirs_file")

    params = DetectorParams(
        min_segment_len=int(args.min_segment_len),
        max_changepoints=int(args.max_changepoints),
        beta=float(args.beta),
    )

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    per_run: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        try:
            rep = _evaluate_one(run_dir, params=params)
            per_run.append(rep)
            (out_dir / f"per_run_{run_dir.name}.json").write_text(
                json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except Exception as e:
            failures.append({"run_dir": str(run_dir), "error": str(e)})

    # cross-seed consistency check
    cross_checks: List[Dict[str, Any]] = []
    if failures or not per_run:
        cross_checks.append({"name": "cross_seed_consistency", "pass": False, "reason": "per-run failures"})
        verdict = "FAIL"
    else:
        cp_lists = [r["output"]["changepoints"] for r in per_run]
        counts = [len(cps) for cps in cp_lists]
        K = min(counts) if counts else 0
        if K < 1:
            cross_checks.append({"name": "K>=1", "pass": False, "K": K})
        else:
            N = int(per_run[0]["inputs"]["N"])
            pos_std_max = float(args.pos_std_max)
            ok_all = True
            per_k = []
            for k in range(K):
                ps = [cps[k] / N for cps in cp_lists]
                sd = _std_vals(ps)
                ok = sd <= pos_std_max
                ok_all = ok_all and ok
                per_k.append({"k": k + 1, "positions": ps, "std": sd, "pass": ok})
            cross_checks.append({"name": "cross_seed_position_std", "pass": ok_all, "K": K, "pos_std_max": pos_std_max, "per_k": per_k})

        verdict = "PASS" if all(r["verdict"] == "PASS" for r in per_run) and all(c["pass"] for c in cross_checks) else "FAIL"

    agg = {
        "tool": "detect_world_pressure_boundaries_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {
            "run_dirs_file": str(Path(args.run_dirs_file).expanduser().resolve()),
            "run_dirs_count": len(run_dirs),
            "params": {
                "min_segment_len": params.min_segment_len,
                "max_changepoints": params.max_changepoints,
                "beta": params.beta,
                "pos_std_max": float(args.pos_std_max),
            },
        },
        "per_run_verdicts": [{"run_dir": r["run_dir"], "verdict": r["verdict"]} for r in per_run],
        "cross_checks": cross_checks,
        "failures": failures,
        "verdict": verdict,
        "notes": "Boundary detector do-or-die calibration on world_u via changepoints.",
    }
    (out_dir / "aggregate.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

