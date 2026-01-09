#!/usr/bin/env python3
"""
V12 Survival Space (E+M) extended validation summarizer v0 (Research repo, stdlib only).

This tool is post-hoc only. It reads a list of run_ids (or run_dirs) and produces:
  - per-run metrics JSONL (append-only file)
  - aggregate summary JSON (by ablation mode)

Primary metrics (decision-level):
  - block_rate: P(action_allowed == False)
  - downshift_rate: P(post_gate_intensity < interaction_intensity)
  - suppression_ratio: (sum(proposed_intensity) - sum(post_gate_intensity)) / sum(proposed_intensity)

Exit codes:
  0: PASS (summary produced)
  2: FAIL (input list invalid / required files missing / strict-jsonl broken)
  1: ERROR (tool crash / invalid usage)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return obj


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


def _pct(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    xs = sorted(values)
    if q <= 0:
        return float(xs[0])
    if q >= 1:
        return float(xs[-1])
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(xs[lo])
    w = pos - lo
    return float(xs[lo] * (1 - w) + xs[hi] * w)


def _stats(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0}
    n = len(values)
    m = sum(values) / n
    var = 0.0
    for x in values:
        var += (x - m) ** 2
    var /= n if n > 0 else 1
    std = math.sqrt(var)
    return {
        "count": n,
        "min": float(min(values)),
        "mean": float(m),
        "std": float(std),
        "p10": _pct(values, 0.10),
        "p25": _pct(values, 0.25),
        "p50": _pct(values, 0.50),
        "p75": _pct(values, 0.75),
        "p90": _pct(values, 0.90),
        "max": float(max(values)),
    }


@dataclass
class RunMetrics:
    run_id: str
    run_dir: str
    mode: str
    seed: Optional[int]
    steps: Optional[int]
    order_attempts_count: Optional[int]
    okx_api_calls_count: Optional[int]
    errors_count: Optional[int]
    block_rate: Optional[float]
    downshift_rate: Optional[float]
    suppression_ratio: Optional[float]
    proposed_intensity_sum: Optional[float]
    post_gate_intensity_sum: Optional[float]


def _resolve_run_dir(runs_root: Path, item: str) -> Tuple[Path, str]:
    s = item.strip()
    if not s:
        raise ValueError("empty run id in list")
    p = Path(s)
    if p.is_absolute():
        run_dir = p
        run_id = p.name
    else:
        run_id = s
        run_dir = runs_root / s
    return run_dir, run_id


def _compute_decision_gate_metrics(decision_trace_path: Path) -> Tuple[Optional[float], Optional[float], Optional[float], float, float]:
    total = 0
    blocked = 0
    down_total = 0
    down_cnt = 0
    proposed_sum = 0.0
    post_sum = 0.0

    for _ln, rec in _iter_jsonl(decision_trace_path):
        total += 1
        aa = rec.get("action_allowed")
        if aa is False:
            blocked += 1

        it = rec.get("interaction_intensity")
        pt = rec.get("post_gate_intensity")
        if _is_num(it) and _is_num(pt):
            itf = float(it)
            ptf = float(pt)
            proposed_sum += itf
            post_sum += ptf
            down_total += 1
            if ptf < itf:
                down_cnt += 1

    block_rate = (blocked / total) if total > 0 else None
    downshift_rate = (down_cnt / down_total) if down_total > 0 else None
    suppression_ratio = ((proposed_sum - post_sum) / proposed_sum) if proposed_sum > 0 else None
    return block_rate, downshift_rate, suppression_ratio, proposed_sum, post_sum


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_root", default="", help="Runs root (used if list contains run_id only)")
    ap.add_argument("--run_list_file", required=True, help="Text file, one run_id or run_dir per line")
    ap.add_argument("--output_dir", default="", help="Output directory (default: /tmp/...)")
    args = ap.parse_args()

    run_list_path = Path(args.run_list_file).expanduser().resolve()
    if not run_list_path.exists():
        print(f"FAIL: run_list_file not found: {run_list_path}", file=sys.stderr)
        return 2

    runs_root = Path(args.runs_root).expanduser().resolve() if args.runs_root else None
    if runs_root is None:
        # If list contains relative run_id, require runs_root.
        # We will still accept absolute paths without runs_root.
        runs_root = Path(".").resolve()

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path(
        f"/tmp/survival_space_em_extended_summary_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    ).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    per_run_path = out_dir / "per_run_metrics.jsonl"
    summary_path = out_dir / "summary.json"

    per_mode_supp: Dict[str, List[float]] = {}
    per_mode_down: Dict[str, List[float]] = {}
    per_mode_block: Dict[str, List[float]] = {}
    per_mode_attempts: Dict[str, List[float]] = {}

    total = 0
    errors: List[str] = []

    with per_run_path.open("w", encoding="utf-8") as outf:
        for raw in run_list_path.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if not s:
                continue

            run_dir, run_id = _resolve_run_dir(runs_root, s)
            total += 1

            manifest_path = run_dir / "run_manifest.json"
            decision_trace_path = run_dir / "decision_trace.jsonl"

            if not manifest_path.exists():
                errors.append(f"{run_id}: missing run_manifest.json")
                continue
            if not decision_trace_path.exists():
                errors.append(f"{run_id}: missing decision_trace.jsonl")
                continue

            try:
                man = _read_json(manifest_path)
            except Exception as e:
                errors.append(f"{run_id}: run_manifest.json invalid: {e}")
                continue

            mode = (
                (man.get("ablation", {}) or {}).get("survival_space", {}) or {}
            ).get("mode") or "unknown"

            seed = man.get("seed")
            seed_i = int(seed) if isinstance(seed, int) else None
            steps = man.get("steps")
            steps_i = int(steps) if isinstance(steps, int) else None

            ev = man.get("evidence", {}) if isinstance(man.get("evidence", {}), dict) else {}
            oa = ev.get("order_attempts", {}) if isinstance(ev.get("order_attempts", {}), dict) else {}
            api = ev.get("okx_api_calls", {}) if isinstance(ev.get("okx_api_calls", {}), dict) else {}
            err = ev.get("errors", {}) if isinstance(ev.get("errors", {}), dict) else {}

            order_attempts_count = oa.get("count") if isinstance(oa.get("count"), int) else None
            okx_api_calls_count = api.get("count") if isinstance(api.get("count"), int) else None
            errors_count = err.get("count") if isinstance(err.get("count"), int) else None

            try:
                block_rate, downshift_rate, suppression_ratio, proposed_sum, post_sum = _compute_decision_gate_metrics(
                    decision_trace_path
                )
            except Exception as e:
                errors.append(f"{run_id}: decision_trace strict-jsonl failed: {e}")
                continue

            rm = RunMetrics(
                run_id=run_id,
                run_dir=str(run_dir),
                mode=str(mode),
                seed=seed_i,
                steps=steps_i,
                order_attempts_count=order_attempts_count,
                okx_api_calls_count=okx_api_calls_count,
                errors_count=errors_count,
                block_rate=block_rate,
                downshift_rate=downshift_rate,
                suppression_ratio=suppression_ratio,
                proposed_intensity_sum=proposed_sum,
                post_gate_intensity_sum=post_sum,
            )

            outf.write(json.dumps(rm.__dict__, ensure_ascii=False) + "\n")

            if rm.suppression_ratio is not None:
                per_mode_supp.setdefault(rm.mode, []).append(float(rm.suppression_ratio))
            if rm.downshift_rate is not None:
                per_mode_down.setdefault(rm.mode, []).append(float(rm.downshift_rate))
            if rm.block_rate is not None:
                per_mode_block.setdefault(rm.mode, []).append(float(rm.block_rate))
            if rm.order_attempts_count is not None:
                per_mode_attempts.setdefault(rm.mode, []).append(float(rm.order_attempts_count))

    if errors:
        # fail-closed: still produce summary with errors, but exit FAIL
        pass

    by_mode: Dict[str, Any] = {}
    modes = sorted(set(list(per_mode_supp.keys()) + list(per_mode_block.keys()) + list(per_mode_attempts.keys())))
    for m in modes:
        by_mode[m] = {
            "suppression_ratio": _stats(per_mode_supp.get(m, [])),
            "downshift_rate": _stats(per_mode_down.get(m, [])),
            "block_rate": _stats(per_mode_block.get(m, [])),
            "order_attempts_count": _stats(per_mode_attempts.get(m, [])),
        }

    summary = {
        "tool": "summarize_survival_space_em_extended_summary_v0",
        "generated_at_utc": _ts_utc(),
        "runs_root": str(runs_root),
        "run_list_file": str(run_list_path),
        "output_dir": str(out_dir),
        "total_runs_processed": total,
        "per_run_metrics_jsonl": str(per_run_path),
        "by_mode": by_mode,
        "errors": errors,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

    if errors:
        print(f"WARNING: non-empty errors ({len(errors)}). See summary.json", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

