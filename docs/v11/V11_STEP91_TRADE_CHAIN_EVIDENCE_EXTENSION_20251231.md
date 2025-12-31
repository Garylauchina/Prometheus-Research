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

归因锚点（hard，冻结）：
- attempt 必须能归因到 **agent** 或 **system** 二者之一（不得都为空）：
  - `agent_id_hash`（agent scope；系统级动作必须为 null）
  - `lifecycle_scope`（system scope，例如 `system_flatten`/`startup_flatten`；agent 行为必须为 null）
- `intent_source`（推荐）：例如 `decision_cycle` / `lifecycle` / `preflight`（用于避免自检单冒充 agent 行为）

写路径参数透传（hard，冻结：Trader input 必须包含 Decision 输出参数）
- 当 attempt 对应“下单/改单”等会触达交易所写路径的 intent（尤其 operation=place/replace）时，`order_attempts.jsonl` 必须包含至少以下字段（字段名允许实现差异，但语义必须等价）：
  - `inst_id`
  - `td_mode`（cross/isolated）
  - `pos_side`（long/short/net；与持仓模式一致）
  - `order_type`（market/limit）
  - `requested_sz`（合约张数；与 ctVal/合约面值换算关系必须可追溯）
  - `limit_px`（仅当 order_type=limit 时必填；market 时必须为 null）
  - `leverage_target`（必填；不得沉默）
  - `leverage_applied`（bool|null；未知必须为 null+reason_code，见 Step leverage truth binding）

说明：
- 交易员（BrokerTrader）职责是“如实记录 + 可审计可回溯”，不要求成功成交；但写路径参数缺失会直接导致交易所使用默认值（不可审计），因此必须冻结为必含字段。

补充：写路径“正确性”判断（资金/保证金/限制）由 gate 负责（冻结）
- DecisionEngine/神经网络不负责判断订单是否“可执行”（例如是否超出可用资金/保证金）；它只负责输出可执行参数集合。
- BrokerTrader 必须在写请求前执行 `risk_limits`（或等价）gate：
  - 允许（allow）：才允许写 connector_call，并向交易所发请求
  - 拒绝（reject）：不得发请求；必须落盘 attempt（status=rejected）并给出 `gate_reason_code`（例如 `insufficient_equity`/`margin_insufficient`/`risk_cap_exceeded` 等 vocabulary）
- 若 Ledger/equity/positions 真值缺失导致无法判断：必须按 truth_profile 进入 NOT_MEASURABLE 或拒绝，并写 Step96（classification=LOCAL_GATE_REJECTED 或 TRUTH_*，按实际原因）

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


