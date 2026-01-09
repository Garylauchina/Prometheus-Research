#!/usr/bin/env python3
"""
Trial-10: BTC Evidence Re-indexing by Consensus Epochs (world_u boundaries) — Descriptive Audit Only.

Fail-closed:
  - Requires interaction_impedance.jsonl, decision_trace.jsonl, errors.jsonl exist in each run_dir
  - Requires strict implicit ordering and ts_utc equality between impedance and decision_trace
  - Uses only descriptive stats + effect sizes (no predictive models)

Outputs:
  - per_run_epoch_metrics.json
  - between_epoch_effects.json
  - aggregate_verdict.json

stdlib only.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    # sample std
    if len(xs2) <= 1:
        std = 0.0
    else:
        m = mean
        std = math.sqrt(max(0.0, sum((x - m) ** 2 for x in xs2) / (len(xs2) - 1)))
    return {
        "count": len(xs2),
        "min": xs2[0],
        "p50": _percentile(xs2, 0.50),
        "p90": _percentile(xs2, 0.90),
        "p99": _percentile(xs2, 0.99),
        "max": xs2[-1],
        "mean": mean,
        "std": std,
    }


def _read_jsonl_lines(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.strip()
            if not s:
                continue
            obj = json.loads(s)
            if not isinstance(obj, dict):
                raise ValueError(f"invalid JSONL record in {path} line {ln}")
            out.append(obj)
    return out


def _read_world_u(run_dir: Path) -> Tuple[List[str], List[float]]:
    p = run_dir / "interaction_impedance.jsonl"
    recs = _read_jsonl_lines(p)
    ts: List[str] = []
    u: List[float] = []
    for r in recs:
        t = r.get("ts_utc")
        if not isinstance(t, str) or not t:
            raise ValueError(f"missing/invalid ts_utc in {p}")
        m = r.get("metrics")
        if not isinstance(m, dict):
            raise ValueError(f"missing metrics in {p} at ts_utc={t}")
        uu = m.get("world_u")
        if not _is_num(uu):
            raise ValueError(f"missing/invalid metrics.world_u in {p} at ts_utc={t}")
        ts.append(t)
        u.append(float(uu))
    return ts, u


def _read_gate(run_dir: Path) -> Tuple[List[str], List[float], List[float]]:
    p = run_dir / "decision_trace.jsonl"
    recs = _read_jsonl_lines(p)
    ts: List[str] = []
    inter: List[float] = []
    post: List[float] = []
    for r in recs:
        t = r.get("ts_utc")
        if not isinstance(t, str) or not t:
            raise ValueError(f"missing/invalid ts_utc in {p}")
        ii = r.get("interaction_intensity")
        pi = r.get("post_gate_intensity")
        if not _is_num(ii) or not _is_num(pi):
            raise ValueError(f"missing/invalid intensity fields in {p} at ts_utc={t}")
        ts.append(t)
        inter.append(float(ii))
        post.append(float(pi))
    return ts, inter, post


def _read_errors_count_by_ts(run_dir: Path) -> Dict[str, int]:
    p = run_dir / "errors.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"missing required file: {p}")
    out: Dict[str, int] = {}
    with p.open("r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            obj = json.loads(s)
            if not isinstance(obj, dict):
                continue
            t = obj.get("ts_utc")
            if isinstance(t, str) and t:
                out[t] = out.get(t, 0) + 1
    return out


def _segments(boundaries: List[int], N: int) -> List[Tuple[str, int, int]]:
    pts = [0] + [b for b in boundaries if 0 < b < N] + [N]
    out: List[Tuple[str, int, int]] = []
    for idx, (a, b) in enumerate(zip(pts, pts[1:])):
        out.append((f"E{idx}", a, b))
    return out


def _cohen_d(x: List[float], y: List[float]) -> float:
    if not x or not y:
        return float("nan")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    vx = sum((v - mx) ** 2 for v in x) / max(1, len(x) - 1)
    vy = sum((v - my) ** 2 for v in y) / max(1, len(y) - 1)
    sp = math.sqrt(max(0.0, ((len(x) - 1) * vx + (len(y) - 1) * vy) / max(1, len(x) + len(y) - 2)))
    if sp <= 0:
        return 0.0
    return (mx - my) / sp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--boundaries", default="644,3837,5812,6339,6676")
    ap.add_argument("--N", type=int, default=10000)
    # do-or-die thresholds (frozen by pre-reg default values)
    ap.add_argument("--d_world_u_min", type=float, default=0.30)
    ap.add_argument("--d_suppression_min", type=float, default=0.30)
    ap.add_argument("--delta_rate_min", type=float, default=0.05)
    args = ap.parse_args()

    run_dirs: List[str] = []
    for ln in Path(args.run_dirs_file).expanduser().read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            run_dirs.append(s)
    if not run_dirs:
        raise SystemExit("empty run_dirs_file")

    boundaries = [int(x.strip()) for x in args.boundaries.split(",") if x.strip()]
    N = int(args.N)
    segs = _segments(boundaries, N)

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    per_run_epoch_metrics: List[Dict[str, Any]] = []
    # store raw per-epoch samples needed for effect sizes
    samples_by_run: Dict[str, Dict[str, Dict[str, List[float]]]] = {}

    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        # fail-closed file existence
        for fn in ("interaction_impedance.jsonl", "decision_trace.jsonl", "errors.jsonl"):
            if not (run_dir / fn).exists():
                raise SystemExit(f"missing required file: {run_dir/fn}")

        ts_u, u = _read_world_u(run_dir)
        ts_g, inter, post = _read_gate(run_dir)
        if len(u) != N or len(inter) != N or len(post) != N:
            raise SystemExit(f"unexpected record count (fail-closed): run={run_dir} u={len(u)} gate={len(inter)} expected N={N}")
        # ts alignment check
        for i, (a, b) in enumerate(zip(ts_u, ts_g)):
            if a != b:
                raise SystemExit(f"ts_utc mismatch at line {i} in run {run_dir} (fail-closed)")

        err_by_ts = _read_errors_count_by_ts(run_dir)

        run_out = {"run_dir": str(run_dir), "epochs": []}
        samples_by_run[str(run_dir)] = {}

        for name, a, b in segs:
            uu = u[a:b]
            ii = inter[a:b]
            pi = post[a:b]
            attempted = [1.0 if x > 0 else 0.0 for x in ii]
            # suppression only on attempted ticks
            sup: List[float] = []
            block = 0
            downshift = 0
            attempted_cnt = 0
            for x, y in zip(ii, pi):
                if x > 0:
                    attempted_cnt += 1
                    s = 1.0 - (y / x)
                    s = min(1.0, max(0.0, s))
                    sup.append(s)
                    if y == 0:
                        block += 1
                    elif 0 < y < x:
                        downshift += 1

            # error density by ts_utc within [a,b)
            err_cnt = 0
            for t in ts_u[a:b]:
                err_cnt += err_by_ts.get(t, 0)

            epoch = {
                "epoch": name,
                "i": a,
                "j": b,
                "len": b - a,
                "world_u": _stats(uu),
                "gate": {
                    "attempted_rate": attempted_cnt / max(1, (b - a)),
                    "block_rate": block / max(1, attempted_cnt),
                    "downshift_rate": downshift / max(1, attempted_cnt),
                    "suppression": _stats(sup),
                },
                "fail_closed": {"errors_count": err_cnt, "errors_per_1k_ticks": 1000.0 * err_cnt / max(1, (b - a))},
            }
            run_out["epochs"].append(epoch)

            # store samples for effect sizes
            samples_by_run[str(run_dir)][name] = {
                "world_u": uu,
                "suppression": sup,
                "block": [1.0] * block + [0.0] * (attempted_cnt - block),
                "downshift": [1.0] * downshift + [0.0] * (attempted_cnt - downshift),
                "attempted": attempted,  # per tick
            }

        per_run_epoch_metrics.append(run_out)

    (out_dir / "per_run_epoch_metrics.json").write_text(
        json.dumps(per_run_epoch_metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Between-epoch effects (per run)
    epoch_names = [s[0] for s in segs]
    pairs = [(a, b) for a, b in itertools.combinations(epoch_names, 2)]
    effects: List[Dict[str, Any]] = []
    distinguishable_pairs: List[Dict[str, Any]] = []

    for e1, e2 in pairs:
        per_seed = []
        for rd in run_dirs:
            run_dir = str(Path(rd).expanduser().resolve())
            s1 = samples_by_run[run_dir][e1]
            s2 = samples_by_run[run_dir][e2]
            d_u = _cohen_d(s1["world_u"], s2["world_u"])
            d_sup = _cohen_d(s1["suppression"], s2["suppression"])
            # rate diffs
            block_rate_1 = sum(s1["block"]) / max(1, len(s1["block"]))
            block_rate_2 = sum(s2["block"]) / max(1, len(s2["block"]))
            down_rate_1 = sum(s1["downshift"]) / max(1, len(s1["downshift"]))
            down_rate_2 = sum(s2["downshift"]) / max(1, len(s2["downshift"]))
            att_rate_1 = sum(s1["attempted"]) / max(1, len(s1["attempted"]))
            att_rate_2 = sum(s2["attempted"]) / max(1, len(s2["attempted"]))
            per_seed.append(
                {
                    "run_dir": run_dir,
                    "d_world_u": d_u,
                    "d_suppression": d_sup,
                    "delta_block_rate": block_rate_1 - block_rate_2,
                    "delta_downshift_rate": down_rate_1 - down_rate_2,
                    "delta_attempted_rate": att_rate_1 - att_rate_2,
                }
            )
        # min across seeds of abs effects
        min_abs_d_u = min(abs(x["d_world_u"]) for x in per_seed)
        min_abs_d_sup = min(abs(x["d_suppression"]) for x in per_seed)
        min_abs_db = min(abs(x["delta_block_rate"]) for x in per_seed)
        min_abs_dd = min(abs(x["delta_downshift_rate"]) for x in per_seed)
        min_abs_da = min(abs(x["delta_attempted_rate"]) for x in per_seed)

        entry = {
            "pair": [e1, e2],
            "per_seed": per_seed,
            "min_abs": {
                "d_world_u": min_abs_d_u,
                "d_suppression": min_abs_d_sup,
                "delta_block_rate": min_abs_db,
                "delta_downshift_rate": min_abs_dd,
                "delta_attempted_rate": min_abs_da,
            },
        }
        effects.append(entry)

        # distinguishable pair rule (frozen)
        if min_abs_d_u >= float(args.d_world_u_min) and (
            min_abs_db >= float(args.delta_rate_min)
            or min_abs_dd >= float(args.delta_rate_min)
            or min_abs_d_sup >= float(args.d_suppression_min)
        ):
            distinguishable_pairs.append(entry)

    (out_dir / "between_epoch_effects.json").write_text(json.dumps(effects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # also write a compact ranking for quick audit
    ranked = sorted(
        effects,
        key=lambda e: (
            max(
                float(e["min_abs"]["d_world_u"]),
                float(e["min_abs"]["d_suppression"]),
                float(e["min_abs"]["delta_block_rate"]),
                float(e["min_abs"]["delta_downshift_rate"]),
            )
        ),
        reverse=True,
    )
    top = []
    for e in ranked[:50]:
        top.append({"pair": e["pair"], "min_abs": e["min_abs"]})
    (out_dir / "between_epoch_effects_top50.json").write_text(
        json.dumps(top, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Verdict
    involved = set()
    for e in distinguishable_pairs:
        involved.add(e["pair"][0])
        involved.add(e["pair"][1])
    verdict = "PASS" if (len(distinguishable_pairs) >= 2 and len(involved) >= 3) else "FAIL"

    agg = {
        "tool": "reindex_btc_evidence_by_consensus_epochs_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {
            "run_dirs_count": len(run_dirs),
            "N": N,
            "boundaries": boundaries,
            "thresholds": {
                "d_world_u_min": float(args.d_world_u_min),
                "d_suppression_min": float(args.d_suppression_min),
                "delta_rate_min": float(args.delta_rate_min),
            },
        },
        "distinguishable_pairs_count": len(distinguishable_pairs),
        "distinguishable_pairs": [{"pair": x["pair"], "min_abs": x["min_abs"]} for x in distinguishable_pairs[:50]],
        "epochs_involved": sorted(involved),
        "verdict": verdict,
        "notes": "Descriptive audit only. No prediction. No mechanism change.",
    }
    (out_dir / "aggregate_verdict.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(agg, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

