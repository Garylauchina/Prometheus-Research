# V11 Step 31 — Extend Evidence Verifier to Tier-1 (Ledger + ProbeGating + Errors) — 2025-12-29

目的：把 evidence gate 的“可复核范围”从 Step 26 的输入链（E/MF/Comfort → Decision）扩展到 execution_world 的 **Tier-1 关键证据一致性**：
- `ledger_ticks.jsonl`（truth snapshots）
- `probe_gating_ticks.jsonl`（gating decisions + mask/理由）
- `errors.jsonl`（任何 STOP/冻结/证据失败的 append-only 记录）

核心原则：
- **fail-closed**：缺证据/不一致 = FAIL（不得误报 PASS）。
- **additive-only**：只允许追加检查项；不改旧语义与 exit code。
- **不引入策略执法**：这里验证的是“证据链可复核”，不是“交易正确/收益正确”。

SSOT 关联：
- Step 27（Step26 最小复核清单）：`docs/v11/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
- Step 28（run-end packaging + gate 规格）：`docs/v11/V11_STEP28_EVIDENCE_PACKAGING_GATE_20251229.md`
- Step 29（CI gate）：`docs/v11/V11_STEP29_CI_EVIDENCE_GATE_STEP26_20251229.md`
- Step 30（Quant 已强制接入 run-end gate）：`docs/v11/V11_STEP30_RUN_END_EVIDENCE_GATE_IMPLEMENTED_20251229.md`

---

## 1) 扩展后的必备文件（Tier-1）

在 Step 27 §1 必备文件基础上，新增（缺一即 FAIL）：
- `ledger_ticks.jsonl`
- `probe_gating_ticks.jsonl`

说明：
- 允许某些 run 没有 `order_attempts.jsonl` 等（无下单时），但 **ledger/gating/errors** 属于执行世界最小闭环证据，不应缺席。

---

## 2) 新增最小一致性检查（必须通过）

### 2.1 ledger_ticks 与 probe_gating_ticks 的 tick 对齐

对每个 tick（以 `probe_gating_ticks.jsonl` 为锚）至少要求：
- `tick` 与 `run_id` 一致（或等价锚点一致）
- `truth_profile` 语义一致（degraded_truth/full_truth_pnl）

FAIL 条件：
- gating 引用的 tick 在 ledger 中不存在（或 run_id 不一致）
- 同 tick 的 truth_profile 前后矛盾（manifest/ledger/gating 三者不一致）

### 2.2 gating_decision 与错误记录的关系（写实一致）

要求：
- 若 `probe_gating_ticks.gating_decision == "stop"`：
  - 必须存在对应 `errors.jsonl` 记录（`error_type` 语义等价：`probe_gating_stop` 或 `evidence_gate_failed` 等）
  - 且 manifest `status` 不能写成“completed/pass”（必须写实为 stop/failed）

FAIL 条件：
- gating_stop 发生但 errors.jsonl 缺失（或无任何 stop 解释）
- gating_stop 发生但 manifest 报告为 completed/pass（误报）

### 2.3 mask discipline 与决策纪律（最小）

要求（best-effort，按现有字段）：
- 若某 tick `probe_gating` 显示核心输入维度全部不可用（例如 `available_count==0` 或等价 mask 摘要）：
  - decision_trace 不得产生 open/close（必须 hold/none）

FAIL 条件：
- 全 mask=0 仍出现 open/close（违反 mask discipline）

---

## 3) Verifier 扩展策略（实现建议）

在 Quant 的 `tools/verify_step26_evidence.py` 基础上 **additive** 扩展为：
- 继续保留 Step26 原检查与 exit code（0/1/2）语义不变
- 新增 Tier-1 检查项（ledger/gating/errors）

输出建议：
- 采用分段 `[n/m]` 打印，失败给出明确原因列表（用于 CI 与 run-end gate 的 `fail_reasons`）

---

## 4) Fixture 与 CI Gate 的扩展（最小增量）

CI fixture（Step 29）必须同步扩展以覆盖 Tier-1：
- fixture 目录新增：
  - `ledger_ticks.jsonl`（至少 1 行）
  - `probe_gating_ticks.jsonl`（至少 1 行）
  - `errors.jsonl`（可为空文件；若 fixture 里 gating_decision=stop 则必须包含对应错误记录）

FAIL 条件：
- fixture 不含 Tier-1 文件，导致 CI 不能防未来退化。


