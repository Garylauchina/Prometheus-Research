# V10 C-Stage Protocol: C1.0 Long-Run (1h) Evidence-Chain Stress Test — 2025-12-21

## Purpose / 目的

**English (primary)**: Upgrade from “short smoke runs” to a **controlled 1-hour run** to validate that our C-stage evidence chain remains stable over time:

- artifacts always written
- no silent drift in manifest schema
- no infinite log spam
- can be safely stopped (STOP) without corrupting evidence

**中文（辅助）**：把 C0.x 的短跑升级为可控长跑（1小时），验证：证据链不会随着时间崩坏，且可安全中止与复盘。

---

## Preconditions / 前置条件

- C0.5/G4.5 passed (okx_rest evidence-chain closure)
- C0.7 passed (positions fallback snapshot)
- C0.8 passed (positions raw evidence linked)
- C0.9 passed (M execution raw evidence)

---

## Run configuration / 运行配置

- Mode: `okx_demo_api`
- Duration: **3600 seconds** (1 hour)
- Data plane: OKX demo REST (`execution_alignment_lib=okx_rest`)
- Core invariance: **no changes to `prometheus/v10/core/`**

---

## Required artifacts / 必须产物（RUN_DIR 内）

Must exist:

- `run_manifest.json`
- `multiple_experiments_summary.json`
- `execution_fingerprint.json`
- `okx_rest_alignment_report.json`
- `okx_rest_raw_samples.json`
- `positions_snapshot.json` (may vary over time; must be present at least once if fills evidence exists)
- `positions_reconstruction_raw.json`
- `m_execution_raw.json`

Optional but recommended:

- `perturbations_applied.json` (if chaos/fault injection is enabled later)

---

## Acceptance checks / 验收检查

### A) Evidence continuity / 证据连续性

- `run_manifest.status` ends as `completed` or `interrupted` (STOP), never “silent hang”.
- `api_calls > 0`.
- manifest schema does not regress (required keys remain present).

### B) Honesty markers / 诚实标记

- `execution_alignment_lib == "okx_rest"` (or project-approved equivalent)
- `impedance_fidelity` remains demo-labeled (must not claim live)
- When evidence is missing, record `null + reason` (no fabricated fills/fees).

### C) No log spam / 无刷屏

- After any internal stop/collapse event, logs must not print per tick indefinitely.

### D) Safe stop / 安全中止

- Creating STOP file triggers graceful shutdown:
  - `run_manifest.status="interrupted"`
  - `end_time` set
  - artifacts remain readable

---

## Minimal report back / 最小回传

After the 1-hour run, report:

1) `RUN_DIR` name
2) `ls -la RUN_DIR` summary
3) From `run_manifest.json`:
   - `status`, `mode`, `api_calls`
   - `execution_alignment_lib`
   - `positions_quality`, `positions_source`
   - `impedance_fidelity`
   - paths + hashes for `positions_reconstruction_raw` and `m_execution_raw` (if present)
4) File sizes (bytes) for raw evidence files (to monitor growth)


