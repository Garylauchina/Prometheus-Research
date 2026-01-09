#!/usr/bin/env python3
"""
V12 Local Reachability — Trial-1 volatility proxy builder v0 (Research repo, stdlib only).

Purpose:
  - Reproduce the Trial-1 (E-only volatility proxy) local_reachability.jsonl from an existing Quant run_dir
  - Write output to a specified path (so we do NOT overwrite Quant artifacts)

This is a builder, not a verifier. Output must be verified with:
  - tools/v12/verify_local_reachability_v0.py
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


def _safe_float(x: Any) -> float:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            raise ValueError("empty numeric string")
        return float(s)
    raise ValueError(f"not a number: {type(x)}")


N = 9
K = 500.0


def _load_market_lv(market_snapshot_jsonl: Path) -> Dict[str, float]:
    market_by_id: Dict[str, Tuple[str, float]] = {}
    order: List[str] = []
    for _ln, rec in _iter_jsonl(market_snapshot_jsonl):
        sid = rec.get("snapshot_id")
        ts = rec.get("ts_utc")
        lp = rec.get("last_px")
        if not (isinstance(sid, str) and sid and isinstance(ts, str) and ts):
            continue
        px = _safe_float(lp)
        if px <= 0:
            raise ValueError("last_px must be > 0")
        market_by_id[sid] = (ts, float(px))
        order.append(sid)
    if not order:
        raise ValueError("empty market_snapshot.jsonl")

    lv_by_id: Dict[str, float] = {}
    prev_px = None
    for i, sid in enumerate(order):
        _ts, px = market_by_id[sid]
        if i == 0 or prev_px is None:
            r = 0.0
        else:
            r = abs(math.log(px / prev_px))
        lv = math.exp(-K * r)
        if lv < 0.0:
            lv = 0.0
        if lv > 1.0:
            lv = 1.0
        lv_by_id[sid] = float(lv)
        prev_px = px
    return lv_by_id


def build(run_dir: Path, output_jsonl: Path) -> int:
    p_market = run_dir / "market_snapshot.jsonl"
    p_dt = run_dir / "decision_trace.jsonl"
    if not p_market.exists():
        raise FileNotFoundError(f"missing: {p_market}")
    if not p_dt.exists():
        raise FileNotFoundError(f"missing: {p_dt}")

    lv_by_id = _load_market_lv(p_market)

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_jsonl.parent / f".tmp_local_reachability_trial1.{_ts_utc().replace(':','').replace('.','')}.jsonl"
    lines = 0
    with tmp.open("w", encoding="utf-8") as w:
        tick_index = 0
        for _ln, rec in _iter_jsonl(p_dt):
            sid = rec.get("market_snapshot_id")
            aid = rec.get("account_id_hash")
            ts = rec.get("ts_utc") or ""
            inten = rec.get("interaction_intensity")
            # keep alignment discipline but do not use intensity to change neighborhood size in Trial-1
            if not (isinstance(sid, str) and sid and isinstance(aid, str) and aid):
                tick_index += 1
                continue
            if not isinstance(ts, str):
                ts = ""
            if not isinstance(inten, int):
                tick_index += 1
                continue

            lv = lv_by_id.get(sid)
            if lv is None:
                raise ValueError(f"missing market_snapshot_id in market_snapshot.jsonl: {sid}")

            feasible_count = int(math.floor(N * float(lv)))
            if feasible_count < 0:
                feasible_count = 0
            if feasible_count > N:
                feasible_count = N

            out = {
                "ts_utc": ts,
                "snapshot_id": sid,
                "account_id_hash": aid,
                "tick_index": tick_index,
                "state_id": f"{sid}:{aid}:{tick_index}",
                "world_contract": {"M_frozen": True, "world_epoch_id": "unknown"},
                "neighborhood": {"candidate_count": N, "feasible_count": feasible_count, "feasible_ratio": feasible_count / N},
                "graph_optional": {
                    "enabled": False,
                    "feasible_component_count": None,
                    "largest_feasible_component_ratio": None,
                    "edge_cut_rate": None,
                },
                "death_label_ex_post": {"enabled": False, "dead_at_or_before_tick": None},
                "reason_codes": ["reachability_proxy:volatility_exp", "reachability_proxy:k=500"],
            }
            w.write(json.dumps(out, ensure_ascii=False) + "\n")
            lines += 1
            tick_index += 1

    tmp.replace(output_jsonl)
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source_run_dir", required=True)
    ap.add_argument("--output_jsonl", required=True)
    args = ap.parse_args()

    run_dir = Path(args.source_run_dir).expanduser().resolve()
    out = Path(args.output_jsonl).expanduser().resolve()

    if not run_dir.exists():
        print(f"FAIL: source_run_dir not found: {run_dir}", file=sys.stderr)
        return 2

    try:
        lines = build(run_dir, out)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2

    print(json.dumps({"verdict": "PASS", "source_run_dir": str(run_dir), "output_jsonl": str(out), "lines_written": lines, "k": K}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

