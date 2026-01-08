#!/usr/bin/env python3
"""
Summarize Survival Space (E+M) structural signals v0 (Research repo, stdlib only).

This tool is post-hoc analysis only (no runtime feedback). It reads a run_dir and produces
`report.json` capturing the 4 structural signals defined by the architecture checklist:
  1) Gate trigger rate
  2) Exhaustion attribution diversity (first_exhaust_dim)
  3) Action–dissipation coupling (intensity vs dL_imp/dt correlation)
  4) Nonlinear collapse signature (stage-wise shrink near L→0)

Exit codes:
  0: PASS (report produced)
  2: FAIL (strict JSONL broken / missing inputs)
  1: ERROR (tool crash / invalid usage)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
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


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _safe_get(d: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in d:
            return d.get(k)
    return None


def _pearsonr(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = 0.0
    dx = 0.0
    dy = 0.0
    for x, y in zip(xs, ys):
        ax = x - mx
        ay = y - my
        num += ax * ay
        dx += ax * ax
        dy += ay * ay
    if dx <= 0 or dy <= 0:
        return None
    return float(num / math.sqrt(dx * dy))


def summarize(run_dir: Path, l_epsilon: float, bins: List[Tuple[float, float]]) -> Dict[str, Any]:
    required = [
        "run_manifest.json",
        "survival_space.jsonl",
        "decision_trace.jsonl",
        "order_attempts.jsonl",
    ]
    missing = [x for x in required if not (run_dir / x).exists()]
    if missing:
        raise ValueError(f"missing required file(s): {missing}")

    manifest = _read_json(run_dir / "run_manifest.json")
    ab = manifest.get("ablation", {})
    ss_ab = ab.get("survival_space", {}) if isinstance(ab, dict) else {}
    ab_enabled = bool(ss_ab.get("enabled")) if isinstance(ss_ab, dict) else False
    ab_mode = ss_ab.get("mode") if isinstance(ss_ab, dict) else None

    # --- Gate trigger rate (prefer order_attempts; fall back to decision_trace)
    gate_total = 0
    gate_blocked = 0
    gate_reason_counts: Dict[str, int] = {}

    def _consume_gate(rec: Dict[str, Any]) -> None:
        nonlocal gate_total, gate_blocked
        aa = rec.get("action_allowed")
        grc = rec.get("gate_reason_codes")
        if not isinstance(aa, bool):
            return
        if grc is not None and not _is_list_of_str(grc):
            return
        gate_total += 1
        if aa is False:
            gate_blocked += 1
        if isinstance(grc, list):
            for c in grc:
                gate_reason_counts[c] = gate_reason_counts.get(c, 0) + 1

    # Try order_attempts first (closer to actual attempts)
    try:
        for _ln, rec in _iter_jsonl(run_dir / "order_attempts.jsonl"):
            _consume_gate(rec)
    except Exception:
        # strict-jsonl issues should be caught by verifier; for report we still fail
        raise

    if gate_total == 0:
        # fallback to decision_trace if attempts don't carry gate fields
        for _ln, rec in _iter_jsonl(run_dir / "decision_trace.jsonl"):
            _consume_gate(rec)

    gate_rate = (gate_blocked / gate_total) if gate_total > 0 else None

    # --- Read survival_space series (for exhaustion + collapse + dL_imp/dt)
    # We join by index/order (tick alignment is assumed by strict per-tick write requirement).
    L_series: List[Optional[float]] = []
    Lm_series: List[int] = []
    Lliq_series: List[Optional[float]] = []
    Lliq_m_series: List[int] = []
    Limp_series: List[Optional[float]] = []
    Limp_m_series: List[int] = []

    for _ln, rec in _iter_jsonl(run_dir / "survival_space.jsonl"):
        L_series.append(float(rec["L"]) if rec.get("L_mask") == 1 and _is_num(rec.get("L")) else None)
        Lm_series.append(int(rec.get("L_mask", 0)) if rec.get("L_mask") in (0, 1) else 0)
        Lliq_series.append(float(rec["L_liq"]) if rec.get("L_liq_mask") == 1 and _is_num(rec.get("L_liq")) else None)
        Lliq_m_series.append(int(rec.get("L_liq_mask", 0)) if rec.get("L_liq_mask") in (0, 1) else 0)
        Limp_series.append(float(rec["L_imp"]) if rec.get("L_imp_mask") == 1 and _is_num(rec.get("L_imp")) else None)
        Limp_m_series.append(int(rec.get("L_imp_mask", 0)) if rec.get("L_imp_mask") in (0, 1) else 0)

    n = len(L_series)

    # --- Exhaustion attribution: first tick where L <= epsilon (measurable)
    first_exhaust = {"tick_idx": None, "first_exhaust_dim": None, "L_at_exhaust": None}
    for i in range(n):
        if Lm_series[i] != 1 or L_series[i] is None:
            continue
        if float(L_series[i]) <= l_epsilon:
            dim = None
            # choose the min contributor if both measurable; else unknown
            if Lliq_m_series[i] == 1 and Limp_m_series[i] == 1 and Lliq_series[i] is not None and Limp_series[i] is not None:
                dim = "liq" if float(Lliq_series[i]) <= float(Limp_series[i]) else "imp"
            first_exhaust = {"tick_idx": i, "first_exhaust_dim": dim, "L_at_exhaust": float(L_series[i])}
            break

    # --- Action–dissipation coupling: intensity vs dL_imp/dt
    # Extract per-tick intensity from decision_trace, best-effort.
    intensities: List[Optional[float]] = []
    for _ln, rec in _iter_jsonl(run_dir / "decision_trace.jsonl"):
        v = _safe_get(rec, ["interaction_intensity", "intensity", "action_intensity"])
        if v is None:
            intensities.append(None)
        elif _is_num(v):
            intensities.append(float(v))
        else:
            intensities.append(None)
        if len(intensities) >= n:
            break
    # pad if shorter
    if len(intensities) < n:
        intensities.extend([None] * (n - len(intensities)))

    xs: List[float] = []
    ys: List[float] = []
    for i in range(1, n):
        if intensities[i] is None:
            continue
        if Limp_m_series[i] != 1 or Limp_m_series[i - 1] != 1:
            continue
        if Limp_series[i] is None or Limp_series[i - 1] is None:
            continue
        d = float(Limp_series[i]) - float(Limp_series[i - 1])  # dL_imp/dt (per tick)
        xs.append(float(intensities[i]))
        ys.append(float(d))

    r = _pearsonr(xs, ys)

    # --- Nonlinear collapse signature: bin by L and summarize gate/intensity-cap visibility
    # intensity_cap may be in decision_trace or order_attempts; summarize if present.
    intensity_caps: List[Optional[float]] = []
    for _ln, rec in _iter_jsonl(run_dir / "decision_trace.jsonl"):
        v = rec.get("intensity_cap")
        if v is None:
            intensity_caps.append(None)
        elif _is_num(v):
            intensity_caps.append(float(v))
        else:
            intensity_caps.append(None)
        if len(intensity_caps) >= n:
            break
    if len(intensity_caps) < n:
        intensity_caps.extend([None] * (n - len(intensity_caps)))

    # We don't require perfect per-tick action_allowed; use global gate_rate plus by-bin using decision_trace when possible
    action_allowed_by_tick: List[Optional[bool]] = []
    for _ln, rec in _iter_jsonl(run_dir / "decision_trace.jsonl"):
        aa = rec.get("action_allowed")
        action_allowed_by_tick.append(aa if isinstance(aa, bool) else None)
        if len(action_allowed_by_tick) >= n:
            break
    if len(action_allowed_by_tick) < n:
        action_allowed_by_tick.extend([None] * (n - len(action_allowed_by_tick)))

    bin_stats: List[Dict[str, Any]] = []
    for lo, hi in bins:
        cnt = 0
        aa_cnt = 0
        aa_blocked = 0
        cap_cnt = 0
        cap_sum = 0.0
        for i in range(n):
            if Lm_series[i] != 1 or L_series[i] is None:
                continue
            v = float(L_series[i])
            if v < lo or v >= hi:
                continue
            cnt += 1
            aa = action_allowed_by_tick[i]
            if isinstance(aa, bool):
                aa_cnt += 1
                if aa is False:
                    aa_blocked += 1
            cap = intensity_caps[i]
            if cap is not None:
                cap_cnt += 1
                cap_sum += float(cap)
        bin_stats.append(
            {
                "L_bin": [lo, hi],
                "L_sample_count": cnt,
                "action_allowed_sample_count": aa_cnt,
                "action_blocked_count": aa_blocked,
                "action_blocked_rate": (aa_blocked / aa_cnt) if aa_cnt > 0 else None,
                "intensity_cap_sample_count": cap_cnt,
                "intensity_cap_mean": (cap_sum / cap_cnt) if cap_cnt > 0 else None,
            }
        )

    report = {
        "tool": "summarize_survival_space_report_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "ablation": {
            "survival_space": {
                "enabled": ab_enabled,
                "mode": ab_mode,
            }
        },
        "signals": {
            "gate_trigger_rate": {
                "total_samples": gate_total,
                "blocked_samples": gate_blocked,
                "blocked_rate": gate_rate,
                "top_reason_codes": dict(sorted(gate_reason_counts.items(), key=lambda x: (-x[1], x[0]))[:50]),
            },
            "exhaustion_attribution": first_exhaust,
            "action_dissipation_coupling": {
                "paired_samples": len(xs),
                "pearsonr_intensity_vs_dL_imp_dt": r,
                "note": "Expect negative correlation in full if higher intensity dissipates L_imp; expect weakened/none in no_m.",
            },
            "nonlinear_collapse": {
                "l_epsilon": l_epsilon,
                "binned_stats": bin_stats,
            },
        },
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Run dir containing survival_space + decision/order evidence")
    ap.add_argument("--output", default="", help="Output report.json path (default: <run_dir>/report.json)")
    ap.add_argument("--l_epsilon", type=float, default=0.02, help="Exhaustion threshold for L (default 0.02)")
    ap.add_argument(
        "--bins",
        default="0,0.05;0.05,0.1;0.1,0.2;0.2,0.4;0.4,0.7;0.7,1.01",
        help="Semicolon-separated L bins 'lo,hi;lo,hi;...'",
    )
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1

    bins: List[Tuple[float, float]] = []
    try:
        for part in args.bins.split(";"):
            part = part.strip()
            if not part:
                continue
            lo_s, hi_s = part.split(",", 1)
            bins.append((float(lo_s.strip()), float(hi_s.strip())))
    except Exception as e:
        print(f"ERROR: invalid --bins: {e}", file=sys.stderr)
        return 1

    try:
        report = summarize(run_dir, l_epsilon=float(args.l_epsilon), bins=bins)
    except ValueError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out_path = Path(args.output).expanduser().resolve() if args.output else (run_dir / "report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

