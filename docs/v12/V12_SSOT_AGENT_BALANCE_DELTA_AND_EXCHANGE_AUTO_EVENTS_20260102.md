# V12 SSOT — Agent Balance Delta + Exchange Auto Events (Truth-First, Event-Driven) — 2026-01-02

目标：以**最小复杂度**支持 V12 的事件驱动生命系统：
- Agent 拥有个体 balance（内部状态），但 Broker 不做逐单“绝对余额”核算
- Broker 只推送 **Δbalance（增量事件）**，Agent 自己做累加
- 交易所自动处置（减仓/强平/资金费/手续费等）必须 **如实落盘**，并可回指交易所真值证据

本文件 additive-only。

---

## 1) Two-layer truth model（冻结）

### 1.1 Account-level truth（交易所真值）

- 来源：交易所接口/回执（REST、private WS、或 auditor materialization）
- 语义：账户总权益/仓位/账单/成交等 **account truth**
- 证据：必须落盘（见 §3）

### 1.2 Agent-level balance（系统内部真值）

- 来源：系统内部账本（Agent 自身状态 + Broker 推送的 Δbalance 事件）
- 语义：用于代谢/繁殖/约束的 **individual state**
- 备注：该 balance **不声称等于**交易所的 USDT 余额；它可被交易所真值事件“校正”，但不是逐单对齐的主路径。

---

## 2) Balance updates are delta events（冻结）

冻结原则：
- Broker 不维护每个 Agent 的“绝对余额真值”
- Broker 只负责发布 **Δbalance events**（增量），并落盘可审计证据
- Agent 侧按幂等规则应用：`balance := balance + delta`

### 2.1 agent_balance_events.jsonl（必须）

文件：`agent_balance_events.jsonl`（append-only）

每条记录最小字段（冻结）：
- `ts_utc`（string）
- `agent_id_hash`（string）
- `event_id`（string，幂等去重键，必须稳定）
- `delta`（number 或 string；推荐 string 以避免精度漂移）
- `currency`（string，例如 `USDT`）
- `source`（enum: `broker_local` | `exchange_truth` | `reconcile`）
- `reason_code`（string）
- `evidence_ref`（object，必须可 join）：
  - `kind`（enum: `order_attempt` | `exchange_api_call` | `fill` | `bill` | `position_snapshot` | `ws_message` | `manual_reconcile`）
  - `ref_id`（string：例如 ordId/billId/call_id/message_id/snapshot_id）
  - `upstream_run_id`（string，optional）

Fail-closed（冻结）：
- 缺失 `event_id` 或 `evidence_ref`：该 run 必须 NOT_MEASURABLE（evidence_incomplete:agent_balance_event）
- `event_id` 冲突但 delta 不一致：verifier 必须 FAIL（不是 NOT_MEASURABLE）

### 2.2 Idempotency rule（冻结）

Agent 应用 Δbalance 的幂等规则（冻结入口）：
- 若 `event_id` 已处理过：必须忽略重复事件（不得重复加减）
- 去重状态建议落盘（可选）：`agent_balance_event_cursor.json`

### 2.3 System balance attribution via Agent-0（冻结，v0）

动机（冻结）：
- 某些账户级真值事件（例如资金费、自动减仓/强平、未知调整）在多 Agent 共享账户时**无法可靠归因**到具体 Agent。
- 为保持实现最小化但可回溯：引入一个“系统收支归因主体（System Agent-0）”。

冻结规则：
- **System Agent-0（保留字）**：
  - 固定 `agent_id_hash = "agent_0_system"`（或其 hash，但必须稳定且跨 run 一致）
  - **不参与演化**：不得进入选择/变异/繁殖/淘汰；仅用于记录系统级收支样本
- 归因口径（冻结）：
  - 若事件无法归因到具体 Agent：生成一条 `agent_balance_events.jsonl` 记录并归因到 Agent-0
  - 该事件必须显式标注为系统级：`attribution_scope="system"`（建议字段；若实现暂不支持，可在 `reason_code` 使用前缀 `system:*` 作为等价替代）
  - 事件仍必须满足幂等与可回指证据（`event_id` + `evidence_ref`）

推荐（冻结入口）：
- `exchange_account_events.jsonl` 记录 account-level truth 事件（billId/fillId/ordId…）
- 同时为 Agent-0 生成对应 Δbalance（`source="exchange_truth"`），以统一“能量/收支”接口，但不污染个体演化归因

---

## 3) Exchange auto events must be recorded（冻结）

动机：交易所会发生“非本系统主动下单”也会改变账户状态的事件（例如强平、ADL、资金费、手续费、自动减仓/平仓）。
这些必须如实落盘，否则演化观测会被“黑箱外力”污染。

### 3.1 exchange_account_events.jsonl（必须）

文件：`exchange_account_events.jsonl`（append-only）

每条记录最小字段（冻结）：
- `ts_utc`
- `account_id_hash`
- `event_id`（幂等；优先使用 billId/fillId/ordId 的稳定组合）
- `event_type`（enum vocabulary，允许追加）：
  - `funding_fee`
  - `trade_fee`
  - `forced_liquidation`
  - `auto_deleveraging`
  - `position_close_auto`
  - `unknown_exchange_adjustment`
- `reason_code`（string）
- `evidence_ref`（同 §2.1 结构，但 `kind` 通常为 `bill` / `fill` / `position_snapshot` / `ws_message`）

### 3.2 Source of truth（冻结入口）

允许的数据来源（按优先级，从可实现到更实时）：
1) REST 周期性快照/对账：`positions` + `bills/fills` materialization
2) Private WS（未来）：账户/订单/成交/仓位事件推送

重要（冻结）：
- public WS（行情）不承担账户事件真值；自动处置属于账户私有真值。

### 3.3 Phase 3 — Settlement materialization (fills/bills → events)（冻结，v0）

目的（冻结）：
- 将“账户级真值（fills/bills/position snapshots）”物化为两类事件流：
  - `exchange_account_events.jsonl`（account truth）
  - `agent_balance_events.jsonl`（Agent 侧可消费的 Δbalance）
- 形成可机验闭环：truth evidence → events → join verification → manifest verdict 一致。

冻结输出（v0 最小集合）：
- `fills.jsonl`（strict JSONL）
- `bills.jsonl`（strict JSONL）
- `exchange_account_events.jsonl`（strict JSONL）
- `agent_balance_events.jsonl`（strict JSONL；允许 append）
- `run_manifest.json`（必须写入 verifier 结果：`verdict` + `join_verification`）

事件生成规则（冻结）：
- **禁止在系统内“自算费用/资金费/强平损益”当真值**：必须来自 `bills/fills` 或 position snapshots 的交易所字段。
- `exchange_account_events.jsonl`：
  - 每条必须回指真值证据：`evidence_ref.kind in {"bill","fill","position_snapshot"}` 且 `ref_id` 为对应主键（例如 billId/fillId/snapshot_id）
  - `event_id` 必须稳定且幂等（冻结入口推荐）：
    - bill 驱动：`event_id = "okx:bill:" + billId`
    - fill 驱动：`event_id = "okx:fill:" + fillId`（若 exchange 不提供 fillId，可用稳定组合键替代）
- `agent_balance_events.jsonl`（source=`exchange_truth`）：
  - 默认从 **bill truth** 派生 Δbalance（冻结入口）：`evidence_ref.kind="bill"`, `ref_id=billId`
  - `event_id` 必须稳定且幂等（冻结入口推荐）：`event_id = "okx:bill_delta:" + billId`

归因规则（冻结，v0）：
- 若 bill/fill 可明确 join 到某个 `client_order_id/clOrdId` 且该 order attempt 有明确 `agent_id_hash`：
  - 允许生成该 Agent 的 Δbalance 事件（`agent_balance_events.jsonl.agent_id_hash=...`）
- 若无法可靠归因到具体 Agent（例如资金费、强平/ADL、未知调整、或 join 断裂）：
  - 必须归因到 **System Agent-0**：`agent_id_hash="agent_0_system"`（见 §2.3）
  - 且必须显式标注系统级（`attribution_scope="system"` 或 `reason_code` 前缀 `system:*`）
- Funding fee（冻结，v0）：
  - 初期视为系统级 account event：必须落在 `exchange_account_events.jsonl.event_type="funding_fee"`；
  - 归因到 Agent-0（system），**不得**在 v0 自动分摊到个体 Agent。

Fail-closed（冻结）：
- `fills.jsonl` / `bills.jsonl` 任一缺失或非 strict JSONL：该 run 必须 NOT_MEASURABLE（evidence_incomplete:settlement_truth）
- 生成的 events 若出现 `event_id` 冲突但内容不一致：verifier 必须 FAIL
- manifest 若出现 `join_verification.*.verified=false` 但 `verdict="PASS"`：verifier 必须 FAIL 并覆盖为一致结果

---

## 4) Join keys（冻结）

必须可 join 的最小闭环（冻结入口）：
- `agent_balance_events.jsonl.evidence_ref` 必须能 join 到：
  - `order_attempts.jsonl`（若 kind=order_attempt）
  - `exchange_api_calls.jsonl`（若 kind=exchange_api_call）
  - `bills.jsonl` / `fills.jsonl`（若 kind=bill/fill）
  - `okx_ws_messages.jsonl`（若 kind=ws_message，通常是 private WS）
- `exchange_account_events.jsonl` 必须能 join 到 bills/fills/position snapshots 或 private WS message。

---

## 5) Verdict discipline（冻结入口）

对 balance/账户事件相关证据的 verdict 语义（补充）：
- `PASS`：证据链可回放、event_id 幂等、evidence_ref 可 join、且缺测被正确标为 NOT_MEASURABLE
- `NOT_MEASURABLE`：因数据源不可用/无推送/窗口不足导致无法测量（必须有 reason_code）
- `FAIL`：证据不一致（重复 event_id 不同 delta）、或引用不可 join

---

## 6) Cross-links（只读）

- Epoch constitution: `docs/v12/V12_SSOT_EPOCH_CONSTITUTION_20260102.md`
- Uplink/Downlink evidence: `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`
- DSM SSOT: `docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`


