#!/usr/bin/env python3
"""
V12 Trial-9: Build epoch candidates from Trial-8 changepoints (annotation-only).

Fail-closed:
  - Requires Trial-8 per-run JSON reports (with changepoints and N)
  - Requires corresponding Quant run_dir interaction_impedance.jsonl for per-epoch descriptive stats
  - Requires N>=1000

Outputs (JSON):
  - epoch_candidates.json (consensus + per-run boundaries + audits)
  - per_run_epoch_stats.json (per-run epochs and per-epoch u stats)
  - consensus_epoch_stats_by_run.json (apply consensus boundaries to each run; stats)

No external deps (stdlib only).
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _read_json(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path} must be a JSON object")
    return obj


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


def _mean(xs: List[float]) -> float:
    return sum(xs) / max(1, len(xs))


def _std(xs: List[float]) -> float:
    n = len(xs)
    if n <= 1:
        return 0.0
    m = _mean(xs)
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return math.sqrt(max(0.0, v))


def _read_world_u_from_run_dir(run_dir: Path) -> List[float]:
    p = run_dir / "interaction_impedance.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"missing required file: {p}")
    u: List[float] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            rec = json.loads(s)
            if not isinstance(rec, dict):
                raise ValueError(f"invalid JSONL record in {p}")
            metrics = rec.get("metrics")
            if not isinstance(metrics, dict):
                raise ValueError(f"missing metrics in {p}")
            uu = metrics.get("world_u")
            if not _is_num(uu):
                raise ValueError(f"missing/invalid metrics.world_u in {p}")
            u.append(float(uu))
    if len(u) < 1000:
        raise ValueError(f"N < 1000 (fail-closed): N={len(u)}")
    return u


def _segments_from_boundaries(n: int, boundaries: List[int]) -> List[Tuple[int, int]]:
    pts = [0] + [b for b in boundaries if 0 < b < n] + [n]
    out: List[Tuple[int, int]] = []
    for a, b in zip(pts, pts[1:]):
        if a < b:
            out.append((a, b))
    return out


def _epoch_stats(u: List[float], segs: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trial8_artifacts_dir", required=True)
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--min_epoch_len", type=int, default=200)
    ap.add_argument("--pos_std_max", type=float, default=0.05)
    args = ap.parse_args()

    trial8_dir = Path(args.trial8_artifacts_dir).expanduser().resolve()
    if not trial8_dir.exists():
        raise SystemExit(f"trial8_artifacts_dir not found: {trial8_dir}")

    run_dirs: List[str] = []
    for ln in Path(args.run_dirs_file).expanduser().read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            run_dirs.append(s)
    if not run_dirs:
        raise SystemExit("empty run_dirs_file")

    # Load Trial-8 per-run reports by matching run_dir name
    per_run_reports: List[Dict[str, Any]] = []
    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        name = run_dir.name
        p = trial8_dir / f"per_run_{name}.json"
        if not p.exists():
            raise SystemExit(f"missing trial8 per_run report: {p}")
        rep = _read_json(p)
        per_run_reports.append(rep)

    Ns = [int(r["inputs"]["N"]) for r in per_run_reports]
    if len(set(Ns)) != 1:
        raise SystemExit(f"inconsistent N across runs: {Ns}")
    N = Ns[0]
    cps_by_run = [list(map(int, r["output"]["changepoints"])) for r in per_run_reports]
    counts = [len(cps) for cps in cps_by_run]
    K = min(counts) if counts else 0

    # consensus boundaries
    consensus_boundaries: List[int] = []
    per_k_audit: List[Dict[str, Any]] = []
    if K >= 1:
        for k in range(K):
            ps = [cps[k] / N for cps in cps_by_run]
            p_star = _median(ps)
            t_star = int(round(p_star * N))
            consensus_boundaries.append(t_star)
            per_k_audit.append(
                {
                    "k": k + 1,
                    "positions": ps,
                    "median_position": p_star,
                    "std_position": _std(ps),
                    "consensus_boundary": t_star,
                    "pass": _std(ps) <= float(args.pos_std_max),
                    "deviations_ticks": [int(cps[k]) - t_star for cps in cps_by_run],
                }
            )

    # validate min epoch len on consensus
    consensus_segs = _segments_from_boundaries(N, consensus_boundaries)
    min_len_ok = all((j - i) >= int(args.min_epoch_len) for i, j in consensus_segs)

    # compute per-epoch stats
    per_run_epoch_stats: List[Dict[str, Any]] = []
    consensus_epoch_stats_by_run: List[Dict[str, Any]] = []
    for rd, cps in zip(run_dirs, cps_by_run):
        run_dir = Path(rd).expanduser().resolve()
        u = _read_world_u_from_run_dir(run_dir)
        segs_run = _segments_from_boundaries(N, cps)
        per_run_epoch_stats.append(
            {"run_dir": str(run_dir), "boundaries": cps, "epochs": _epoch_stats(u, segs_run)}
        )
        consensus_epoch_stats_by_run.append(
            {
                "run_dir": str(run_dir),
                "consensus_boundaries": consensus_boundaries,
                "epochs": _epoch_stats(u, consensus_segs),
            }
        )

    # verdict
    pass_pos = (K >= 1) and all(x["pass"] for x in per_k_audit)
    verdict = "PASS" if (pass_pos and min_len_ok) else "FAIL"

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    epoch_candidates = {
        "tool": "build_epoch_candidates_from_changepoints_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {
            "trial8_artifacts_dir": str(trial8_dir),
            "run_dirs_file": str(Path(args.run_dirs_file).expanduser().resolve()),
            "run_dirs_count": len(run_dirs),
            "N": N,
            "min_epoch_len": int(args.min_epoch_len),
            "pos_std_max": float(args.pos_std_max),
        },
        "per_run": [{"run_dir": rd, "changepoints": cps, "cp_count": len(cps)} for rd, cps in zip(run_dirs, cps_by_run)],
        "consensus": {
            "K": K,
            "boundaries": consensus_boundaries,
            "segments": [{"i": i, "j": j, "len": j - i} for i, j in consensus_segs],
            "min_epoch_len_ok": min_len_ok,
            "audit_per_k": per_k_audit,
        },
        "verdict": verdict,
        "notes": "Annotation-only. No downstream mechanism changes.",
    }
    (out_dir / "epoch_candidates.json").write_text(json.dumps(epoch_candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "per_run_epoch_stats.json").write_text(json.dumps(per_run_epoch_stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "consensus_epoch_stats_by_run.json").write_text(
        json.dumps(consensus_epoch_stats_by_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(epoch_candidates, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

