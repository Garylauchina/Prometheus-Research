# V10 Milestone: C1.1 Raw Evidence Growth Control PASSED (Rolling Shards + Index) — 2025-12-21

## What this milestone means / 这意味着什么

**English (primary)**: We implemented and validated the C1.1 raw-evidence storage pattern:

- raw evidence is written as **rolling shards** (bounded growth per file)
- an **index JSON** records shard hashes + counts (tamper-evident)
- `run_manifest.json` references index paths + hashes (stable audit entry point)

This makes long-run evidence sustainable without sacrificing auditability.

**中文（辅助）**：我们把“raw 证据会无限长”的问题收口成工程可控形态：分片 + 索引 + hash + manifest 引用。  
从此 raw 证据既能增长，又不会把单文件写爆，也不会丢失可审计性。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251221_182148_4974080`
- **Artifacts present (10 files)**:
  - Base evidence chain (6):
    - `run_manifest.json`
    - `okx_rest_alignment_report.json`
    - `okx_rest_raw_samples.json`
    - `execution_fingerprint.json`
    - `multiple_experiments_summary.json`
    - `positions_snapshot.json`
  - C1.1 additions (4):
    - `m_execution_raw_part_0001.json`
    - `m_execution_raw_index.json`
    - `positions_reconstruction_raw_part_0001.json`
    - `positions_reconstruction_raw_index.json`

---

## Sharding policy / 分片策略

- Policy type: `records_count`
- Threshold: `200` records per shard

---

## Manifest requirements satisfied / manifest 要求已满足

`run_manifest.json` contains (new, C1.1):

- `m_execution_raw_index_path`
- `m_execution_raw_index_hash`
- `positions_reconstruction_raw_index_path`
- `positions_reconstruction_raw_index_hash`

Backward compatibility:

- legacy single-file fields are preserved (no breaking changes)

---

## Index integrity / 索引完整性

Both index files include:

- `version`
- `policy`
- `shards[]` (each with `sha256_16`)
- `total_shards`
- `total_records`

This enables independent verification per shard.


