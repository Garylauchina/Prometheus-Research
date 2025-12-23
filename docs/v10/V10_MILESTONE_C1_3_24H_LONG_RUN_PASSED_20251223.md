# V10 Milestone: C1.3 24h Long-Run (okx_demo_api) PASSED — 2025-12-23

## What this milestone means / 这意味着什么

**English (primary)**: We completed a **24-hour `okx_demo_api` run** with:

- stable evidence-chain artifacts over day-scale runtime
- C1.1 sharding + indexing + hash continuity working end-to-end
- bounded raw growth (no monolithic blow-up)
- manifest remaining the stable audit entry point

**中文（辅助）**：我们完成了整天级别（24h）的长跑，并证明证据链在日尺度下仍连续、可审计、可回放入口稳定；分片+索引+hash 的增长控制有效。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251222_012118_4974080`
- **Mode**: `okx_demo_api`
- **Status**: `completed`
- **Start (UTC)**: `2025-12-22T01:21:18.830030Z`
- **End (UTC)**: `2025-12-23T01:21:30.531561Z`
- **Duration**: `86411s` (≈ 24.00 hours)
- **api_calls**: `1435` (manifest)

Raw growth-control (C1.1) summary:

- `m_execution_raw_index.json`:
  - `total_shards = 8`
  - `total_records = 1434`
- `positions_reconstruction_raw_index.json`:
  - `total_shards = 8`
  - `total_records = 1434`

Disk footprint (host):

- `RUN_DIR` size: `964K` (Mac host check)

Local audit report (Mac host, produced by a read-only verifier script):

- `C1_3_24H_REPORT_20251223_093404.txt` (path: `/Users/liugang/Cursor_Store/Prometheus-Quant/C1_3_24H_REPORT_20251223_093404.txt`)

---

## Audit notes / 审计备注（不影响通过，但需记账）

- There is a **1-call discrepancy**:
  - `run_manifest.api_calls = 1435`
  - `execution_fingerprint.api_calls = 1434`
  - `m_execution_raw_index.total_records = 1434`
- Interpretation (most likely): a single **connect/probe** call is counted in the manifest but not recorded as a raw evidence record (or vice versa).
- Action: later we should unify the definition of “api_calls” across manifest / fingerprint / raw index to avoid audit confusion.

---

## Interpretation / 解读

- PASS means our C-stage “flight recorder” can sustain **day-scale runtime** with:
  - continuous artifacts
  - bounded raw evidence growth via sharding
  - tamper-evident audit entry via index + hashes

---

## Next step / 下一步（建议）

- Proceed to **C2.0 incident drill** (ops-only actions) to validate the Incident Evidence Bundle (IEB) workflow, without changing `prometheus/v10/core/`.


