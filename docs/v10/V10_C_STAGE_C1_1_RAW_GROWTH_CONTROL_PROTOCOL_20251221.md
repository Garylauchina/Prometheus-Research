# V10 C-Stage Protocol: C1.1 Raw Evidence Growth Control (Rolling Shards + Index) — 2025-12-21

## Purpose / 目的

**English (primary)**: After C1.0 (1h long-run) we observed raw evidence growth.  
C1.1 introduces a **scalable, auditable raw-evidence storage pattern**:

- split raw evidence into rolling shards (bounded file size)
- maintain an index file (hashes + counts + time ranges)
- make `run_manifest.json` reference the index (stable audit entry point)

**中文（辅助）**：C1.1 的目标是：raw 证据允许增长，但必须“可控增长、可审计增长、可回放增长”，避免长跑变成“磁盘黑天鹅”。

---

## Scope / 范围

- **Allowed**: `prometheus/v10/ops/**` only
- **Forbidden**: any change to `prometheus/v10/core/**`
- No monkey patch / runtime injection.

---

## Target artifacts / 目标产物（RUN_DIR 内）

### M execution raw evidence

- Shards:
  - `m_execution_raw_part_0001.json`
  - `m_execution_raw_part_0002.json`
  - ...
- Index:
  - `m_execution_raw_index.json`

### Positions reconstruction raw evidence

- Shards:
  - `positions_reconstruction_raw_part_0001.json`
  - `positions_reconstruction_raw_part_0002.json`
  - ...
- Index:
  - `positions_reconstruction_raw_index.json`

> Notes:
> - Shards are append-only per shard; once a shard is closed, never modify it.
> - Index is updated append-only in semantics (may be rewritten as a whole file, but must preserve all prior shard records).

---

## Sharding policy / 分片策略（最小可行）

Pick one (must be recorded in the index `policy` section):

- **By record count (recommended)**: rotate when `records >= 200`
- **By wall-clock**: rotate every `5 minutes`

---

## Index schema (minimal) / 索引结构（最小字段）

Each index file should include:

- `version`
- `run_id`
- `created_at`
- `policy` (type + thresholds)
- `shards`: list of
  - `filename`
  - `start_ts` / `end_ts` (UTC)
  - `records_count`
  - `sha256_16` (hash of the shard file content)

---

## Manifest requirements / manifest 要求（强制）

`run_manifest.json` must include:

- `m_execution_raw_index_path`
- `m_execution_raw_index_hash`
- `positions_reconstruction_raw_index_path`
- `positions_reconstruction_raw_index_hash`

The manifest must not “forget” existing single-file paths if they existed; but future audit entry should prefer the index fields.

---

## Acceptance / 验收

PASS if:

- At least one shard exists for each raw channel (M + positions) in a 1h run
- Index files exist and cover all shards
- Manifest references index paths + hashes
- Evidence chain remains complete (run_manifest/alignment/fingerprint/summary/etc.)

---

## Why this is still honest / 为什么这仍然“诚实”

- We do not delete evidence; we only **structure it**.
- Hashes make each shard tamper-evident.
- Index becomes the stable “audit entry point”, preventing drift in how we locate evidence.


