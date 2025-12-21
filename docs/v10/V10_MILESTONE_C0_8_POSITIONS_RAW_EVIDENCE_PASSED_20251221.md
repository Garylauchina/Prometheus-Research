# V10 Milestone: C0.8 Positions Reconstruction Raw Evidence PASSED — 2025-12-21

## What this milestone means / 这意味着什么

**English (primary)**: We can now produce **two linked artifacts** for positions reconstruction in the execution-interface world:

- `positions_snapshot.json` (reconstruction result)
- `positions_reconstruction_raw.json` (sanitized raw evidence used for reconstruction)

This closes the “why do we believe this positions snapshot?” audit gap.

**中文（辅助）**：我们现在不只是“能重建持仓（结果）”，还做到了“重建依据可追溯（原始证据）”。  
这一步的意义是：以后任何人质疑 `positions_snapshot.json`，我们都能指回 `positions_reconstruction_raw.json`（脱敏）作为依据，而不是讲故事。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251221_161052_96de55f`
- **Mode**: `okx_demo_api`
- **Artifacts present**:
  - `run_manifest.json`
  - `execution_fingerprint.json`
  - `multiple_experiments_summary.json`
  - `okx_rest_alignment_report.json`
  - `okx_rest_raw_samples.json`
  - `positions_snapshot.json`
  - ✅ `positions_reconstruction_raw.json` (C0.8 key artifact)

---

## Pass criteria / 通过判定

- `positions_reconstruction_raw.json` exists in the run directory
- `run_manifest.json` includes:
  - `positions_reconstruction_raw_path`
  - `positions_reconstruction_raw_hash`
  - `positions_reconstruction_evidence_type`

> Note: The exact evidence type may vary by demo availability (`fills` / `order_status` / `synthetic_from_local_events`).  
The critical requirement is **honesty + auditability**, not a specific endpoint.

---

## Scope boundary / 边界

- This milestone validates **audit evidence integrity**, not profitability.
- Core (`prometheus/v10/core/`) remains unchanged.


