# V11 Step 92 — Metabolism ↔ TradeChain Alignment — SSOT — 2025-12-31

目的：在不改变既有合同语义的前提下（additive-only），把 **Step72/73 的 metabolism 可观测证据** 与 **Step91 的交易链证据扩展** 做一次最小对齐，形成“资源消耗 ↔ 写侧行为 ↔ 真值物化”的可机读关联点。

本文件只允许追加（additive-only）。

---

## 1) Scope（冻结）

Step92 只做“对齐/引用”，不做：
- 新的交易策略能力
- 新的对账逻辑
- 修改 Step72/73 或 Step91 的既有字段含义

---

## 2) Inputs（冻结）

本 Step 依赖以下既有产物（若文件名不同，以 Quant 实际输出为准，但语义必须等价）：
- Step72/73 metabolism evidence：`agent_metabolism_summary.json`（以及其 entry/index 引用）
- Step91 trade chain evidence：`order_attempts.jsonl`、`exchange_api_calls.jsonl`（或 `okx_api_calls.jsonl`）、`reconciliation_summary.json`

---

## 3) Alignment Contract（冻结）

### 3.1 `reconciliation_summary.json`（Step91）增加可选字段（additive-only）

在 `reconciliation_summary.json` 顶层新增：
- `metabolism_alignment`：
  - `metabolism_summary_ref`：evidence_refs（指向 `agent_metabolism_summary.json`）
  - `metabolism_window`：{`start_ts_utc`, `end_ts_utc`}（与 reconciliation 窗口一致或可解释）
  - `attempt_resource_join`（可选统计）：
    - `attempt_count_total`
    - `resource_cpu_time_ms_total`（若 metabolism 中提供）
    - `resource_api_calls_total`（若 metabolism 中提供）
    - `notes`（可选）

约束：
- 该字段 **可缺省**，但一旦存在，必须可解引用且时间窗口一致/可解释。

### 3.2 `agent_metabolism_summary.json`（Step72/73）不做任何改动

Step92 不允许为了对齐而修改 Step72/73 的既有 schema；只能在 Step91 的 summary 中添加引用。

---

## 4) Acceptance（冻结）

新增 Step92 verifier gate（read-only）：
- 若 `reconciliation_summary.json.metabolism_alignment` 存在：
  - `metabolism_summary_ref` 必须可解引用
  - `metabolism_window` 必须与 `reconciliation_summary.time_window_utc` 一致（或给出 reason_codes/notes）
  - 统计字段存在时必须类型正确、不可为 NaN

Verdict 规则：
- 引用存在但不可解引用 / 时间窗口矛盾不可解释：FAIL（fail-closed）
- 未提供 alignment 字段：PASS（Step92 未启用，不阻断）

---

## 5) Quant Deliverable（冻结）

Quant 侧落地记录（不可变）：
- `docs/v11/V11_STEP92_METABOLISM_TRADECHAIN_ALIGNMENT_IMPLEMENTED_IN_QUANT_20251231.md`

最小内容：
- code commit SHA
- Step92 verifier 命令 + exit code
- 示例 run_dir：`reconciliation_summary.json` 中 `metabolism_alignment.metabolism_summary_ref` 可解引用证明

---

## 6) Change Log（追加区）

- 2025-12-31: 创建 Step92 SSOT（以 Step91 summary 引用方式对齐 Step72/73 metabolism）。


