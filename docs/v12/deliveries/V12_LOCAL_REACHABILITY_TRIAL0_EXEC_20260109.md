# Delivery — Quant Instructions — Local Reachability Trial-0 Smoke (2026-01-09)

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`  
Goal: produce `<RUN_DIR>/local_reachability.jsonl` for an existing Survival Space run directory, per Research SSOT.

SSOT / pre-reg references (Research repo):
- SSOT: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL0_SMOKE_V0_20260109.md`

---

## A) Create a post-hoc tool in Quant

Create a new script:

- `tools/v12/posthoc_local_reachability_v0.py`

It must:
- Take `--run_dir <RUN_DIR>`
- Require files:
  - `<RUN_DIR>/run_manifest.json`
  - `<RUN_DIR>/survival_space.jsonl`
  - `<RUN_DIR>/decision_trace.jsonl`
- Write:
  - `<RUN_DIR>/local_reachability.jsonl` (strict JSONL, append-only)
- Implement Trial-0 frozen definitions:
  - Neighborhood `N=9`, deltas `[-0.40,-0.20,-0.10,-0.05,0,+0.05,+0.10,+0.20,+0.40]`
  - candidate intensity: `clip(proposed_intensity * (1 + delta), 0..1)`
  - feasibility (M-frozen proxy): `feasible=1` iff `candidate_intensity>0` AND `L_imp>0` (same tick)
  - graph_optional: disabled (null fields)
  - death_label_ex_post: disabled (null)

### A.1 Cat command (create file)

```bash
cat > /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v0.py << 'EOF'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path} line {ln}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be object at {path} line {ln}")
            yield ln, obj


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _clip01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass(frozen=True)
class TickRec:
    snapshot_id: str
    account_id_hash: str
    tick_index: int
    ts_utc: str
    proposed_intensity: float
    L_imp: Optional[float]


DELTAS = [-0.40, -0.20, -0.10, -0.05, 0.00, +0.05, +0.10, +0.20, +0.40]


def _load_manifest_epoch(run_manifest: Dict[str, Any]) -> str:
    # best-effort: keep deterministic string even if absent
    epoch = run_manifest.get("world_epoch_id")
    return epoch if isinstance(epoch, str) and epoch else "unknown"


def _load_by_tick(run_dir: Path) -> List[TickRec]:
    p_ss = run_dir / "survival_space.jsonl"
    p_dt = run_dir / "decision_trace.jsonl"

    # index survival_space by snapshot_id
    ss_by_snapshot: Dict[str, Dict[str, Any]] = {}
    for _ln, rec in _iter_jsonl(p_ss):
        sid = rec.get("snapshot_id")
        if isinstance(sid, str) and sid:
            ss_by_snapshot[sid] = rec

    out: List[TickRec] = []
    for _ln, rec in _iter_jsonl(p_dt):
        sid = rec.get("snapshot_id")
        aid = rec.get("account_id_hash")
        ti = rec.get("tick_index")
        ts = rec.get("ts_utc")
        prop = rec.get("proposed_intensity")

        if not (isinstance(sid, str) and sid and isinstance(aid, str) and aid):
            continue
        if not isinstance(ti, int):
            continue
        if not (isinstance(ts, str) and ts):
            ts = ""
        if not _is_num(prop):
            continue

        ss = ss_by_snapshot.get(sid)
        L_imp = None
        if isinstance(ss, dict):
            x = ss.get("L_imp")
            if _is_num(x):
                L_imp = float(x)

        out.append(
            TickRec(
                snapshot_id=sid,
                account_id_hash=aid,
                tick_index=int(ti),
                ts_utc=ts,
                proposed_intensity=_clip01(float(prop)),
                L_imp=L_imp,
            )
        )

    if not out:
        raise ValueError("No usable ticks found in decision_trace.jsonl")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        print(f"FAIL: run_dir not found: {run_dir}", file=sys.stderr)
        return 2

    p_manifest = run_dir / "run_manifest.json"
    p_ss = run_dir / "survival_space.jsonl"
    p_dt = run_dir / "decision_trace.jsonl"
    for p in (p_manifest, p_ss, p_dt):
        if not p.exists():
            print(f"FAIL: missing required file: {p}", file=sys.stderr)
            return 2

    try:
        manifest = json.loads(p_manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("run_manifest.json must be a JSON object")
        world_epoch_id = _load_manifest_epoch(manifest)
        ticks = _load_by_tick(run_dir)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2

    out_path = run_dir / "local_reachability.jsonl"
    tmp_path = run_dir / f".local_reachability.tmp.{_ts_utc().replace(':','').replace('.','')}.jsonl"

    lines = 0
    with tmp_path.open("w", encoding="utf-8") as w:
        for t in ticks:
            # Trial-0 frozen feasibility: candidate_intensity>0 AND L_imp>0 (same tick)
            cand = []
            for d in DELTAS:
                cand.append(_clip01(t.proposed_intensity * (1.0 + float(d))))

            candidate_count = len(cand)
            if candidate_count < 1:
                raise ValueError("candidate_count < 1 (neighborhood undefined)")

            feasible_count = 0
            for x in cand:
                feasible = 1 if (x > 0.0 and (t.L_imp is not None and t.L_imp > 0.0)) else 0
                feasible_count += feasible

            feasible_ratio = feasible_count / max(1, candidate_count)

            rec = {
                "ts_utc": t.ts_utc,
                "snapshot_id": t.snapshot_id,
                "account_id_hash": t.account_id_hash,
                "tick_index": t.tick_index,
                "state_id": f"{t.snapshot_id}:{t.account_id_hash}:{t.tick_index}",
                "world_contract": {"M_frozen": True, "world_epoch_id": world_epoch_id},
                "neighborhood": {
                    "candidate_count": candidate_count,
                    "feasible_count": feasible_count,
                    "feasible_ratio": feasible_ratio,
                },
                "graph_optional": {
                    "enabled": False,
                    "feasible_component_count": None,
                    "largest_feasible_component_ratio": None,
                    "edge_cut_rate": None,
                },
                "death_label_ex_post": {"enabled": False, "dead_at_or_before_tick": None},
                "reason_codes": [],
            }
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")
            lines += 1

    # atomic-ish replace
    tmp_path.replace(out_path)
    print(json.dumps({"verdict": "PASS", "run_dir": str(run_dir), "lines_written": lines}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
EOF
chmod +x /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v0.py
```

---

## B) Run Trial-0 on an existing run_dir

Pick one existing Survival Space run directory that contains:
- `run_manifest.json`
- `survival_space.jsonl`
- `decision_trace.jsonl`

Then run:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v0.py \
  --run_dir "<RUN_DIR>"
```

Expected output:
- `<RUN_DIR>/local_reachability.jsonl` exists and is non-empty

---

## C) Report back (for Research completion anchors)

Send back:
- the absolute `<RUN_DIR>`
- the exact command you ran
- `wc -l <RUN_DIR>/local_reachability.jsonl`
- first 2 lines + last 2 lines (sanity only)

