# V12 SSOT — Downlink Subscription Manager (DSM) / 下行订阅管理角色 — 2026-01-01

目标：在 V12 的“双管道”信息流中，为 **下行（Exchange→System）** 明确设立一个独立角色，负责订阅、连接管理、事件标准化与二级订阅（internal pub/sub），并保证证据可回放、可审计、fail-closed。

本文件 additive-only。

---

## 1) 为什么需要 DSM（冻结）

在上行我们已经有 Broker（Agent→Broker→Exchange）。下行如果让每个 Agent 直接对接交易所订阅，会导致：
- 连接数量爆炸（限速/断连/资源不可控）
- 不同 Agent 看到的数据不一致（时序/丢包/订阅时刻差异）
- 无法形成可回放的“决策所见市场”证据链

因此，下行必须有 **DSM（Downlink Subscription Manager）**：
- 统一维护少量共享 WS 连接（按 inst_id/topic 维度）
- 把原始推送落盘并映射到 canonical schema
- 在系统内部提供二级订阅（internal pub/sub）给 Agent

---

## 2) 角色定义（冻结）

### 2.1 DSM 的职责（必须做）

1) **连接管理**：建立/维持/重连 OKX public WS（以及未来 private WS 的扩展）
2) **订阅编排**：按系统配置订阅 channels（例如 tickers/books/trades/mark/index/funding），并记录订阅请求与回执
3) **消息接收与落盘**：原始消息流 append-only 落盘（用于可回放审计）
4) **标准化（canonicalization）**：
   - 将 WS 消息映射为 canonical `market_snapshot`/`market_event`（mask/quality/reason_code 纪律）
5) **二级订阅（internal pub/sub）**：
   - Agent 在系统层面订阅 DSM 的 topic（不是交易所通道）
6) **可用性判定（fail-closed）**：
   - 断连/无推送/订阅失败必须显式 NOT_MEASURABLE，并落 reason_code

### 2.2 DSM 不负责的事（硬边界）

- 不做交易决策、不做策略推断
- 不对上行下单负责（那是 Broker 的职责）
- 不“修正市场真相”：只记录/投影，不得伪造 0 或补全缺失

---

## 3) 两级订阅模型（冻结）

### 3.1 一级订阅（Exchange WS）

- 系统只维护少量共享连接
- 订阅以 `inst_id=BTC-USDT-SWAP` 为中心（v0 约束）

### 3.2 二级订阅（System internal pub/sub）

Agent 订阅系统 topic，例如（示例，不冻结命名）：
- `E.tickers.BTC-USDT-SWAP`
- `E.booksL1.BTC-USDT-SWAP`
- `E.mark_px.BTC-USDT-SWAP`

硬规则：
- Agent 的订阅必须被记录（可审计）
- Decision 输出必须能引用“消费了哪个 snapshot/event”（可 join）

---

## 4) Evidence files（冻结）

下行（WS）必须落盘：
- `okx_ws_sessions.jsonl`：连接建立/断开/重连、ws_url、mode、conn_id（若可得）、reason_code
- `okx_ws_requests.jsonl`：subscribe/unsubscribe 原始 JSON（含 id/op/args）
- `okx_ws_messages.jsonl`：每条推送/回执原始 JSON（含接收时间）

标准化产物（canonical）：
- `market_snapshot.jsonl`（与 V12 Scanner schema 对齐）
- （未来可选）`market_events.jsonl`：事件流粒度（比 snapshot 更细），用于真正 event-driven

二级订阅证据（系统内）：
- `agent_subscriptions.jsonl`：
  - `ts_utc`
  - `agent_id_hash`
  - `topics`（array）
  - `action`（subscribe/unsubscribe）

Join 锚点（冻结入口）：
- Decision/Trader evidence 中必须能引用：
  - `snapshot_id`（或未来 `market_event_ref`）

---

## 5) 与 v0/v0.5/v1 的关系（冻结）

- v0：允许仅 REST 快照（DSM 可未实现），但 canonical schema 先验收跑通
- v0.5：DSM 上线（WS ingestion only），落盘 WS 证据，并映射到 `market_snapshot.jsonl`（仍可 tick 消费）
- v1：Decision 真正 event-driven（消费 `market_events` 或更高频 snapshot），新陈代谢/繁殖触发也可以基于事件流

---

## 5.1) Status: capability sealed（封存状态，additive-only）

当前策略（临时决策，冻结入口）：
- DSM 已作为独立能力模块完成“功能验收闭环”（连接/订阅/落盘/canonical/replayability/verifier）。
- **但 DSM 暂不作为系统主线依赖**：主线可先使用 tick + REST snapshot（或低频 canonical snapshot）推进生命系统（代谢 v0）与建模/对齐工作。
- DSM 的“并入系统”需要长期稳定测试通过（见下节 integration gate）。

---

## 5.2) Integration gate: long-run stability（并入门槛：长期稳定测试，冻结入口）

动机：
- DSM 一旦并入系统，会横向影响：Decision、Broker、Settlement、Metabolism、Auditor 的时序与证据 join。
- 因此短时“能跑通”不足以作为并入标准；必须证明长期稳定性与可回放性。

并入门槛（建议口径，v0，冻结入口）：

- **Long-run availability**：
  - 连续运行 ≥ N 小时（N 由实验要求设定），连接断开/重连必须可见（落盘 sessions + reason_code），不得静默。
- **Subscription integrity**：
  - 订阅集合在运行期间保持一致；任何丢订阅/无推送超时必须 NOT_MEASURABLE 可见。
- **Replayability**：
  - 任意窗口的 `market_snapshot.jsonl` 必须能回指 `okx_ws_messages.jsonl`（`source_message_ids` 可解析），并可由 verifier 重放验证。
- **Verdict discipline**：
  - `run_manifest.json.verdict` 与 verifier 输出一致；若存在 `not_measurable:*`，必须 NOT_MEASURABLE（禁止假 PASS）。

## 7) DSM v0.5+ implementation reference (additive-only, frozen semantics)

目的：
- 记录 DSM 在 v0.5→v0.9.1 的“已验证实现要点”，作为后续扩展（v1 event-driven / internal pubsub）的稳定基底。
- 本节只追加事实与冻结语义，不替代上文。

### 7.1 Evidence join anchor for WS（冻结）

- `market_snapshot.jsonl` 必须携带：`source_message_ids`（array）
- `source_message_ids` 必须可在 `okx_ws_messages.jsonl.message_id` 中解析（replayability）
- 若 snapshot 引用的 message_id 不可解析：verifier 必须 FAIL（不是 NOT_MEASURABLE）

### 7.2 Public WS minimal channel set (v0.9.1 reference)（冻结入口）

说明：
- DSM 的“订阅集合”允许随版本扩展，但每次扩展必须保持：
  - append-only evidence
  - channel→字段映射可审计
  - 缺测必须 NOT_MEASURABLE（不得用 0 伪装）

参考通道集（已在 VPS REAL WS 验收跑通）：
- `tickers`（instId=`BTC-USDT-SWAP`）→ `last_px`
- `mark-price`（instId=`BTC-USDT-SWAP`）→ `mark_px`
- `books5`（instId=`BTC-USDT-SWAP`）→ `bid_px_1/ask_px_1/bid_sz_1/ask_sz_1`
- `index-tickers`（instId=`BTC-USDT`）→ `index_px`
  - 关键规则（冻结）：对 `BTC-USDT-SWAP`，index 源通常属于 underlying/uly（`BTC-USDT`），不可直接用 swap instId 订阅，否则可能无推送→NOT_MEASURABLE
- `funding-rate`（instId=`BTC-USDT-SWAP`）→ `funding_rate/next_funding_ts_ms`

### 7.3 Verdict discipline (fail-closed)（冻结入口）

动机：
- 防止“字段缺失但 PASS”这类假阳性，确保后续建模/对照可复核。

冻结语义（建议在 run_manifest 中体现）：
- `PASS`：schema verifier PASS 且 canonical 字段满足该版本的“可测闭环”（例如 v0.9.1 需要 9/9 字段非 null）
- `NOT_MEASURABLE`：存在 `not_measurable:*` reason_codes（例如无推送/窗口过短/参数不匹配/解析失败），必须显式记录原因
- `FAIL`：证据缺失、join 不可回放、或 verifier rules 失败

## 6) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- Scanner E schema: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- Modeling pipeline: `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`


