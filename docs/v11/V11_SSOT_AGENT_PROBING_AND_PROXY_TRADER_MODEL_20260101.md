# V11 SSOT — Agent Probing Model + Proxy Trader (BrokerTrader) Contract — 2026-01-01

目的：重新冻结“建模与职责边界”，让 V11 的交易系统以**试探（probing）**为核心：  
Agent 不理解交易规则，只提出订单参数；系统的 Proxy Trader（BrokerTrader）负责资源门禁、真实执行与真值落盘（成功与否不背锅，但必须可审计）。

本文件只允许追加（additive-only）。

---

## 1) 角色与职责（冻结）

### 1.1 Agent / DecisionEngine（只试探）

Agent 的唯一动作：向系统提交一个“下单请求”（order proposal / intent），其内容等价于交易所下单接口可接受的参数集合（见 §2）。

硬边界（hard）：
- Agent **不需要**理解合约规则、最小下单单位、杠杆上限、保证金计算等；这些都不属于 Agent 的职责。
- Agent 的输出只被视为“试探提案”，并不保证可执行、更不保证成交。

### 1.2 Proxy Trader（BrokerTrader：唯一交易入口）

Proxy Trader 必须做且只做三件事：
1) **资源门禁（gate）**：判断是否超出 Agent 可用资源 / 风控约束（见 §3）  
2) **真实执行（exchange write）**：allow 才能触发写请求；拿到回执（ack/ordId 等）  
3) **真值落盘（append-only evidence）**：无论成功/失败都要完整记录本地 attempt + 交易所返回（或错误）

硬边界（hard）：
- Proxy Trader **不负责“结果好坏”**：不保证成交、不保证盈利；但必须保证“发生了什么”可回放可审计。
- 任何 reject 都必须可解释（reason_code），任何 allow 都必须可追踪（refs + join keys）。

---

## 2) Agent → Proxy Trader 的“下单提案”参数集合（冻结）

原则：只对齐“交易所能接受的参数”，不对齐“交易所会接受的规则”。

当提案会触达写路径时（place/replace），最小字段集合（语义冻结；字段名允许实现差异）：
- `inst_id`（例如 `BTC-USDT-SWAP`）
- `td_mode`（`cross` / `isolated`）
- `pos_side`（`long` / `short` / `net`）
- `order_type`（`market` / `limit`）
- `requested_sz`（合约张数；对 OKX U 本位永续：张数与面值/ctVal 的换算关系应可追溯）
- `limit_px`（仅当 limit 时必填；market 时必须为 null）
- `leverage_target`（必填；不得沉默。其来源可来自 genome：leverage preference）

说明：
- 这不是“能成交/能开仓”的保证；只是“参数齐全、可被 gate 判定”的输入形态。

---

## 3) Proxy Trader Gate：两层门禁（冻结）

### 3.1 Agent Resource Gate（必须存在，fail-closed）

定义：只判断“是否超出该 Agent 被允许消耗的资源”，不判断市场对错。

最小覆盖面（必须至少包含）：
- **资金/保证金可用性**：`insufficient_equity` / `margin_insufficient`
- **持仓/风险上限**（按 Agent 配额或风控策略）：`risk_cap_exceeded`
- **订单频率/数量配额**（按 Agent）：`agent_rate_limited` / `agent_order_quota_exceeded`

如果缺少关键真值导致无法判断（例如 equity/positions unknown）：
- 必须按 truth_profile 进入 **NOT_MEASURABLE 或 reject**，不得默认 allow。

### 3.2 System Ecology Gate（必须存在，防系统自毁）

定义：保护系统与交易所生态的硬限制（即使 Agent 资源足够也可能被系统拒绝）。

示例（冻结为“必须有对应 reason_code”，具体阈值可后续追加版本化）：
- 交易所限速/风控压力：`exchange_rate_limited` / `too_many_requests`
- 未成交挂单上限/产品维度挂单上限：`exchange_order_limit_reached`
- 运行期冻结（Step74–84/Step96）：`execution_frozen`

---

## 4) Evidence：allow/reject 都必须可机验（冻结）

落盘最小要求（与 Step91 对齐）：
- 每一次提案处理必须写一条 `order_attempts.jsonl`：
  - `gate_name`、`gate_decision`（allow/reject）、`gate_reason_code`
  - allow 才允许写 `connector_call` refs，并落 `okx_api_calls.jsonl`
- join keys 必须可用：
  - `client_order_id`/`clOrdId`（写侧主键）
  - `ordId`（若交易所返回/后续可查得）
- 若成交：必须 materialize `orders_history.jsonl`；filled 则 `fills.jsonl`/`bills.jsonl` 必须存在且可 join（truth-first）

---

## 5) 对“只限制一种产品（BTC/USDT 永续）”的解释（非强制）

产品限制与否属于“系统实现复杂度选择”，不改变本模型的契约：  
无论限制 1 个产品还是 N 个产品，Agent 都只是试探，Proxy Trader 都必须 gate + 执行 + 真值落盘。

---

## 6) 与现有 SSOT 的关系（入口）

- Execution World 分层与 hard rules：`docs/v11/V11_DESIGN_EXECUTION_WORLD_20251227.md`
- 交易链证据扩展（order_attempts/api_calls/join）：`docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_20251231.md`
- 杠杆真值绑定：`docs/v11/V11_NOTE_LEVERAGE_PREFERENCE_TRUTH_BINDING_20251231.md`
- 错误篓子（NOT_MEASURABLE/分类/vocab）：`docs/v11/V11_STEP96_EXCHANGE_ERROR_BASKET_20251231.md`


