# Delivery — Quant Instructions — Local Reachability Trial-2 (Impedance probe; M-measurable) — 2026-01-09

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Make M measurable per tick via **probe attempts**
- Generate `<RUN_DIR>/local_reachability.jsonl` using the **M-only impedance proxy** (no thresholds)

Research references (absolute paths):
- SSOT v0: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Pre-reg (Trial-2): `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`

---

## A) Runner change (Quant): add M-probe attempts (measurement only)

Modify `tools/v12/run_survival_space_em_v1.py`:

1) Add CLI arg:
- `--probe_attempts_per_tick` (int, default 0)

2) During each tick, **independently of gate / agent action**, generate exactly `probe_attempts_per_tick` simulated attempts (measurement only) and record them into:
- `order_attempts.jsonl` (strict JSONL; you may add an extra field `attempt_kind="probe"` but keep existing fields intact)
- ensure these probe attempts contribute to:
  - `interaction_impedance.metrics.order_attempts_count` (so M becomes measurable per tick)

Hard constraints:
- Probe attempts MUST NOT alter survival ledger or reward ledger.
- Probe attempts MUST NOT bypass agent gate semantics (they are not “agent actions”).

Acceptance expectation:
- If `--probe_attempts_per_tick 1`, then every tick should have `interaction_impedance.metrics.order_attempts_count >= 1` and `interaction_impedance.verdict == PASS`.

---

## B) Create Trial-2 posthoc tool in Quant

Create:
- `tools/v12/posthoc_local_reachability_v2_impedance_proxy.py`

Inputs (required):
- `<RUN_DIR>/interaction_impedance.jsonl` (must be PASS per tick)
- `<RUN_DIR>/decision_trace.jsonl` (for tick indexing + join keys)

Output:
- `<RUN_DIR>/local_reachability.jsonl` (strict JSONL; SSOT schema)

Frozen mapping (from Trial-2 pre-reg):
- N=9
- latency_hi_ms = 200.0
- coefficients: a=2.0, b=3.0, c=2.0, d=1.0
- `L_m = exp(-(a*rej_rate + b*rl_rate + c*http_rate + d*lat_norm))`
- `feasible_count = floor(N * L_m)`

### B.1 Cat command (create file)

```bash
cat > /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py << 'EOF'
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


N = 9
LAT_HI_MS = 200.0
A = 2.0
B = 3.0
C = 2.0
D = 1.0


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(\"--run_dir\", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    p_imp = run_dir / \"interaction_impedance.jsonl\"
    p_dt = run_dir / \"decision_trace.jsonl\"
    if not p_imp.exists() or not p_dt.exists():
        print(f\"FAIL: missing required files under {run_dir}\", file=sys.stderr)
        return 2

    # index impedance by ts_utc (tick-aligned)
    imp_by_ts: Dict[str, Dict[str, Any]] = {}
    for _ln, rec in _iter_jsonl(p_imp):
        ts = rec.get(\"ts_utc\")
        if isinstance(ts, str) and ts:
            imp_by_ts[ts] = rec

    out_path = run_dir / \"local_reachability.jsonl\"
    tmp_path = run_dir / f\".local_reachability.tmp.{_ts_utc().replace(':','').replace('.','')}.jsonl\"

    lines = 0
    with tmp_path.open(\"w\", encoding=\"utf-8\") as w:
        tick_index = 0
        for _ln, drec in _iter_jsonl(p_dt):
            ts = drec.get(\"ts_utc\") or \"\"
            sid = drec.get(\"market_snapshot_id\")
            aid = drec.get(\"account_id_hash\")
            if not (isinstance(ts, str) and ts and isinstance(sid, str) and sid and isinstance(aid, str) and aid):
                tick_index += 1
                continue

            imp = imp_by_ts.get(ts)
            if not isinstance(imp, dict):
                raise ValueError(f\"missing impedance tick for ts_utc={ts}\")

            verdict = imp.get(\"verdict\")
            if verdict != \"PASS\":
                raise ValueError(f\"impedance not PASS at ts_utc={ts}: {verdict}\")

            m = imp.get(\"metrics\") or {}
            attempts = int(m.get(\"order_attempts_count\", 0) or 0)
            rejects = int(m.get(\"reject_count\", 0) or 0)
            rl = int(m.get(\"rate_limited_count\", 0) or 0)
            http_err = int(m.get(\"http_error_count\", 0) or 0)
            lat_ms = m.get(\"avg_ack_latency_ms\")
            lat_f = float(lat_ms) if isinstance(lat_ms, (int, float)) else None

            if attempts < 1:
                raise ValueError(f\"attempts<1 at ts_utc={ts} (probe missing)\")

            rej_rate = rejects / max(1, attempts)
            rl_rate = rl / max(1, attempts)
            http_rate = http_err / max(1, attempts)
            lat_norm = 0.0 if lat_f is None else _clamp01(lat_f / LAT_HI_MS)

            Lm = math.exp(-((A * rej_rate) + (B * rl_rate) + (C * http_rate) + (D * lat_norm)))
            Lm = _clamp01(Lm)

            feasible_count = int(math.floor(N * float(Lm)))
            if feasible_count < 0:
                feasible_count = 0
            if feasible_count > N:
                feasible_count = N

            out = {
                \"ts_utc\": ts,
                \"snapshot_id\": sid,
                \"account_id_hash\": aid,
                \"tick_index\": tick_index,
                \"state_id\": f\"{sid}:{aid}:{tick_index}\",
                \"world_contract\": {\"M_frozen\": True, \"world_epoch_id\": \"unknown\"},
                \"neighborhood\": {\"candidate_count\": N, \"feasible_count\": feasible_count, \"feasible_ratio\": feasible_count / N},
                \"graph_optional\": {\"enabled\": False, \"feasible_component_count\": None, \"largest_feasible_component_ratio\": None, \"edge_cut_rate\": None},
                \"death_label_ex_post\": {\"enabled\": False, \"dead_at_or_before_tick\": None},
                \"reason_codes\": [\n+                    \"reachability_proxy:impedance_exp\",\n+                    \"reachability_proxy:coeffs:a2_b3_c2_d1\",\n+                    \"reachability_proxy:latency_hi_ms=200\",\n+                    \"reachability_proxy:probe_attempts_per_tick=1\",\n+                ],\n+            }\n+            w.write(json.dumps(out, ensure_ascii=False) + \"\\n\")\n+            lines += 1\n+            tick_index += 1\n+\n+    tmp_path.replace(out_path)\n+    print(json.dumps({\"verdict\": \"PASS\", \"run_dir\": str(run_dir), \"lines_written\": lines}, ensure_ascii=False))\n+    return 0\n+\n+\n+if __name__ == \"__main__\":\n+    raise SystemExit(main())\n+EOF\n+chmod +x /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py\n+```\n+\n+---\n+\n+## C) Run (one example)\n+\n+1) Re-run (or create) a modeling-tool run with probe enabled:\n+\n+```bash\n+python3 tools/v12/run_survival_space_em_v1.py \\\n+  --dataset_dir \"/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m\" \\\n+  --runs_root \"/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool\" \\\n+  --steps 10000 \\\n+  --seed 60001 \\\n+  --ablation_mode full \\\n+  --probe_attempts_per_tick 1\n+```\n+\n+2) Generate Trial-2 reachability output:\n+\n+```bash\n+python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \\\n+  --run_dir \"<RUN_DIR>\"\n+```\n+\n+3) Return to Research:\n+- `<RUN_DIR>` absolute path\n+- command lines\n+- `wc -l <RUN_DIR>/local_reachability.jsonl`\n+- verifier output:\n+  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_local_reachability_v0.py --run_dir <RUN_DIR>`\n+\n*** End Patch"} }
