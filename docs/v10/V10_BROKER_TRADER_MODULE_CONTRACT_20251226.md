# V10 BrokerTrader Module Contract (Execution + Registry) — 2025-12-26

目的：把“执行交易 + 如实入册（exchange JSON）”封装成一个代理交易员模块，作为 `execution_world` 的唯一交易入口。  
核心：BrokerTrader 不发明记账方法，只保证 **可回查 JSON 的事实链完整**，并补充 `agent_id` 归因字段。

---

## 0) 第一性原理（hard）

- **真值**仅来自交易所可回查 JSON（orders / fills / bills / positions / equity）。
- **BrokerTrader 只做两件事**：
  1) **Execute**：接收 Agent 委托（intent）并向交易所发起请求  
  2) **Registry**：把交易所返回的事实按 append-only 入册（落盘 evidence）
- **唯一允许新增字段**：`agent_id`（归因）与 `clOrdId`（本地绑定键）。
- **禁止**：内部模拟成交/费用/仓位；禁止 runner 直接调用底层 connector 进行下单或真值查询（绕过入册）。

**孤儿订单（orphan order）定义（hard）：**

- 交易所可回查到的订单/成交事实，如果在本地入册证据中无法找到**明确归因锚点**（`agent_id_hash` 或 `lifecycle_scope`），则视为孤儿订单/孤儿事件。
- “不能逐个 Agent 强平”本身不会自动产生孤儿；真正的风险来自：强平/撤单/补救订单在入册时缺少归因字段，或绕过 BrokerTrader 导致入册缺失。

---

## 1) 模块边界（hard）

### 1.1 BrokerTrader 对外提供的唯一能力

- **submit_intent(...)**：提交一次委托（open/close/cancel/hold→no-op），并入册 ack 事实
- **confirm_order(...)**：基于 `ordId`/`clOrdId` 对订单状态进行确认（P2），并入册查询事实
- **optional: fetch_fills(...) / fetch_bills(...)**：在需要成交/账务闭环时（P3/P4）拉取并入册
- **execute_lifecycle_flatten(...)（必须，execution_world）**：为生命周期裁决提供“强平/归零仓位”的执行入口，并把所有动作正常入册（见 §4.6）

### 1.2 查询入口（你提的两个入口）

- **Agent 个体查询入口（per-agent）**：
  - 输入：`agent_id`（或 `agent_id_hash`）
  - 输出：该 agent 的订单/成交/账单引用集合（`clOrdId` 列表、对应 `ordId_hash` 列表、相关 evidence 路径）
  - 目的：做生命周期分析与归因时能从 agent 一键回指到交易所事实证据

- **审计整体查询入口（global audit）**：
  - 输出：全局订单确认统计与异常清单（例如 ack 未确认、分页未闭合、truth_quality degraded）
  - 目的：对“通信造成的不一致”给出证据化的分类，而不是靠猜测

> 注：上述“入口”既可以是 Python API，也可以是离线聚合脚本；契约要求的是“能产出可复核结果”，而不是强制实现形态。

---

## 2) 关键主键（hard）

- **本地绑定键**：`clOrdId`（BrokerTrader 生成/验证合规性；绑定 `agent_id`）
- **订单主键**：`ordId`（交易所生成；在本项目中可脱敏为 `ordId_hash`）
- **成交主键**：`tradeId`（若可得）
- **账单行主键**：`billId/id`（以交易所 JSON 为准）；若账单行有 `ordId`，它是强外键但不是账单行主键

---

## 3) 订单确认协议（hard）

BrokerTrader 必须实现并遵守订单确认协议（P0–P5）：

- 协议文档：`docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`
- 最小要求：对所有 ack 的订单必须完成 P2（终态可回查）；否则必须触发 execution freeze（不再发单）并落盘原因。

---

## 3.5) L1 一级分类（execution-time classification, hard）

BrokerTrader 在执行每一笔委托（无论来自决策模块还是审判模块）时，必须对执行过程中出现的问题做 **一级分类（L1）**，并触发预定义动作。  
上游模块只表达意图；**分类与处置由交易员负责**，且必须入册（append-only）。

### L1 taxonomy（冻结词表，additive-only）

- `L1_OK`
  - 定义：ack 成功且能完成 P2（终态可回查）；若做成交/账务结论则完成对应 P3/P4
  - 动作：继续

- `L1_RETRYABLE_TRANSPORT`
  - 定义：可重试传输类问题（timeout/connection_error/rate_limited/5xx 等）
  - 动作：限次重试 + backoff；超阈值 → 记录 `recommended_action=stop_and_ieb`（由 runner 决定是否停止）

- `L1_ACCOUNT_RESTRICTED`
  - 定义：账户受限/风控锁死/权限异常（明确错误码或稳定复现的拒绝）
  - 动作：记录 `recommended_action=stop_and_ieb`（由 runner 决定是否停止）

- `L1_EXCHANGE_REJECTED`
  - 定义：交易所业务拒绝（参数不合法、规则不满足、仓位方向不匹配等，sCode/sMsg 明确）
  - 动作：停止该动作并入册原因；若该动作属于生命周期强平且无法完成“归零敞口”目标 → 记录 `recommended_action=stop_and_ieb`

- `L1_TRUTH_INCOMPLETE`
  - 定义：已发生 ack 或关键动作，但无法在最终一致窗口内完成 P2/P3/P4（回查缺失/分页不闭合/字段缺失）
  - 动作：如实写 `truth_quality=degraded/unknown + reason_code`；记录 `recommended_action=freeze_or_stop`（由 runner 决定）

- `L1_LIQUIDITY_UNAVAILABLE`
  - 定义：在强平/归零敞口目标下，多次尝试仍无法使风险敞口归零（例如无法成交/无法撤单导致无法归零）
  - 动作：记录 `recommended_action=stop_and_ieb`（由 runner 决定是否停止；通常应停止）

### 入册要求（hard）

每次委托尝试（含重试）都必须在入册证据中写入：
- `l1_classification`
- `reason_code`（更细粒度；additive-only）
- `intent_source`：`decision_cycle | lifecycle_judge`
- `lifecycle_scope`（若为生命周期动作，如 `system_flatten`）
- `recommended_action`：`continue | retry_with_backoff | freeze_or_stop | stop_and_ieb`

---

## 3.6) reason_code → L1 最小映射表（frozen, additive-only）

目的：把“执行过程中出现的问题如何一级分型”固定成可复核规则，避免实现时随意分型导致审计口径漂移。  
规则：本表 **只允许新增**（additive-only），不得更改既有条目的语义。

### Transport / infrastructure

| reason_code | map_to_l1 | notes |
|---|---|---|
| `timeout` | `L1_RETRYABLE_TRANSPORT` | request timed out |
| `connection_error` | `L1_RETRYABLE_TRANSPORT` | DNS/TCP/TLS/connect errors |
| `request_exception` | `L1_RETRYABLE_TRANSPORT` | unexpected client exception |
| `rate_limited` | `L1_RETRYABLE_TRANSPORT` | 429 or exchange throttling |
| `http_5xx` | `L1_RETRYABLE_TRANSPORT` | upstream/server errors |

### Account restricted / permissions

| reason_code | map_to_l1 | notes |
|---|---|---|
| `invalid_api_key` | `L1_ACCOUNT_RESTRICTED` | auth rejected |
| `permission_denied` | `L1_ACCOUNT_RESTRICTED` | missing permissions / read-only key used for write |
| `risk_control_locked` | `L1_ACCOUNT_RESTRICTED` | exchange risk control / account locked |
| `account_restricted` | `L1_ACCOUNT_RESTRICTED` | generic restriction |

### Exchange rejected (business rule)

| reason_code | map_to_l1 | notes |
|---|---|---|
| `exchange_rejected` | `L1_EXCHANGE_REJECTED` | generic sCode/sMsg rejection |
| `param_invalid` | `L1_EXCHANGE_REJECTED` | invalid parameter |
| `lot_size_invalid` | `L1_EXCHANGE_REJECTED` | e.g. OKX `sCode=51121` |
| `no_position_to_close` | `L1_EXCHANGE_REJECTED` | e.g. OKX `sCode=51169` |

### Truth incomplete / evidence chain gap

| reason_code | map_to_l1 | notes |
|---|---|---|
| `status_query_failed` | `L1_TRUTH_INCOMPLETE` | cannot complete P2 |
| `fills_query_failed` | `L1_TRUTH_INCOMPLETE` | cannot complete P3 |
| `bills_query_failed` | `L1_TRUTH_INCOMPLETE` | cannot complete P4 |
| `paging_incomplete` | `L1_TRUTH_INCOMPLETE` | cannot prove completeness |
| `field_missing` | `L1_TRUTH_INCOMPLETE` | required fields absent in JSON |

### Liquidity / cannot flatten exposure

| reason_code | map_to_l1 | notes |
|---|---|---|
| `liquidity_unavailable` | `L1_LIQUIDITY_UNAVAILABLE` | cannot reduce exposure despite attempts |
| `flatten_failed_after_max_attempts` | `L1_LIQUIDITY_UNAVAILABLE` | repeated failure at lifecycle flatten |

### Defaulting rule (hard)

- 如果 `reason_code` 未能匹配本表，必须写入：
  - `l1_classification=L1_TRUTH_INCOMPLETE`
  - 并附 `reason_code=unknown_reason_code:<raw>`（保留原始错误摘要，避免吞错）

---

## 4) Evidence（入册文件，append-only）

BrokerTrader 至少写出这些证据文件（runner 不得绕过）：

- `order_attempts.jsonl`：每次提交/撤单请求的 ack 事实（含 `agent_id_hash`、`clOrdId`、`ordId_hash(若有)`、`sCode/sMsg`、HTTP status、latency）
- `order_status_samples.jsonl`：每次订单状态查询返回的事实（append-only，不得只写最终态）

可选（当做出对应结论时必须启用）：

- `fills_query_evidence.jsonl` / `fills_samples.json`：成交事实（P3）
- `account_bills_samples.jsonl`：账务事实（P4）

所有文件必须具备：
- `ts_utc`、`run_id`、`tick`（若在 tick 循环内）
- `truth_quality` 与 `reason_code`（当无法证明完整性时）
- `raw_ref`（指向脱敏 raw 样本或其索引）

---

## 4.5) 周期收尾（runner orchestration, recommended）

推荐的“轮回周期结束”收尾顺序（默认）：

1) BrokerTrader 完成当期入册（确保 P1/P2 证据已落盘，必要时 P3/P4 也已落盘）
2) ExchangeAuditor 对当期 run_dir 做一次只读交叉核验并落盘（不干预系统）：
   - `auditor_report.json`
   - `auditor_discrepancies.jsonl`
3) RunArtifacts 生成/更新 `FILELIST.ls.txt` + `SHA256SUMS.txt`
4) STOP

说明：
- 这属于 runner 编排，不改变 BrokerTrader/ExchangeAuditor 的模块功能；未来可以把步骤 2 改为定期执行。

---

## 4.6) 生命周期强平入口（Lifecycle flatten, execution+registry）

当 LifecycleJudge 在周期末需要执行“死亡/繁殖前强平”（释放保证金、归零风险敞口）时：

- **调用入口**：runner 只能通过 BrokerTrader 的 `execute_lifecycle_flatten(...)` 触发（禁止绕过）。
- **入册要求（hard）**：该强平必须像普通订单一样走 P0–P5，产生完整证据链：
  - `order_attempts.jsonl`（必须）
  - `order_status_samples.jsonl`（必须）
  - 若要对成交/费用下结论，必须落盘 P3/P4

关键约束（现实边界，必须诚实）：
- 在“单账户 + 多 Agent 归因”的执行模式下，交易所层面的仓位通常是**系统级净仓**，不一定能逐 Agent 独立强平。
- 因此本入口的 **scope 默认是 system-level flatten**（把账户在该合约/该产品下的风险敞口归零），并在入册记录中标注：
  - `lifecycle_scope`: `system_flatten`
  - `lifecycle_reason`: `death_or_reproduce_settlement`
  - `agent_id_hash`：可填 `null` 或填触发该轮回的审判上下文（用于归因审查），但不得暗示“交易所层面是该 agent 独占仓位”。

> 如果未来要实现“逐 agent 独立强平”，必须引入可隔离的执行形态（例如子账户/分仓/单 agent 专用账户），并单独立契约。

**重大故障语义（hard）：反复强平失败必须 STOP + 证据保全**

如果 `execute_lifecycle_flatten(...)` 出现“反复执行但持续失败”的情况（无论原因：通信退化、账户风控锁死、交易所异常、黑天鹅流动性枯竭等），都视为重大事件：

- **不得无限重试**：必须有明确的 `max_attempts`（例如 2–3 次）与退避（backoff），且每次尝试都必须入册（P1/P2）。
- **超过阈值即升级**：超过 `max_attempts` 仍无法证明仓位风险敞口已归零（或无法回查到对应订单终态），BrokerTrader 必须记录 `recommended_action=stop_and_ieb`；是否 STOP 由 runner 决定（本版本建议 stop）。
- **失败必须分型落盘**：每次失败都必须写 `truth_quality=degraded/unknown` 并附 `reason_code`（建议词表）：
  - `network_error` / `timeout` / `rate_limited`
  - `account_restricted` / `risk_control_locked`
  - `exchange_rejected`（含 `sCode/sMsg`）
  - `liquidity_unavailable`（无法成交/无法撤单导致无法归零）

> 目的：把“强平失败”从模糊的运行日志，提升为可审计的 incident 证据链，避免继续运行污染后续裁决与基因演化结果。

## 5) Freeze（接口冻结）

BrokerTrader 通过 Gate4/PROBE 后，冻结：

- public 方法签名与语义（submit/confirm/query）
- 入册 evidence schema（上面列出的 json/jsonl）
- error taxonomy（`reason_code` 词表，additive-only）

破坏性变更必须：
- 升级 `contract_version`
- 重新跑最小 PROBE（orders：ack→status→(fills/bills 可选)→hash）


