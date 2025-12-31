# V11 Note — Leverage Preference → Decision → Trader Input → Exchange Truth Binding (First Flight) — 2025-12-31

目的：冻结一个最基本但长期被忽略的 execution_world 事实：**Agent 基因存在“杠杆偏好/杠杆上限”并不等于交易所实际使用了该杠杆**。  
First Flight 阶段必须把“杠杆”变成 **可机核验的执行链证据**，否则任何“行为/演化解释”都不可信。

本文件只允许追加（additive-only）。

---

## 1) Scope（冻结）

覆盖：
- OKX demo/live execution_world
- First Flight / Real Flight
- Decision 输出字段（decision_trace）
- Trader 输入字段（order_attempts / api_calls）
- 交易所真值回查（orders_history/positions 或 set-leverage API call evidence）

不覆盖：
- 杠杆偏好如何参与收益/风险模型（策略层问题，先不争论）

---

## 2) Hard Requirements（冻结）

### 2.1 Decision 输出必须包含 leverage（必做）

当 Agent 产生任何“会触达交易所写路径”的 intent（open/close/modify）时，必须在决策证据中写入：
- `leverage_target`（number 或 string，建议明确为数值）
- `leverage_source`（枚举建议：`genome_preference` / `override_first_flight` / `fixed_default`）
- `leverage_reason_code`（例如：`genome_leverage_appetite` / `risk_cap` / `exchange_limit_cap`）

最低要求：即使当前实现暂时不支持 set-leverage，也必须把 `leverage_target` 写出来（否则无法审计“杠杆偏好是否被使用/被忽略”）。

### 2.1.1 Decision 输出的“订单参数对齐”最小集合（冻结）

我们不要求 Decision 直接产出 OKX 原始 payload，但要求 Decision 输出必须**可映射**为交易所可接受的下单参数集合（否则会出现“缺字段→交易所默认值→不可审计”的问题）。

当 intent 会触达写路径（open/close/modify）时，决策证据（`decision_trace.jsonl` 的 agent_detail 或等价可 join 记录）必须包含至少：
- `inst_id`（例如 `BTC-USDT-SWAP`）
- `td_mode`（cross/isolated；与账户模式一致）
- `pos_side`（long/short/net；与持仓模式一致）
- `order_type`（market/limit）
- `requested_sz`（合约张数；非 BTC 数量）
- `limit_px`（仅当 order_type=limit 时必填；market 时必须为 null）
- `leverage_target` + `leverage_source` + `leverage_reason_code`

若某字段在该 intent 下不适用（例如 market 无 px）：必须写 null；不得伪造为 0。

### 2.2 Trader 输入必须包含 leverage（必做）

当 BrokerTrader 生成任何写请求（place/cancel/replace/flatten）时，必须在交易链入册中写入：
- `leverage_target`（与 decision 输出一致，允许被裁剪但必须写明原因）
- `leverage_applied`（bool：是否已对交易所生效；若未知则写 `null` 并给出 reason_code）

建议落盘位置（additive-only）：
- `order_attempts.jsonl`：每条 attempt 附带 leverage 字段（join-first）
- `okx_api_calls.jsonl`（或 Step91 的 `exchange_api_calls.jsonl`）：若发生 set-leverage / 修改杠杆请求，必须落盘 endpoint + params + response

### 2.3 Exchange Truth 必须可核验（必做）

First Flight 的“杠杆”采信必须满足至少一条：
- A) 存在 **set-leverage**（或等价）API call 的落盘证据（request+response，含 http_status + sCode/sMsg），且能 join 到 run_id
- B) 能从交易所真值回查当前杠杆（例如 positions snapshot 里有 lever/leveraged field），并能 join 到该 run 的时间窗/inst_id/posSide

若两条都不满足：必须 NOT_MEASURABLE，并写入错误篓子（Step96，reason_code 建议：`missing_leverage_truth`）。

---

## 3) First Flight Gate（冻结）

进入下一阶段前必须通过：
- decision_trace 中存在 `leverage_target`（对产生写 intent 的 tick）
- order_attempts / api_calls 中存在 `leverage_target`
- truth 侧能证明 leverage 已应用或明确 NOT_MEASURABLE（不得沉默）

---

## 4) Rationale（简述）

杠杆是 execution_world 的一等风险/敞口事实。  
如果“基因里有杠杆偏好”但执行链路从未把它写入交易所（或从未证明写入），那我们观测到的演化行为无法归因，等价于“核心信号丢失”。

---

## 5) Change Log（追加区）

- 2025-12-31: 创建本 note，冻结 First Flight 阶段的 leverage truth binding 最小要求。


