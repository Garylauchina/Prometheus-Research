# V11 Step 31 — Tier-1 Evidence Verifier Extension (Implemented in Quant) — 2025-12-29

目的：记录 Step 31（扩展 evidence verifier 覆盖 Tier-1：`ledger_ticks`/`probe_gating_ticks`/`errors` 的最小一致性）已在实现仓库（Prometheus-Quant）落地，并冻结其“对外可审计口径”。

SSOT 规格：
- Step 31 Spec：`docs/v10/V11_STEP31_EXTEND_EVIDENCE_VERIFIER_TIER1_20251229.md`

关联（此前已落地）：
- Step 29（CI evidence gate）：`docs/v10/V11_STEP29_CI_EVIDENCE_GATE_STEP26_20251229.md`
- Step 30（run-end gate 强制执行）：`docs/v10/V11_STEP30_RUN_END_EVIDENCE_GATE_IMPLEMENTED_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`8c00f2f`
- message：`v11: extend step26 evidence verifier to tier-1 (ledger/probe_gating/errors), update fixture`

变更概览（实现仓库口径）：
- 扩展 `tools/verify_step26_evidence.py`（additive-only；exit code 语义不变：0/1/2）
- 扩展 CI fixture：`tests/fixtures/step26_min_run_dir/` 新增 `ledger_ticks.jsonl`、`probe_gating_ticks.jsonl`、`errors.jsonl`，并更新 `FILELIST/SHA256SUMS`
- CI gate（Step 29）与 run-end gate（Step 30）由于调用同一 verifier，自动升级覆盖 Tier-1

---

## 2) 冻结的对外口径（最小）

### 2.1 exit code 语义（不变）
- `0` PASS
- `1` FAIL（证据缺口/不一致）
- `2` ERROR（文件缺失/格式错误/不可读）

### 2.2 Tier-1 最小一致性（新增）
- `probe_gating_ticks` ↔ `ledger_ticks`：tick/run_id/truth_profile 对齐，不得矛盾
- `gating_decision=stop` → `errors.jsonl` 必须写实（且 manifest 不得误报 completed/pass）
- mask discipline（best-effort）：full_truth 模式下，全 mask=0 不得 open/close

---

## 3) 影响范围（为什么重要）

Step 31 使 evidence gate 从“输入链可复核”提升到“输入链 + 真值链 + 失败链”最小闭环可复核，主要防止：
- ledger/gating tick 漂移（审计口径断裂）
- stop 发生但无 errors 记录（证据盲区）
- 全 mask=0 仍交易（违反 mask 纪律）


