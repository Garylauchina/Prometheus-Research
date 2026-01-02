# V12 SSOT — Uplink/Downlink Pipes + Evidence + Join Keys — 2026-01-01

目标：把 V12 的“双信息管道”冻结成可实现、可审计的证据合同：
- **Downlink（Exchange→System）**：DSM 负责订阅与事件输入（WS）
- **Uplink（Agent→Broker→Exchange）**：Broker 负责提交交易请求（HTTP/REST/WS trade API 均可扩展）

原则：不考虑算力/存储上限时，**上下行都应尽量全量落盘**；现实约束下可做降采样，但必须显式标注 NOT_MEASURABLE 与原因，禁止静默丢失。

本文件 additive-only。

---

## 0) Evidence path convention (runs_root/run_id)（冻结）

目的：硬化 V12 的证据保存路径，避免“跑过但找不到证据/不同人不同目录”的混乱。

默认约定（冻结，Quant repo 内相对路径）：
- **runs_root（默认）**：`./runs_v12/`
- **run_dir 命名**：`$runs_root/$run_id/`
- **run_id 命名规则（推荐）**：
  - `run_{component}_{truth_profile}_{YYYYMMDDTHHMMSSZ}`
  - 例：`run_scanner_v0_replay_20260101T091611Z`

兼容（冻结入口）：
- 若历史实现已使用 `./runs_v12_scanner/`（例如 v12-scanner-m0 的早期 run），允许继续读取，但从本冻结开始**新 run 统一写入 `./runs_v12/`**。

可复用定位方式（冻结）：
- `RUN_DIR="$(ls -td "$RUNS_ROOT"/run_* | head -1)"`
- 必须始终打印：`runs_root + run_id + 可复跑命令`

## 1) Roles（冻结）

- **DSM（Downlink Subscription Manager）**：连接/订阅/重连、原始消息落盘、canonicalization、内部二级订阅（internal pub/sub）
- **Broker（Proxy Trader / BrokerTrader）**：接收 Agent 交易请求→提交→回执→落盘（同时必须遵守 fail-closed gate 的边界，见 V11/Step91）
- **Agent**：只订阅系统 topic（不直接订阅交易所），提交交易请求给 Broker

---

## 1.1 Account-local “interaction impedance” (不可共享真值，冻结)

现实约束（冻结）：
- “交互阻抗/执行摩擦”在很大程度上是 **账号/子账户/连接局部** 的：限速桶、风控级别、历史行为、网络路径、队列位置等都可能导致不同账号观察到不同的拒单/延迟/成交体验。
- 这些差异并非交易所会对外提供的“全局状态”，因此不能被当作公共世界真值；它只能作为 **account-local truth** 记录与建模。

因此，证据必须显式携带“账号身份锚点”（脱敏可，但必须可 join）：
- `account_id_hash`（或等价字段：subaccount_id_hash / user_id_hash）

---

## 2) Evidence files（冻结）

### 2.1 Downlink (WS) evidence（必须）

- `okx_ws_sessions.jsonl`
  - connect/disconnect/reconnect events, ws_url, mode, conn_id (if available), reason_code
  - `account_id_hash`（必填，脱敏可）
- `okx_ws_requests.jsonl`
  - subscribe/unsubscribe raw JSON (`id/op/args`) + `account_id_hash`
- `okx_ws_messages.jsonl`
  - every received message (raw JSON) + receive_ts + `account_id_hash`

Canonical outputs（必须）：
- `market_snapshot.jsonl`（canonical schema, mask discipline）
- （v1+ 可选）`market_events.jsonl`（更细粒度事件流；若引入必须同样可回放/可 join）

### 2.1.1 Downlink replayability anchor (WS)（冻结入口）

目的：
- WS 下行没有 `source_call_ids`（REST 才有）。因此 canonical snapshot 必须能回指原始 WS 消息流。

冻结规则：
- `market_snapshot.jsonl` 必须包含：`source_message_ids`（array[string]）
- `okx_ws_messages.jsonl` 必须包含：`message_id`（可被 snapshot 引用）
- verifier 必须验证：snapshot 的 `source_message_ids` 全部可解析到 `okx_ws_messages.jsonl`

Internal pub/sub evidence（必须）：
- `agent_subscriptions.jsonl`
  - `ts_utc`, `agent_id_hash`, `topics[]`, `action` (subscribe/unsubscribe)

### 2.2 Uplink (trade) evidence（必须）

- `decision_trace.jsonl`
  - 必须能引用下行锚点（见 §3）
- `order_attempts.jsonl`
  - 每一次写操作 attempt（含 gate allow/reject + reason_code）
  - 必须包含 `account_id_hash`（或等价字段），否则无法解释“账号局部阻抗”
- `okx_api_calls.jsonl`（或统一 `exchange_api_calls.jsonl`）
  - 每一次 HTTP request/response（含 http_status、code/msg、sCode/sMsg）
  - 必须包含 `account_id_hash`（或等价字段）

Exchange truth（First Flight / truth-first 时必须）：
- `orders_history.jsonl`
- `fills.jsonl`
- `bills.jsonl`

### 2.3 Agent balance & exchange auto events（V12 life-system minimal interface, 冻结入口）

目的：
- 支持“事件驱动的新陈代谢/繁殖”而不引入复杂分账：Broker 只推送 Δbalance，Agent 自己累加。
- 交易所自动处置（强平/ADL/资金费/手续费等）必须如实落盘，作为 account-level truth 的一部分。

必须新增（append-only）：
- `agent_balance_events.jsonl`
  - 每条必须含 `event_id`（幂等）与 `evidence_ref`（可 join），见：
    `docs/v12/V12_SSOT_AGENT_BALANCE_DELTA_AND_EXCHANGE_AUTO_EVENTS_20260102.md`
- `exchange_account_events.jsonl`
  - 自动处置/非本系统主动交易的账户事件记录（同样必须可回指 bills/fills/position snapshots）

---

## 3) Join keys & attribution anchors（冻结）

### 3.1 Run-level keys（必须）

- `run_id`
- `run_start_ts_ms` / `run_end_ts_ms`

### 3.2 Downlink ↔ Decision join（必须）

Decision 必须能回答“当时看到的市场是什么”：
- decision record 中必须包含：
  - `market_snapshot_id`（引用 `market_snapshot.jsonl.snapshot_id`）
  - `market_ts_utc`（snapshot 的时间戳锚点）
  - `market_source`（例如 `rest_snapshot` / `ws_public`）

### 3.2.1 Decision record — candidate dims (unknown semantics but measurable)（冻结）

目的（冻结）：
- 允许引入“语义未知但强度可测”的候选维度（例如 `cloud_intensity`），用于演化/消融实验，但必须保持可审计与可回放。

硬规则（冻结）：
- `decision_trace.jsonl` 必须包含候选维度的 evidence 字段（若开启该实验）：
  - `cloud_intensity`（float in [0,1] 或 null）
  - `cloud_mask`（0/1）
  - `cloud_reason_codes`（array[string]）
- `run_manifest.json` 必须包含消融开关：
  - `ablation.cloud.enabled`（bool）
  - `ablation.cloud.mode`（`on|off`）
- **Fail-closed**：
  - 若 `ablation.cloud.enabled=true` 且缺少上述任一字段：该 run 必须判为 NOT_MEASURABLE（evidence_incomplete:candidate_dim）
  - 若 `ablation.cloud.mode="off"`：必须写 `cloud_mask=0` + `cloud_intensity=null` + `cloud_reason_codes=["ablation:cloud_off"]`

若未来使用事件流：
- 使用 `market_event_ref`（指向 `market_events.jsonl` 的主键）替代或并存

### 3.3 Decision ↔ Uplink order join（必须）

最小可 join 锚点（语义冻结）：
- `agent_id_hash`（或 `lifecycle_scope`，二者不得都为空）
- `client_order_id` / `clOrdId`
- `ordId`（若可得）

建议：
- `decision_ref`：在 `order_attempts.jsonl` 中引用 `decision_trace.jsonl` 的 evidence_ref（实现可机 join 闭环）

---

## 4) Fail-closed visibility（冻结）

任何一条管道发生以下情况必须显式落盘并进入 NOT_MEASURABLE（或 gate reject）：
- WS 断连/重连/订阅失败
- “订阅成功但无推送”超时
- REST/HTTP 调用失败或被限速
- 关键证据文件缺失或不可回放（例如有交易但无 api_calls）

### 4.1 Verdict semantics (PASS / NOT_MEASURABLE / FAIL)（冻结入口）

动机：
- 统一“verifier PASS”与“run verdict”之间的语义，避免出现字段缺失但 verdict=PASS 的假阳性。

冻结建议（run_manifest）：
- `verdict="PASS"`：verifier PASS 且该版本声明的关键字段闭环满足（例如 DSM v0.9.1 的 9/9 字段非 null）
- `verdict="NOT_MEASURABLE"`：存在明确的 `not_measurable:*` 原因码（例如 no_push / window_short / param_mismatch / parse_failed）
- `verdict="FAIL"`：verifier FAIL、证据文件缺失、或 replayability join 不可解析

补充（冻结入口）：
- 对下行 `index_px`：当订阅 `index-tickers` 时，instId 可能需要使用 underlying（例如 `BTC-USDT`）而非 `BTC-USDT-SWAP`；若订阅参数不匹配导致无推送，应记为 `not_measurable:index_tickers_param_mismatch`（而不是 not_implemented）

---

## 5) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- DSM SSOT: `docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`
- Scanner E schema: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- Trade chain evidence (V11): `docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_20251231.md`


