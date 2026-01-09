# Delivery — Quant Instructions — Local Reachability Trial-1 (Volatility proxy; E-only) — 2026-01-09

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`  
Goal: generate `<RUN_DIR>/local_reachability.jsonl` using an E-only volatility proxy (no attempt-driven M), per Research pre-reg.

Research references (absolute paths):
- SSOT v0: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Pre-reg (Trial-1): `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL1_VOLATILITY_PROXY_V0_20260109.md`

---

## A) Create a post-hoc tool in Quant

Create:
- `tools/v12/posthoc_local_reachability_v1_volatility_proxy.py`

Inputs (required):
- `<RUN_DIR>/run_manifest.json`
- `<RUN_DIR>/market_snapshot.jsonl` (must contain `snapshot_id`, `ts_utc`, `last_px`)
- `<RUN_DIR>/decision_trace.jsonl` (must contain `market_snapshot_id`, `account_id_hash`, `interaction_intensity`, `ts_utc`)

Output:
- `<RUN_DIR>/local_reachability.jsonl` (strict JSONL)

Frozen rules (Trial-1):
- N=9, deltas = [-0.40,-0.20,-0.10,-0.05,0,+0.05,+0.10,+0.20,+0.40]
- r_t = abs(log(last_px_t / last_px_{t-1})), r_0=0
- L_v = exp(-k*r_t), k=500.0
- feasible_count = floor(N * L_v), feasible_ratio = feasible_count / N

### A.1 Cat command (create file)

```bash
cat > /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v1_volatility_proxy.py << 'EOF'
#!/usr/bin/env python3
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
        for ln, raw in enumerate(f, 1):
            s = raw.strip()
            if not s:
                continue
            obj = json.loads(s)
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be object at {path} line {ln}")
            yield ln, obj


def _safe_float(x: Any) -> float:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            raise ValueError("empty numeric string")
        return float(s)
    raise ValueError(f"not a number: {type(x)}")


DELTAS = [-0.40, -0.20, -0.10, -0.05, 0.00, +0.05, +0.10, +0.20, +0.40]
N = 9
K = 500.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        print(f"FAIL: run_dir not found: {run_dir}", file=sys.stderr)
        return 2

    p_manifest = run_dir / "run_manifest.json"
    p_market = run_dir / "market_snapshot.jsonl"
    p_dt = run_dir / "decision_trace.jsonl"
    for p in (p_manifest, p_market, p_dt):
        if not p.exists():
            print(f"FAIL: missing required file: {p}", file=sys.stderr)
            return 2

    # market snapshots: map snapshot_id -> (ts_utc, last_px)
    market_by_id: Dict[str, Tuple[str, float]] = {}
    market_order: List[str] = []
    try:
        for _ln, rec in _iter_jsonl(p_market):
            sid = rec.get("snapshot_id")
            ts = rec.get("ts_utc")
            lp = rec.get("last_px")
            if not (isinstance(sid, str) and sid and isinstance(ts, str) and ts):
                continue
            last_px = _safe_float(lp)
            if last_px <= 0:
                raise ValueError("last_px must be > 0")
            market_by_id[sid] = (ts, float(last_px))
            market_order.append(sid)
    except Exception as e:
        print(f"FAIL: parse market_snapshot.jsonl: {e}", file=sys.stderr)
        return 2

    if not market_order:
        print("FAIL: empty market_snapshot.jsonl", file=sys.stderr)
        return 2

    # precompute r_t and L_v per snapshot_id using market order
    Lv_by_id: Dict[str, float] = {}
    prev_px = None
    for i, sid in enumerate(market_order):
        _ts, px = market_by_id[sid]
        if i == 0 or prev_px is None:
            r = 0.0
        else:
            r = abs(math.log(px / prev_px))
        Lv = math.exp(-K * r)
        if Lv < 0.0:
            Lv = 0.0
        if Lv > 1.0:
            Lv = 1.0
        Lv_by_id[sid] = Lv
        prev_px = px

    out_path = run_dir / "local_reachability.jsonl"
    tmp_path = run_dir / f".local_reachability.tmp.{_ts_utc().replace(':','').replace('.','')}.jsonl"

    lines = 0
    try:
        with tmp_path.open("w", encoding="utf-8") as w:
            tick_index = 0
            for _ln, rec in _iter_jsonl(p_dt):
                sid = rec.get("market_snapshot_id")
                aid = rec.get("account_id_hash")
                ts = rec.get("ts_utc") or ""
                inten = rec.get("interaction_intensity")
                if not (isinstance(sid, str) and sid and isinstance(aid, str) and aid):
                    tick_index += 1
                    continue
                if not isinstance(ts, str):
                    ts = ""
                if not isinstance(inten, int):
                    tick_index += 1
                    continue

                Lv = Lv_by_id.get(sid)
                if Lv is None:
                    raise ValueError(f"missing market_snapshot_id in market_snapshot.jsonl: {sid}")

                # neighborhood (Trial-1 keeps it fixed-size; intensity is not used to change N)
                feasible_count = int(math.floor(N * float(Lv)))
                if feasible_count < 0:
                    feasible_count = 0
                if feasible_count > N:
                    feasible_count = N

                rec_out = {
                    "ts_utc": ts,
                    "snapshot_id": sid,
                    "account_id_hash": aid,
                    "tick_index": tick_index,
                    "state_id": f"{sid}:{aid}:{tick_index}",
                    "world_contract": {"M_frozen": True, "world_epoch_id": "unknown"},
                    "neighborhood": {
                        "candidate_count": N,
                        "feasible_count": feasible_count,
                        "feasible_ratio": feasible_count / N,
                    },
                    "graph_optional": {
                        "enabled": False,
                        "feasible_component_count": None,
                        "largest_feasible_component_ratio": None,
                        "edge_cut_rate": None,
                    },
                    "death_label_ex_post": {"enabled": False, "dead_at_or_before_tick": None},
                    "reason_codes": ["reachability_proxy:volatility_exp", "reachability_proxy:k=500"],
                }
                w.write(json.dumps(rec_out, ensure_ascii=False) + "\\n")
                lines += 1
                tick_index += 1
    except Exception as e:
        print(f"FAIL: build local_reachability.jsonl: {e}", file=sys.stderr)
        return 2

    tmp_path.replace(out_path)
    print(json.dumps({"verdict": "PASS", "run_dir": str(run_dir), "lines_written": lines, "k": K}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
EOF
chmod +x /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v1_volatility_proxy.py
```

---

## B) Run Trial-1 on a run_dir

Choose an existing `<RUN_DIR>` and run:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v1_volatility_proxy.py \\
  --run_dir \"<RUN_DIR>\"\n+```

Expected:
- `<RUN_DIR>/local_reachability.jsonl` exists and is non-empty

---

## C) Report back (for Research completion anchors)

Send back:
- the absolute `<RUN_DIR>`
- the exact command
- `wc -l <RUN_DIR>/local_reachability.jsonl`
- verifier output (Research):\n+  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_local_reachability_v0.py --run_dir <RUN_DIR>`\n+- summary output path:\n+  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_report_v0.py --run_dir <RUN_DIR> --output_json /tmp/local_reachability_report_<tag>.json`\n+
