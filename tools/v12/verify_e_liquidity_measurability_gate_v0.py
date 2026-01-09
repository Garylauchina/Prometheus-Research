#!/usr/bin/env python3
"""
V12 Gate — E-liquidity measurability qualification v0 (stdlib only).

Checks bid/ask coverage in a replay dataset's market_snapshot.jsonl.

Verdict:
  - PASS: N>=1000 and coverage>=0.95
  - NOT_MEASURABLE: N>=1000 and coverage<0.95
  - FAIL: evidence broken (missing file / invalid JSONL) or N<1000
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


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


def _safe_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_dir", required=True)
    ap.add_argument("--min_ticks", type=int, default=1000)
    ap.add_argument("--coverage_threshold", type=float, default=0.95)
    ap.add_argument("--output_json", default="")
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    p = dataset_dir / "market_snapshot.jsonl"
    report: Dict[str, Any] = {
        "tool": "verify_e_liquidity_measurability_gate_v0",
        "generated_at_utc": _ts_utc(),
        "dataset_dir": str(dataset_dir),
        "market_snapshot_jsonl": str(p),
        "min_ticks": int(args.min_ticks),
        "coverage_threshold": float(args.coverage_threshold),
        "stats": {},
        "verdict": "FAIL",
        "errors": [],
    }

    if not p.exists():
        report["errors"].append("missing_required_file:market_snapshot.jsonl")
        if args.output_json:
            Path(args.output_json).expanduser().resolve().write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 2

    N = 0
    ok = 0
    bad_bid = 0
    bad_ask = 0
    missing_bid = 0
    missing_ask = 0
    try:
        for _ln, rec in _iter_jsonl(p):
            N += 1
            bid = rec.get("bid_px_1")
            ask = rec.get("ask_px_1")
            if bid is None:
                missing_bid += 1
            if ask is None:
                missing_ask += 1
            bid_f = _safe_float(bid)
            ask_f = _safe_float(ask)
            if bid_f is None or bid_f <= 0:
                bad_bid += 1
                continue
            if ask_f is None or ask_f <= 0:
                bad_ask += 1
                continue
            ok += 1
    except Exception as e:
        report["errors"].append(f"market_snapshot_jsonl_invalid:{e}")
        print(json.dumps(report, ensure_ascii=False))
        return 2

    if N < int(args.min_ticks):
        report["errors"].append(f"insufficient_ticks:N={N} < min_ticks={int(args.min_ticks)}")
        report["stats"] = {"N": N, "eligible_tick_count": ok}
        print(json.dumps(report, ensure_ascii=False))
        return 2

    coverage = ok / max(1, N)
    report["stats"] = {
        "N": N,
        "eligible_tick_count": ok,
        "coverage": coverage,
        "missing_bid_count": missing_bid,
        "missing_ask_count": missing_ask,
        "bad_bid_count": bad_bid,
        "bad_ask_count": bad_ask,
    }

    if coverage >= float(args.coverage_threshold):
        report["verdict"] = "PASS"
        code = 0
    else:
        report["verdict"] = "NOT_MEASURABLE"
        code = 0

    if args.output_json:
        out = Path(args.output_json).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

