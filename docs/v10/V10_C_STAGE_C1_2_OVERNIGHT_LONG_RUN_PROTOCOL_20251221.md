# V10 C-Stage Protocol: C1.2 Overnight Long-Run (6–8h) Evidence-Chain Stress Test — 2025-12-21

## Purpose / 目的

**English (primary)**: Validate that our C-stage evidence chain remains stable for **multiple hours** (sleep-scale), including:

- shard/index growth control (C1.1) under sustained runtime
- artifact continuity (no missing files)
- stable manifest references (index paths + hashes)
- safe STOP semantics remain available (optional)

**中文（辅助）**：把 C1.0 的 1 小时验证升级为“睡一觉级别”的多小时长跑（6–8小时），专门压测：分片索引是否稳定、证据链是否不断、raw 增长是否仍可控。

---

## Preconditions / 前置条件

- C1.0 PASSED (1h long-run)
- C1.1 PASSED (raw growth control: shards + index + hash + manifest ref)

---

## Run configuration / 运行配置

- Mode: `okx_demo_api`
- Duration: **6–8 hours** (recommended: 6h = 21600s for the first overnight run)
- Evidence pattern: C1.1 shards + indexes enabled
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
- `m_execution_raw_index.json` + `m_execution_raw_part_*.json` (1+ shards)
- `positions_reconstruction_raw_index.json` + `positions_reconstruction_raw_part_*.json` (1+ shards)

---

## Acceptance checks / 验收检查

### A) Duration / 时长

- `duration_seconds >= 21600` (6h) if the goal is “completed”.
- If STOP is used, `status="interrupted"` with `stop_*` fields and still full artifacts.

### B) Evidence continuity / 证据连续性

- All required artifacts exist.
- Index files cover all shard files.
- Manifest references index paths + hashes (stable audit entry point).

### C) Growth control / 增长控制

- Shards rotate according to the configured policy (e.g., records_count threshold).
- Single raw file does not grow unbounded (no monolithic raw file).

---

## Minimal report back / 最小回传

After the run:

1) `RUN_DIR`
2) `ls -la RUN_DIR` (file list + sizes)
3) From `run_manifest.json`:
   - `status`, `mode`, `api_calls`
   - `start_time`, `end_time`, `duration_seconds`
   - index paths + hashes for both raw channels
4) From each index:
   - `total_shards`, `total_records`
   - first/last shard filenames and hashes


