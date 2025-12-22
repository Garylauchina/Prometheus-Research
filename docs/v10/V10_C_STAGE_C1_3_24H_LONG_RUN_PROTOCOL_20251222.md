# V10 C-Stage Protocol: C1.3 24h Long-Run Evidence-Chain Stress Test — 2025-12-22

## Purpose / 目的

**English (primary)**: Validate that our C-stage evidence chain remains stable for **24 hours** under `okx_demo_api`, with C1.1 sharding/indexing enabled:

- continuous artifact integrity over day-scale runtime
- shard/index rotation stays consistent and tamper-evident (hashes)
- no silent drift in manifest fields
- no log spam / no silent hangs

**中文（辅助）**：C1.3 是“整天级别”的压力测试：跑满 24 小时，验证证据链不断、分片索引不崩、raw 增长可控、manifest 口径不漂移。

---

## Preconditions / 前置条件

- C1.0 PASSED (1h long-run)
- C1.1 PASSED (raw growth control: shards + index + hash + manifest ref)
- C1.2 PASSED (6h overnight run)

---

## Run configuration / 运行配置

- Mode: `okx_demo_api`
- Duration: **24h = 86400 seconds**
- Evidence pattern: C1.1 shards + indexes enabled
- STOP: **not used** (this run is for completion, not interruption semantics)
- Core invariance: **no changes to `prometheus/v10/core/`**

---

## Required artifacts / 必须产物（RUN_DIR 内）

Must exist:

- `run_manifest.json`
- `multiple_experiments_summary.json`
- `execution_fingerprint.json`
- `okx_rest_alignment_report.json`
- `okx_rest_raw_samples.json`
- `positions_snapshot.json`
- `m_execution_raw_index.json` + `m_execution_raw_part_*.json` (multiple shards expected)
- `positions_reconstruction_raw_index.json` + `positions_reconstruction_raw_part_*.json` (multiple shards expected)

---

## Acceptance checks / 验收检查

### A) Duration / 时长

- `status="completed"`
- `duration_seconds >= 86400` (allow small overhead)
- `api_calls > 0`

### B) Evidence continuity / 证据连续性

- All required artifacts exist at end of run.
- Index files cover all shard files (no orphan shards).
- Manifest references index paths + hashes.

### C) Growth control / 增长控制（重点）

- `total_shards` increases over time as expected (rotation works).
- No monolithic raw file blow-up.
- Index `total_records` increases monotonically.

### D) Sanity / 健康性

- No `NaN/Inf` in summaries (if reported).
- No infinite log spam.

---

## Minimal report back / 最小回传

After 24h:

1) `RUN_DIR`
2) `run_manifest.json` fields:
   - `status`, `mode`, `api_calls`
   - `start_time`, `end_time`, `duration_seconds`
   - `m_execution_raw_index_path/hash`
   - `positions_reconstruction_raw_index_path/hash`
3) Each index summary:
   - `total_shards`, `total_records`
   - first/last shard filename + `sha256_16`
4) Disk footprint:
   - total size of RUN_DIR


