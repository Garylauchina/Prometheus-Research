---
title: V10 Reconciliation Module Contract (OKX Execution World)
version: "2025-12-23.1"
scope_repo: Prometheus-Research
owner: Architect AI
status: active
---

# V10 对账模块合同（OKX 执行世界：demo/live）

> 本文件定义 **Reconciliation（对账）模块**的接口、证据与失败语义。  
> 适用范围：`okx_demo_api` / `okx_live`（执行世界）。  
> 原则：**交易所为真值**；不一致必须可回溯；不得静默“修平”。

---

## 1) 模块边界（Hard Scope）

### 1.1 对账模块负责

- 周期开始生成交易所快照（Exchange Snapshot）
- 输出对账事件（Reconciliation Event）
- 对账不一致必须附带：`reason_codes` + `evidence_refs`
- 默认模式：`observe_only`（记录差异，不改内部账本）

### 1.2 对账模块不负责

- Agent 决策（不得为了“对账一致”去干预交易）
- 伪造成交/伪造 fills（对账不能制造证据）
- 改写 core 账本语义（除非另立版本合同）

---

## 2) 真值与语义（Hard Semantics）

### 2.1 真值来源

- `exchange_equity`（交易所权益）为真值观测：`totalEq` 或 `USDT.eq`（必须记录 `field_used`）

### 2.2 不一致的定义

\[
\Delta = exchange\_equity - internal\_current\_total
\]

其中：

- `internal_current_total = allocated_capital + system_reserve`（内部账本可审计三元组）

若 \(|\Delta| > tolerance\)，必须写入对账事件（见 §3.2），不得静默吞掉。

### 2.3 默认行为：observe-only

在 `observe_only` 模式：

- 只记录 \(\Delta\) 与解释证据
- **不得**通过 `system_reserve = exchange_equity - allocated_capital` 来“制造闭合”

> 说明：只有在具备 fills/fees 等证据闭环时，才允许引入“强一致修正”模式（需另立版本/合同）。

---

## 3) 输出工件（Artifacts Contract）

### 3.1 `exchange_snapshots.jsonl`（必需，append-only）

每个交易周期开始必须追加 1 条记录。

最小 schema（字段必须存在，允许为 null 但必须给 reason）：

- `ts_utc`（ISO8601）
- `tick_id`（int）
- `mode`（okx_demo_api / okx_live）
- `inst_id`（string）
- `contract_version`（string；必须与本文 front-matter 的 `version` 一致）
- `exchange_equity`（float）
- `exchange_equity_field_used`（"totalEq" / "USDT.eq" / other）
- `balances_min`（对象；至少包含 `USDT` 的 `eq/availEq/frozenBal/upl`）
- `positions_min`（数组；每项至少含 `instId/posSide/pos/availPos/avgPx/lever/upl`）
- `open_orders_min`（对象或数组；若未实现，必须为 `null` 且写 `open_orders_reason`）
- `snapshot_hash_16`（可选；对该条记录内容 sha256[:16]）

### 3.2 `capital_reconciliation_events.jsonl`（必需，append-only）

每个周期至少追加 1 条记录（或在 delta 超阈值时追加；推荐每周期一条，保证可回溯连续性）。

最小 schema：

- `ts_utc`
- `tick_id`
- `contract_version`（string；必须与本文 front-matter 的 `version` 一致）
- `reconciliation_mode`：`"observe_only"`（默认）
- `exchange_equity`
- `internal_current_total`
- `allocated_capital`
- `system_reserve`
- `delta`（exchange - internal）
- `tolerance`
- `reason_codes`（数组，至少 1 项）
- `evidence_refs`（数组，至少 1 项；每项为 `{file, record_selector, sha256_16}`）

### 3.3 reason_codes 词表（最小集）

必须使用以下之一（可扩展，但需版本化）：

- `consistent_within_tolerance`（当 \(|\Delta| <= tolerance\) 时允许使用；表示“本周期差异在容忍范围内”）
- `open_positions_present`
- `open_orders_present`
- `fills_missing`
- `fees_unaccounted`
- `preflight_not_flattened`
- `exchange_unreachable`
- `unknown_unexplained`

当使用 `unknown_unexplained` 时，必须触发降级/告警（见 §4）。

---

## 4) 降级/告警语义（Hard Semantics）

当 `reason_codes` 包含 `unknown_unexplained`：

- 必须进入降级：
  - 暂停下单（ops-only），继续产出 snapshots/events
  - 或人工 STOP（产出 IEB）
- 不得继续在不可信输入上让 Agent 决策。

---

## 5) 接口冻结（Interface Freeze）

对账模块验收通过后：

- `exchange_snapshots.jsonl` 与 `capital_reconciliation_events.jsonl` 的 schema **必须冻结**
- 允许向后兼容扩展：只能新增字段，不得更改字段含义/类型，不得删除字段
- 如需破坏性变更：必须提升 `contract_version` 并重做 Gate 4 对账回归证据包


