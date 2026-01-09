#!/usr/bin/env python3
"""
V12 Local Reachability multi-run summary (grouped) v0 (Research repo, stdlib only).

Groups runs by:
  - run_manifest.json: ablation.survival_space.mode (full/no_e/no_m/null)

Produces descriptive-only stats:
  - per-run feasible_ratio stats
  - aggregate distribution of per-run mean feasible_ratio per group

No thresholds, no verdict.
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


def _read_json(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path} must be a JSON object")
    return obj


def _get_mode(run_manifest: Dict[str, Any]) -> str:
    ab = run_manifest.get("ablation")
    if isinstance(ab, dict):
        ss = ab.get("survival_space")
        if isinstance(ss, dict):
            mode = ss.get("mode")
            if isinstance(mode, str) and mode:
                return mode
    return "unknown"


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


def _parse_run_dirs_file(path: Path) -> List[str]:
    out: List[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dirs_file", required=True)
    ap.add_argument("--output_json", required=True)
    args = ap.parse_args()

    run_dirs = _parse_run_dirs_file(Path(args.run_dirs_file).expanduser().resolve())
    if not run_dirs:
        raise SystemExit("empty run_dirs_file")

    per_run: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    group_means: Dict[str, List[float]] = {}

    for rd in run_dirs:
        run_dir = Path(rd).expanduser().resolve()
        try:
            manifest = _read_json(run_dir / "run_manifest.json")
            mode = _get_mode(manifest)
            fr = _read_run_feasible_ratios(run_dir)
            st = _stats(fr)
            per_run.append(
                {
                    "run_dir": str(run_dir),
                    "mode": mode,
                    "dataset_dir": manifest.get("dataset_dir"),
                    "probe_attempts_per_tick": manifest.get("params", {}).get("probe_attempts_per_tick", None),
                    "local_reachability_jsonl": str(run_dir / "local_reachability.jsonl"),
                    "feasible_ratio": st,
                }
            )
            if st.get("count", 0) > 0 and _is_num(st.get("mean")):
                group_means.setdefault(mode, []).append(float(st["mean"]))
        except Exception as e:
            failures.append({"run_dir": str(run_dir), "error": str(e)})

    grouped = {mode: _stats(means) for mode, means in sorted(group_means.items(), key=lambda x: x[0])}

    report = {
        "tool": "summarize_local_reachability_multi_run_grouped_v0",
        "generated_at_utc": _ts_utc(),
        "inputs": {"run_dirs_count": len(run_dirs), "run_dirs_file": str(Path(args.run_dirs_file).expanduser().resolve())},
        "grouped_per_run_mean_feasible_ratio": grouped,
        "per_run": per_run,
        "failures": failures,
        "notes": "Descriptive only. No thresholds, no verdict.",
    }

    out = Path(args.output_json).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

