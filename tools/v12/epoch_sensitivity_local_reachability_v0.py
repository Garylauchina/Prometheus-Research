#!/usr/bin/env python3
"""
V12 Local Reachability — Epoch sensitivity test v0 (Research repo, stdlib only).

Purpose (post-hoc, fail-closed input handling):
  - For a single run_dir, compute non-overlapping window means of feasible_ratio for multiple window sizes.
  - Compare the window-mean series across window sizes via Spearman rank correlation after time-alignment.

This tool does NOT decide PASS/FAIL; pre-reg defines thresholds.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
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
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path} line {line_no}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be an object at {path} line {line_no}")
            yield line_no, obj


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _rankdata(xs: List[float]) -> List[float]:
    # average ranks for ties, 1..n
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        # average rank in [i..j]
        avg = (i + 1 + j + 1) / 2.0
        for t in range(i, j + 1):
            ranks[order[t]] = avg
        i = j + 1
    return ranks


def _pearson(x: List[float], y: List[float]) -> float:
    if len(x) != len(y) or not x:
        return float("nan")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = 0.0
    dx = 0.0
    dy = 0.0
    for a, b in zip(x, y):
        xa = a - mx
        yb = b - my
        num += xa * yb
        dx += xa * xa
        dy += yb * yb
    if dx <= 0 or dy <= 0:
        return float("nan")
    return num / math.sqrt(dx * dy)


def _spearman(x: List[float], y: List[float]) -> float:
    if len(x) != len(y) or not x:
        return float("nan")
    rx = _rankdata(x)
    ry = _rankdata(y)
    return _pearson(rx, ry)


def _window_means(series: List[float], k: int) -> List[float]:
    if k <= 0:
        raise ValueError("k must be > 0")
    out: List[float] = []
    n = len(series)
    m = n // k
    for i in range(m):
        chunk = series[i * k : (i + 1) * k]
        out.append(sum(chunk) / len(chunk))
    return out


def _align_small_to_big(small_means: List[float], k_small: int, k_big: int) -> List[float]:
    # k_small must divide k_big
    if k_big % k_small != 0:
        raise ValueError("k_big must be multiple of k_small for alignment")
    factor = k_big // k_small
    big_len = len(small_means) // factor
    out: List[float] = []
    for i in range(big_len):
        block = small_means[i * factor : (i + 1) * factor]
        out.append(sum(block) / len(block))
    return out


def _load_feasible_ratio(run_dir: Path) -> List[float]:
    p = run_dir / "local_reachability.jsonl"
    if not p.exists():
        raise FileNotFoundError(f"missing: {p}")
    out: List[float] = []
    for _ln, rec in _iter_jsonl(p):
        nb = rec.get("neighborhood")
        if not isinstance(nb, dict):
            continue
        x = nb.get("feasible_ratio")
        if _is_num(x):
            out.append(float(x))
    if not out:
        raise ValueError("no feasible_ratio values found")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--k_list", default="100,500,1000,5000")
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--output_md", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        print(f"FAIL: run_dir not found: {run_dir}", file=sys.stderr)
        return 2

    try:
        ks = [int(s.strip()) for s in str(args.k_list).split(",") if s.strip()]
        ks = sorted(set(k for k in ks if k > 0))
        if len(ks) < 2:
            raise ValueError("k_list must include at least 2 positive integers")
    except Exception as e:
        print(f"FAIL: invalid k_list: {e}", file=sys.stderr)
        return 2

    try:
        fr = _load_feasible_ratio(run_dir)
    except Exception as e:
        print(f"FAIL: load feasible_ratio: {e}", file=sys.stderr)
        return 2

    n = len(fr)
    per_k: Dict[int, Dict[str, Any]] = {}
    means_by_k: Dict[int, List[float]] = {}
    for k in ks:
        m = _window_means(fr, k)
        means_by_k[k] = m
        per_k[k] = {"k": k, "window_count": len(m)}

    # pairwise comparisons after aligning to larger-k windows when possible
    comparisons: List[Dict[str, Any]] = []
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            k1 = ks[i]
            k2 = ks[j]
            small_k, big_k = (k1, k2)
            small = means_by_k[small_k]
            big = means_by_k[big_k]

            aligned_small = None
            aligned_big = None
            rho = float("nan")
            method = "unaligned"

            if big_k % small_k == 0:
                aligned_small = _align_small_to_big(small, small_k, big_k)
                L = min(len(aligned_small), len(big))
                aligned_small = aligned_small[:L]
                aligned_big = big[:L]
                rho = _spearman(aligned_small, aligned_big)
                method = "aligned_by_time"

            comparisons.append(
                {
                    "k_small": small_k,
                    "k_big": big_k,
                    "method": method,
                    "spearman_rho": rho,
                    "aligned_length": None if aligned_small is None else len(aligned_small),
                }
            )

    report = {
        "tool": "epoch_sensitivity_local_reachability_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "records": n,
        "k_list": ks,
        "per_k": [per_k[k] for k in ks],
        "comparisons": comparisons,
        "notes": "This tool is descriptive; pre-reg defines falsification thresholds for epoch sensitivity.",
    }

    out_json = Path(args.output_json).expanduser().resolve()
    out_md = Path(args.output_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md: List[str] = []
    md.append("# Local Reachability — Epoch Sensitivity Report v0\n\n")
    md.append(f"- generated_at_utc: {report['generated_at_utc']}\n")
    md.append(f"- run_dir: `{report['run_dir']}`\n")
    md.append(f"- records: {n}\n")
    md.append(f"- k_list: {ks}\n\n")
    md.append("## Pairwise Spearman correlations (time-aligned when possible)\n\n")
    for c in comparisons:
        md.append(f"- k_small={c['k_small']} k_big={c['k_big']} method={c['method']} spearman_rho={c['spearman_rho']}\n")
    out_md.write_text("".join(md), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

