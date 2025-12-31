# V11 Step 91 — Trade Chain Evidence Extension — SSOT — 2025-12-31

目的：在不破坏 Step88/89 的既有证据链合同前提下（additive-only），扩展“交易链”证据，使每一次真实下单（或被 gate 拒绝的下单）都能被**机器复核**为一个闭环：从意图 → 风控/门禁 → API 调用 → 交易所响应 → 订单状态/成交/账单 → 运行期对账摘要。

本文件只允许追加（additive-only）。

---

## 1) 范围（冻结）

Step91 扩展覆盖：
- **Write-path**：intent → (freeze gate / risk gate) → connector request/response → local attempt record
- **Exchange truth**：orders/fills/bills snapshots（read-only auditor materialization）
- **Reconciliation summary**：本次 run 的最小对账摘要（不要求完整财务报表，但要求可机读解释）

不覆盖：
- 策略收益评估、长期统计、回测框架

---

## 2) 核心 join keys（冻结）

为保证可复核 join，以下字段在证据中必须可定位（可脱敏但需可 join）：
- `run_id`
- `audit_scope_id`（若存在）
- `freeze_id`（若发生冻结拒绝；Step81 join key）
- `client_order_id` / `clOrdId`（写侧主键）
- `ordId`（交易所订单 id，若可得）

约束：
- 不允许用 hash 代替 join 主键作为唯一索引（hash 只能作为辅助字段）

---

## 3) 新增/扩展的证据文件（additive-only）

### 3.1 `order_attempts.jsonl`（扩展字段）

每一次“写操作尝试”（包括被 gate 拒绝）记录一条 attempt。

必须字段（已有/应已有）：
- `ts_utc`
- `run_id`
- `intent_id`（若存在）
- `client_order_id`（clOrdId）
- `operation`（place/cancel/replace）
- `status`（ok/rejected/error）
- `rejected`（bool）
- `l1_classification`（例如 `L1_EXECUTION_FROZEN`）

新增字段（Step91）：
- `gate`：
  - `gate_name`（e.g. `execution_freeze`, `risk_limits`, `connector_write`）
  - `gate_decision`（allow/reject）
  - `gate_reason_code`（vocabulary）
- `connector_call`（如果 gate_allow 才允许存在）：
  - `endpoint`
  - `request_ref`（evidence_refs，指向 request json 记录）
  - `response_ref`（evidence_refs，指向 response json 记录）
- `exchange_ids`：
  - `ordId`（nullable）
  - `tradeIds`（nullable list, if available）

### 3.2 `okx_api_calls.jsonl` / `exchange_api_calls.jsonl`（统一语义）

要求：
- 每一次 HTTP 请求/响应都落地一条 record，并能被 `order_attempts.jsonl.connector_call.*_ref` 解引用。

新增字段（Step91）：
- `call_id`（可作为引用 key）
- `clOrdId`（若请求包含）
- `ordId`（若响应包含）
- `http_status`
- `okx_code` / `exchange_code`

### 3.3 `positions_snapshot.json`（可选但推荐）

在 run_start 与 run_end 至少各写一份 position snapshot（或在 ledger truth 中已有等价文件则复用）。
用于解释“为什么本次 run 没有产生成交/仓位变化”。

### 3.4 `reconciliation_summary.json`（新增）

最小对账摘要（机器可读）：
- `run_id`
- `time_window_utc`（start/end）
- `attempt_counts`（by status/l1_classification）
- `exchange_materialized`：orders/fills/bills 文件是否存在、条数、sha256_16
- `net_position_delta`（若可得）
- `net_cash_delta`（若可得）
- `explainability`：
  - `reason_codes`（如果 delta 不可解释/不可测量）
  - `links`（evidence_refs 指向 supporting records）

---

## 4) 验收（冻结）

### 4.1 Step91 Verifier Gate（新 gate）

在 CI/runner gate 中新增 Step91 verifier（read-only）：
- 对每个 `order_attempts.jsonl` 记录：
  - 若 `gate_decision=reject`：必须有对应 gate evidence（例如 freeze_events + 相关 reason_code）
  - 若 `gate_decision=allow`：必须能解引用到 `exchange_api_calls` 的 request/response，并能从中提取 `clOrdId`（以及可选 `ordId`）
- 对 run 级别：
  - `reconciliation_summary.json` 必须存在，且内部引用可解引用（若声明了 links）

Verdict 规则：
- 缺关键文件/关键字段：FAIL（fail-closed）
- 交易所真值受限导致无法 materialize：允许 NOT_MEASURABLE，但必须给出 reason_codes 且不得宣称“闭环完成”

---

## 5) 交付物（Quant，冻结）

Quant 必须新增一份不可变落地记录（只写 anchors + 结果，不复制 Research 内容）：
- `docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_IMPLEMENTED_IN_QUANT_20251231.md`

最小记录内容：
- code commit SHA
- main HEAD CI run link（若以 CI 为真值）
- Step91 verifier 命令 + exit code
- 示例 attempt 的 clOrdId/ordId join 证明（可脱敏）

---

## 6) 变更记录（追加区）

- 2025-12-31: 创建 Step91 SSOT（交易链证据扩展：attempt→gate→api_call→exchange→reconcile）。


