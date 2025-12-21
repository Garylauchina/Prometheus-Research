# V10 Milestone: C0.5 / G4.5 Evidence-Chain Closure (OKX REST, okx_demo_api) — 2025-12-21

## What this milestone means / 这意味着什么

**English (primary)**: We have a **completed, auditable `okx_demo_api` run** where:

- `api_calls > 0` (real demo API interaction, not simulation)
- `run_manifest.json` truthfully declares execution library = **`okx_rest`**
- a sanitized **execution-alignment evidence bundle** exists and is referenced by manifest:
  - `okx_rest_alignment_report.json`
  - `okx_rest_raw_samples.json`
- CCXT evidence is **not faked**: `ccxt_*` fields are `null` with a clear skip reason

This closes the **C-stage evidence-chain entry gate** without claiming “CCXT alignment passed”.

**中文（辅助）**：这意味着我们已经跑通了 C阶段的“证据链闭环起点”——真实连接 OKX demo（`api_calls>0`），并且以**诚实口径**落盘了对齐证据包（OKX REST 版），没有伪装 CCXT 对齐通过。

---

## Evidence / 证据（最小可复核信息）

- **Run ID (host volumes)**: `run_20251221_150526_bf82b23`
- **Mode**: `okx_demo_api`
- **Status**: `completed`
- **api_calls**: `15` (must be > 0 for `okx_demo_api`)

**Artifacts present** (in the run directory):

- `run_manifest.json`
- `execution_fingerprint.json`
- `multiple_experiments_summary.json`
- `okx_rest_alignment_report.json`
- `okx_rest_raw_samples.json`

**Truth markers (manifest)**:

- `execution_alignment_lib = "okx_rest"`
- `execution_alignment_ok = true`
- `ccxt_alignment_ok = null`
- `ccxt_alignment_skipped_reason = "ccxt_not_installed_using_okx_rest_evidence"`
- `positions_quality = "unreliable"` (demo expected)
- `positions_source = "inferred"` (fallback strategy marker)
- `impedance_fidelity = "simulated"` (demo expected)

---

## Scope boundary / 边界

- This milestone validates **artifact integrity and honesty**, not profitability.
- It does **not** imply that OKX demo positions/trade fields are fully reliable.
- It does **not** replace Gate 1–3 (A/B2 + ablations) conclusions; it is a **C-stage migration license step** only.


