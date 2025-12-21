# V10 Milestone: C0.7 Positions Fallback (Reconstructed-from-Fills) PASSED — 2025-12-21

## What this milestone means / 这意味着什么

**English (primary)**: We have a completed `okx_demo_api` run where the system can **produce an auditable positions snapshot** using a conservative fallback: **reconstruct positions from fills evidence**.  
This is the minimum requirement to make I1/I2 (position state/direction) **obtainable in the execution-interface world** without faking exchange positions.

**中文（辅助）**：我们已经跑通了“执行接口世界”里 I（持仓状态）的最小可得性：  
在 `okx_demo_api` 下，系统能够基于可审计证据重建持仓，并落盘 `positions_snapshot.json`，同时把 manifest 的口径升级为 `reconstructed_from_fills`。  
这不代表 demo positions 可靠，而是代表 **fallback 证据链成立**，不会“凭空猜持仓”。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251221_155211_3126b54`
- **Mode**: `okx_demo_api`
- **Status**: `completed`
- **api_calls**: `9` (must be > 0)

Artifacts present:

- `run_manifest.json`
- `execution_fingerprint.json`
- `multiple_experiments_summary.json`
- `okx_rest_alignment_report.json`
- `okx_rest_raw_samples.json`
- ✅ `positions_snapshot.json` (C0.7 key artifact)

---

## Manifest truth markers (positions) / Manifest关键字段（持仓口径）

- `positions_fallback_ok = true`
- `positions_fallback_reason = null`
- `positions_quality = "reconstructed_from_fills"`
- `positions_source = "reconstructed_from_fills"`
- `positions_evidence_path` points to:
  - `/var/lib/prometheus-quant/runs/run_20251221_155211_3126b54/positions_snapshot.json`

---

## Snapshot note / 快照解读（重要）

This run’s `positions_snapshot.json` indicates **flat / no position** at the snapshot time:

- `has_position = false`
- `position_side = null`
- `contracts = 0.0`
- `avg_entry_price = null`
- `source = "reconstructed_from_fills"`

This is **still a PASS**: the milestone validates the **reconstruction pipeline + evidence integrity**, not “must end with a position”.

---

## Scope boundary / 边界

- This milestone validates I-fallback **auditability**, not profitability.
- It does not claim demo friction equals live; `impedance_fidelity` remains demo-labeled.
- Core (`prometheus/v10/core/`) remains unchanged.


