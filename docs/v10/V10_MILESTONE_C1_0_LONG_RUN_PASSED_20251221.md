# V10 Milestone: C1.0 Long-Run (1h) Evidence-Chain Stress Test PASSED — 2025-12-21

## What this milestone means / 这意味着什么

**English (primary)**: We completed a **full 1-hour `okx_demo_api` run** with stable, auditable artifacts. This is the first proof that our C-stage evidence chain can survive **long-run execution** (not just short smoke tests).

**中文（辅助）**：我们完成了真正的 1 小时长跑，并且证据链 8件套完整落盘。这证明我们的“事故记录仪”已经具备长期运行的工程可靠性（至少在 demo_proxy 世界里）。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251221_170248_9026266`
- **Mode**: `okx_demo_api`
- **Status**: `completed`
- **Duration**: `3601.85s` (≈ 60.03 minutes)
- **api_calls**: `63` (long-run accumulation)
- **impedance_fidelity**: demo-labeled (`demo_proxy`)

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

## Key observation / 关键观察（为下一步做准备）

Raw evidence growth is now visible at 1-hour scale:

- `m_execution_raw.json` grew to ~31 KB
- `positions_reconstruction_raw.json` grew to ~10 KB

This is expected, but it becomes a scaling concern for multi-hour / multi-day runs.

**Next step (C1.1)** should address **raw evidence growth control** without breaking auditability (rolling windows / sampling / compression / hash+index).


