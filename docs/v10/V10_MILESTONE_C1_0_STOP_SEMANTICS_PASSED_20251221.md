# V10 Milestone: C1.0 STOP Semantics PASSED (Partial C1.0) — 2025-12-21

## What this milestone means / 这意味着什么

**English (primary)**: We can now trigger a safe stop via STOP file and have the run terminate with **auditable interruption semantics**:

- `run_manifest.status = "interrupted"`
- `stop_detected = true`
- `stop_time` and `stop_reason` are written
- full evidence-chain artifacts are still produced (no corruption)

This is a **partial pass** for C1.0: it validates safe-stop integrity, but not the 1-hour duration target.

**中文（辅助）**：我们已验证“可安全中止且证据链不断”的关键能力：STOP 文件触发后，run 以 `interrupted` 结束，并落盘 stop 相关字段；产物齐全。  
但本次并未验证 1 小时长跑（因为 STOP 提前触发）。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251221_165245_9026266`
- **Mode**: `okx_demo_api`
- **Status**: `interrupted`
- **Duration**: `198.11s` (≈ 3m18s)
- **api_calls**: `8`

STOP semantics (from manifest):

- `stop_detected = true`
- `stop_time = 2025-12-21T16:56:03.228288Z`
- `stop_reason = "stop_file"`

Artifacts present (8/8 evidence-chain set):

- `run_manifest.json`
- `okx_rest_alignment_report.json`
- `okx_rest_raw_samples.json`
- `execution_fingerprint.json`
- `multiple_experiments_summary.json`
- `m_execution_raw.json`
- `positions_reconstruction_raw.json`
- `positions_snapshot.json`

---

## Scope boundary / 边界

- PASS here only means: **safe stop is auditable and does not break evidence chain**
- It does **not** mean the 1-hour long-run stress test has passed (duration target not met)


