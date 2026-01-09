#!/usr/bin/env python3
"""
Survival Space Poset Round-1 — Incomparability Saturation Test v0 (Research repo, stdlib only).

Reads per-run metrics JSONL and estimates:
  - incomparability_rate among random pairs under componentwise dominance
  - stability vs sample size curve

Exit codes:
  0: PASS (report produced; verdict in JSON)
  2: FAIL (inputs missing/invalid)
  1: ERROR (tool crash)
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
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
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path} line {line_no}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be an object at {path} line {line_no}")
            yield line_no, obj


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[Optional[float], Optional[float]]:
    if n <= 0:
        return None, None
    phat = k / n
    denom = 1.0 + (z * z) / n
    center = (phat + (z * z) / (2 * n)) / denom
    half = (z / denom) * math.sqrt((phat * (1 - phat) / n) + (z * z) / (4 * n * n))
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return float(lo), float(hi)


@dataclass(frozen=True)
class Point:
    run_id: str
    mode: str
    x1: float  # suppression_ratio
    x2: float  # block_rate


def _dominates(a: Point, b: Point) -> bool:
    # lower = easier; direction frozen higher=harder
    return (a.x1 <= b.x1) and (a.x2 <= b.x2)


def _load_points(per_run_metrics_jsonl: Path, allowed_modes: List[str]) -> List[Point]:
    out: List[Point] = []
    for _ln, rec in _iter_jsonl(per_run_metrics_jsonl):
        mode = rec.get("mode")
        if allowed_modes and mode not in allowed_modes:
            continue
        rid = rec.get("run_id") or rec.get("run_dir") or "unknown"
        x1 = rec.get("suppression_ratio")
        x2 = rec.get("block_rate")
        if not (_is_num(x1) and _is_num(x2)):
            continue
        out.append(Point(run_id=str(rid), mode=str(mode), x1=float(x1), x2=float(x2)))
    return out


def _sample_incomparability(rng: random.Random, pts: List[Point], pair_samples: int) -> Dict[str, Any]:
    if len(pts) < 2:
        return {"pair_samples": pair_samples, "incomparability_rate": None, "comparable_rate": None, "n_points": len(pts)}

    inc = 0
    comp = 0
    for _ in range(pair_samples):
        a = pts[rng.randrange(0, len(pts))]
        b = pts[rng.randrange(0, len(pts))]
        if a.run_id == b.run_id:
            # allow self-pairing; it's comparable, but doesn't add info; keep it simple
            comp += 1
            continue
        ab = _dominates(a, b)
        ba = _dominates(b, a)
        if ab or ba:
            comp += 1
        else:
            inc += 1

    n = inc + comp
    ir = inc / n if n > 0 else None
    cr = comp / n if n > 0 else None
    lo, hi = _wilson_ci(inc, n)
    return {
        "pair_samples": pair_samples,
        "n_points": len(pts),
        "incomparability_count": inc,
        "comparable_count": comp,
        "incomparability_rate": ir,
        "incomparability_rate_ci95": [lo, hi],
        "comparable_rate": cr,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_run_metrics_jsonl", required=True, help="per_run_metrics.jsonl path (Research artifact)")
    ap.add_argument("--modes", default="full,no_e", help="Comma-separated modes to include (default: full,no_e)")
    ap.add_argument("--seed", type=int, default=20260109, help="RNG seed for sampling (default frozen)")
    ap.add_argument("--pair_samples", type=int, default=50000, help="Pair samples per curve point")
    ap.add_argument("--curve_sizes", default="200,400,800,1600,3200", help="Comma-separated sample sizes for stability curve")
    ap.add_argument("--threshold", type=float, default=0.80, help="Incomparability saturation threshold (default 0.80)")
    ap.add_argument("--output_json", required=True, help="Output JSON report path")
    ap.add_argument("--output_md", required=True, help="Output Markdown report path")
    args = ap.parse_args()

    src = Path(args.per_run_metrics_jsonl).expanduser().resolve()
    if not src.exists():
        print(f"FAIL: per_run_metrics_jsonl not found: {src}", file=sys.stderr)
        return 2

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    try:
        pts_all = _load_points(src, modes)
    except Exception as e:
        print(f"FAIL: load points: {e}", file=sys.stderr)
        return 2

    if len(pts_all) < 2:
        report = {
            "tool": "poset_incomparability_test_v0",
            "generated_at_utc": _ts_utc(),
            "verdict": "NOT_MEASURABLE",
            "reason": "insufficient_points",
            "per_run_metrics_jsonl": str(src),
            "modes": modes,
            "points_count": len(pts_all),
            "dimension_set": {"x1": "suppression_ratio", "x2": "block_rate", "direction": "higher=harder"},
        }
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        Path(args.output_md).write_text("# NOT_MEASURABLE: insufficient points\n", encoding="utf-8")
        return 0

    rng = random.Random(int(args.seed))
    sizes: List[int] = []
    for part in args.curve_sizes.split(","):
        part = part.strip()
        if not part:
            continue
        sizes.append(int(part))
    sizes = sorted(set([s for s in sizes if s > 1]))
    if not sizes:
        print("FAIL: curve_sizes empty", file=sys.stderr)
        return 2

    curve: List[Dict[str, Any]] = []
    for n in sizes:
        # sample without replacement when possible, else with replacement fallback
        if n <= len(pts_all):
            pts = rng.sample(pts_all, n)
        else:
            pts = [pts_all[rng.randrange(0, len(pts_all))] for _ in range(n)]
        curve.append({"sample_size": n, **_sample_incomparability(rng, pts, int(args.pair_samples))})

    # Verdict logic: saturation if all large points >= threshold (conservative)
    # Use the last 2 points as "large enough" in v0.
    tail = curve[-2:] if len(curve) >= 2 else curve[-1:]
    sat = True
    for pt in tail:
        ir = pt.get("incomparability_rate")
        if ir is None or float(ir) < float(args.threshold):
            sat = False
            break
    verdict = "FAIL" if sat else "PASS"

    report = {
        "tool": "poset_incomparability_test_v0",
        "generated_at_utc": _ts_utc(),
        "per_run_metrics_jsonl": str(src),
        "modes": modes,
        "dimension_set": {
            "x1": "suppression_ratio",
            "x2": "block_rate",
            "direction": "higher=harder",
            "order": "componentwise_dominance",
        },
        "threshold": float(args.threshold),
        "pair_samples_per_point": int(args.pair_samples),
        "curve": curve,
        "verdict": verdict,
        "interpretation": (
            "FAIL means incomparability saturation likely holds (poset operationally uninformative) "
            "under this dimension set; PASS means not saturated (may consider Round-2 only if needed)."
        ),
    }

    out_json = Path(args.output_json).expanduser().resolve()
    out_md = Path(args.output_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Minimal markdown
    lines = []
    lines.append("# Survival Space Poset Round-1 — Incomparability Saturation Test v0\n")
    lines.append(f"- generated_at_utc: {report['generated_at_utc']}\n")
    lines.append(f"- modes: {', '.join(modes)}\n")
    lines.append(f"- dimensions: (suppression_ratio, block_rate), higher=harder\n")
    lines.append(f"- threshold: {report['threshold']}\n")
    lines.append(f"- verdict: **{verdict}**\n\n")
    lines.append("## Curve (sample_size → incomparability_rate)\n\n")
    for pt in curve:
        ir = pt.get("incomparability_rate")
        ci = pt.get("incomparability_rate_ci95")
        lines.append(f"- n={pt['sample_size']}: ir={ir} ci95={ci}\n")
    out_md.write_text("".join(lines), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

