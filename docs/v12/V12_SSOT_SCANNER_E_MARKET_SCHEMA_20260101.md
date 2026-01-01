# V12 SSOT — Scanner v0 (E: Market Info) — OKX Public Scan List + Evidence Schema — 2026-01-01

目标：把 V12 的第一阶段（M0）冻结成“可实现、可验收、可迁移”的契约：  
Scanner v0 只做 **E（外显）市场信息查询**，锁定单一产品 `BTC-USDT-SWAP`，并输出可机读证据与对齐表。

本文件 additive-only。

---

## 1) Scope（冻结）

- **inst_id（frozen）**：`BTC-USDT-SWAP`
- **mode**：okx_demo_api / okx_live_api（都必须支持；demo 与 live 的 base URL/headers 作为事实落盘）
- **read-only**：本阶段不启用任何写探针（不下单、不撤单、不设杠杆）

传输层选择（冻结）：
- **v0 实现优先使用 REST 拉取快照**（request/response 证据最稳定，最易复现与审计）。
- **WebSocket（事件驱动）作为 v1 扩展**：用于更低延迟/更高频的行情推送，但必须满足 WS 证据纪律（订阅与消息流落盘）后才允许作为“决策输入真值”。

---

## 2) OKX Public endpoints（v0 清单，冻结入口）

说明：
- 这里冻结的是“Scanner 必须覆盖的能力面”（market/mark/index/funding/books/trades/candles）。  
- endpoint 的具体 path/参数若与 OKX 官方文档存在差异，以后只做 additive 修正（补充“confirmed_by_source”字段与版本戳），不删旧记录。

### 2.1 Required probes（必须覆盖）

- **Ticker / last price**：按 `instId=BTC-USDT-SWAP` 获取最新行情快照  
- **Order book (L2)**：按 `instId` 获取盘口（至少 L1：bid1/ask1）  
- **Trades**：按 `instId` 获取最新成交流（用于 microstructure 外显）  
- **Candles**：按 `instId` 获取 K 线（至少一种粒度；粒度作为参数落盘）  
- **Mark price (perp)**：获取 `BTC-USDT-SWAP` 标记价格  
- **Index price (perp underlying)**：获取指数/指数相关价格（作为外显参照）  
- **Funding rate**：获取资金费率与下一次结算时间等外显字段（若 OKX 公共接口可得）

### 2.2 Evidence requirement（冻结）

- 每个 probe 的每次请求/响应必须写入：
  - `okx_api_calls.jsonl`（request + response + http_status + code/msg + sCode/sMsg + timing）
- 每次“聚合一次外显快照”必须写入：
  - `market_snapshot.jsonl`

---

## 3) `market_snapshot.jsonl` schema（冻结）

每行表示某一时刻对 `BTC-USDT-SWAP` 的外显快照（可由多个 endpoint 聚合而成）。

### 3.1 Required fields（必须）

- `ts_utc` (string): ISO8601
- `inst_id` (string): must be `BTC-USDT-SWAP`
- `snapshot_id` (string): 本地生成（用于 join 到 decision）
- `source_endpoints` (array[string]): 本条 snapshot 使用了哪些 probe
- `quality` (object):
  - `overall` (string): `ok` / `degraded` / `not_measurable`
  - `reason_codes` (array[string])

### 3.2 Market fields（建议，v0 至少产出其中一部分；缺失必须可审计）

- `last_px` (string|null)
- `bid_px_1` (string|null)
- `ask_px_1` (string|null)
- `bid_sz_1` (string|null)
- `ask_sz_1` (string|null)
- `mark_px` (string|null)
- `index_px` (string|null)
- `funding_rate` (string|null)
- `next_funding_ts_ms` (integer|null)

### 3.3 Mask discipline（冻结）

- unknown 不得伪造为 `0` 或空字符串。
- 若某字段不可得，必须为 `null`，并在 `quality.reason_codes` 提供原因（例如 `endpoint_unavailable` / `rate_limited` / `schema_changed`）。

---

## 4) `market_feature_vector.jsonl`（可选，冻结入口）

用途：将 `market_snapshot.jsonl` 映射为固定维度 E 向量，供后续“基因维度/决策输入”对齐。

若启用，必须包含：
- `ts_utc`
- `inst_id`
- `snapshot_id`
- `feature_contract_version`
- `features` (array[number]): fixed-dim
- `mask` (array[int]): same length, values ∈ {0,1}
- `reason_codes` (array[string]): 对 mask=0 的维度解释

注意：v0 可以暂不启用 feature_vector，但必须先把 snapshot 做实。

---

## 5) Acceptance (M0)（冻结）

### PASS 条件（必须全部满足）

- run_dir 内存在：
  - `run_manifest.json`
  - `okx_api_calls.jsonl`
  - `errors.jsonl`
  - `scanner_report.json`
  - `market_snapshot.jsonl` 且 **非空**
- `market_snapshot.jsonl` 中每行 `inst_id` 均为 `BTC-USDT-SWAP`
- 任一 probe 若失败，必须在 `scanner_report.json` 与 `errors.jsonl` 中体现为 NOT_MEASURABLE（含 reason_code），不得静默跳过

### FAIL 条件（任一触发即 FAIL）

- 不产出 `market_snapshot.jsonl` 或产出空文件
- unknown 被写成 0（违反 mask 纪律）
- 发生请求但没有在 `okx_api_calls.jsonl` 留下可回放证据

---

## 6) Canonical schema verification（schema 先验收后采信，冻结）

定位（冻结）：
- `market_snapshot.jsonl` 的 schema 在 v0 阶段属于 **candidate canonical schema**（候选合同）。
- 只有当 Scanner 的真实运行证据证明该 schema 可稳定产出、缺失可解释、类型/单位一致时，才能升级为 **verified canonical schema**，作为“建模工具合同”被采信。

验证执行者（冻结）：
- 由独立 **tools/verifier** 执行验证（read-only，fail-closed），输入为 `run_dir`。
- v0 只做 **读验证**；v1/v2 可追加 **交易验证**（通过可控写探针）作为更强的约束验证来源。

### 6.1 必须新增的 manifest/report 字段（冻结）

Scanner v0 必须在 `run_manifest.json`（或 `scanner_report.json`）写入：
- `schema_contract`：
  - `name`: `market_snapshot`
  - `version`: 例如 `v0`
  - `status`: `candidate` / `verified`
  - `verification`：
    - `passed` (bool)
    - `failed_rules` (array[string])
    - `field_coverage` (object): key=field_name, value={present_ratio, not_measurable_ratio, top_reason_codes}

### 6.2 验证规则（v0，冻结）

在一个 run 中对 `market_snapshot.jsonl` 做以下自检（fail-closed）：
- **Schema adherence**：每行必须包含 required fields（§3.1）；缺一个即 FAIL。
- **Type discipline**：字段类型必须符合 §3（例如 px 用 string 或 null；ts 为 ISO8601 字符串），否则 FAIL。
- **Mask discipline**：unknown 不得写 0/空字符串；必须 `null + reason_code`，否则 FAIL。
- **Evidence replayability**：每个 snapshot 的 `source_endpoints` 必须能在 `okx_api_calls.jsonl` 中找到对应请求/响应证据（可用 call_id 或可回放索引），否则 FAIL。

### 6.3 verified 的门槛（冻结入口）

`status=verified` 的最低门槛（建议 v0→v1 升级时执行）：
- 在 >=N 次独立 runs 中（N 后续补充）均能产出非空 `market_snapshot.jsonl`
- 对关键字段（例如 `bid_px_1/ask_px_1/last_px`）达到可解释的覆盖率门槛（coverage 规则后续 additive 冻结）
- schema 的版本升级遵守 additive-only（只增字段/增 reason_code，不得删除或改语义）

---

## 7) OKX WebSocket public data (public WS) — extracted notes（只读参考，additive-only）

来源：用户提供页面 `https://www.okx.com/docs-v5/zh/#public-data-websocket`（OKX docs-v5 zh）。  
定位：这是 OKX **公共数据 WebSocket**（public WS），用于“普通产品”的公共数据推送/订阅，更符合我们 `BTC-USDT-SWAP` 的 E（外显）市场信息事件驱动路径。

连接地址（文档示例）：
- 模拟盘：`wss://wspap.okx.com:8443/ws/v5/public`
-（实盘地址在该文档站点的其它位置通常也会给出；本段只记录我们从页面片段中抽取到的明确字符串）

URL Path（文档原文示例）：
- `/ws/v5/public`

订阅请求通用结构（文档示例）：
- `id`：可选，1–32 位字母数字组合（回显用于关联请求）
- `op`：`subscribe` / `unsubscribe`
- `args`：数组，每项至少包含：
  - `channel`
  - `instId` 或 `instType`（取决于频道）

通用返回结构（从文档示例抽取）：
- 成功：`event=subscribe`，回显 `arg`，包含 `connId`
- 失败：`event=error`，包含 `code=60012` 与 `msg=Invalid request...`（示例）

### 7.1 Instruments channel（产品频道）

用途（文档原文）：当有产品状态变化时推送增量数据（不再推送全量）。

订阅示例（文档原文）：
- `channel`: `instruments`
- `instType`: `SWAP`（永续合约；我们锁定的产品类型）

### 7.2 Mark price channel（标记价格频道）

订阅示例（文档原文）：
- `channel`: `mark-price`
- `instId`: 示例中为 `BTC-USDT`（注意：这不是 `BTC-USDT-SWAP`；具体 instId 取值需以实际验证为准）

推送频率（文档原文）：
- 标记价格有变化时：每 200ms 推送一次
- 标记价格没变化时：每 10s 推送一次

### 7.3 Index tickers channel（指数行情频道）

订阅示例（文档原文）：
- `channel`: `index-tickers`
- `instId`: `BTC-USDT`（文档解释：指数，以 USD/USDT/BTC/USDC 为计价货币的指数；与 `uly` 含义相同）

推送频率（文档原文）：
- 每 100ms 有变化就推送一次
- 否则一分钟推一次

### 7.4 Funding rate channel（资金费率频道）

订阅示例（文档原文）：
- `channel`: `funding-rate`
- `instId`: 示例为 `BTC-USD-SWAP`（我们目标是 `BTC-USDT-SWAP`，需用 scanner/tools 做真实验证）

推送频率（文档原文）：
- 30 秒到 90 秒内推送一次数据

### 7.5 Other public-data channels (observed in doc page ids)（只记录存在性）

该页面还包含（从章节 id 列表提取）：
- `mark-price-candlesticks`（标记价格 K 线）
- `index-candlesticks`（指数 K 线）
- `open-interest`（持仓量）
- `price-limit`（涨跌停价格）
- 以及其它公共数据频道（adl-warning / economic-calendar / liquidation-orders / option-summary 等）

对 V12 的影响（冻结）：
- v0 仍用 REST 快照；此处是 v1 事件驱动的 **public WS 参考锚点**。
- 基因/维度对齐仍以 canonical schema（`market_snapshot.jsonl`）为准；WS 只是更高频的采样机制。
- 对于 `instId` 取值（`BTC-USDT` vs `BTC-USDT-SWAP`）的差异：必须通过 scanner + tools 验证后才允许写入“可采信建模结论”。

### 7.6 v1 verification cases for `BTC-USDT-SWAP` (read-only, fail-closed)

目的：把 “public WS 的参数到底该怎么填” 从猜测变成可复现事实。  
这些用例是 **read-only**，用于 v1 WS 扩展或 tools 验证阶段；v0（REST 快照）不强制实现 WS。

证据落盘（v1 入口冻结，additive-only）：
- `okx_ws_sessions.jsonl`：连接建立/断开、ws_url、mode、conn_id（若可得）
- `okx_ws_requests.jsonl`：subscribe/unsubscribe 原始 JSON（含 id/op/args）
- `okx_ws_messages.jsonl`：每条推送/回执原始 JSON（含接收时间）

用例 VC1 — Instruments: 确认 `BTC-USDT-SWAP` 的存在与字段
- Subscribe:
  - `channel=instruments`
  - `instType=SWAP`
- Verify (PASS 条件)：
  - 在推送 `data[]` 中能找到 `instId=BTC-USDT-SWAP`
  - 记录该条目中与 E 维度有关的字段存在性（例如 tickSz/lotSz/ctVal/settleCcy 等，字段名以返回为准）
- FAIL 条件：
  - 订阅成功但在可接受时间窗内从未出现该 instId（必须 NOT_MEASURABLE: inst_not_observed）

用例 VC2 — Mark price: `mark-price` 的 instId 取值验证
- Try Subscribe A:
  - `channel=mark-price`, `instId=BTC-USDT-SWAP`
- If A returns `event=error` / no data, Try Subscribe B (fallback probe):
  - `channel=mark-price`, `instId=BTC-USDT`
- Verify：
  - 任一订阅路径能稳定收到推送（且推送结构可解析出 mark price 值字段，字段名以返回为准）
  - 在 `market_snapshot.jsonl` 中落 `mark_px`，并注明 `source_endpoints=["ws:mark-price"]`
- 规则：
  - fallback 的存在必须显式落盘（不能静默替换 instId）

用例 VC3 — Index tickers: `index-tickers` 的 instId 语义验证
- Subscribe:
  - `channel=index-tickers`, `instId=BTC-USDT`（文档说明其语义等价于指数/uly）
- Verify：
  - 能稳定收到推送并抽取 `index_px`（字段名以返回为准）

用例 VC4 — Funding rate: `funding-rate` 的 instId 取值验证
- Subscribe:
  - `channel=funding-rate`, `instId=BTC-USDT-SWAP`
- Verify：
  - 能收到推送并抽取 `funding_rate`、`next_funding_ts_ms`（字段名以返回为准；缺失必须 `null+reason_code`）

用例 VC5 — Candles (index/mark): 证明 WS candle 频道可用性（可选）
- Subscribe one of:
  - `channel=index-candlesticks`, `instId=BTC-USDT`（若该频道要求 bar/粒度，以返回/文档为准）
  - `channel=mark-price-candlesticks`, `instId=BTC-USDT-SWAP`（或 fallback，按 VC2 逻辑）
- Verify：
  - 能收到至少 1 条 candle 推送，并能映射到 `market_snapshot` 的时间戳锚点（若 v1 需要）

通用 FAIL-CLOSED 规则（适用于 VC1–VC5）：
- 任何 `event=error` 必须落盘（含 code/msg），并进入 `scanner_report.json` 的 NOT_MEASURABLE reasons（例如 ws_channel_unavailable / ws_instid_invalid）。
- “订阅成功但无推送”必须按时间窗判定为 NOT_MEASURABLE（ws_no_data_within_window），不得无限等待。

---

## 8) OKX WebSocket public channel (spread trading / business WS) — extracted notes（只读参考，additive-only）

来源：用户提供页面 `https://www.okx.com/docs-v5/zh/#spread-trading-websocket-public-channel`（OKX docs-v5 zh）。  
注意：此处描述的是 **spread trading** 的公共频道，走 **business WebSocket**，使用 `sprdId`（如 `BTC-USDT_BTC-USDT-SWAP`）。它不等价于“普通产品 `BTC-USDT-SWAP` 的 public WS 行情频道”。我们把它作为 v1 事件驱动的可选参考锚点，避免概念混淆。

连接地址（文档原文）：
- 实盘：`wss://ws.okx.com:8443/ws/v5/business`
- 模拟盘：`wss://wspap.okx.com:8443/ws/v5/business`

订阅请求通用结构（文档示例）：
- `id`：可选，1–32 位字母数字组合（回显用于关联请求）
- `op`：`subscribe` / `unsubscribe`
- `args`：数组，每项至少包含：
  - `channel`
  - `sprdId`（例如 `BTC-USDT_BTC-USDT-SWAP`）

### 8.1 Order book / depth channels（深度频道）

可用频道（文档原文）：
- `sprd-bbo-tbt`：首次推 1 档快照；之后定量推送（每 10ms，当 1 档变化推送一次）
- `sprd-books5`：首次推 5 档快照；之后定量推送（每 100ms，当 5 档变化推送一次）
- `sprd-books-l2-tbt`：首次推 400 档快照；之后增量推送（每 10ms 推送一次变化数据）

推送顺序（文档原文，单连接/交易产品维度固定）：
- `sprd-bbo-tbt` → `sprd-books-l2-tbt` → `sprd-books5`

### 8.2 Public trades channel（公共成交数据频道）

- `channel`: `sprd-public-trades`
- 推送语义（文档原文）：有成交就推送；每次推送仅包含一条成交数据
- 推送示例字段（节选）：`sprdId`, `tradeId`, `px`, `sz`, `side`, `ts`
- 错误示例（文档原文）：`event=error`, `code=60012`, `msg=Invalid request ...`

### 8.3 Tickers channel（行情频道）

- `channel`: `sprd-tickers`
- 推送频率（文档原文）：
  - 最快 100ms 推送一次
  - 无触发事件时最慢 1s 推送一次
  - 触发事件：成交、买一卖一发生变动
- 推送字段（示例节选）：`last`, `lastSz`, `askPx`, `askSz`, `bidPx`, `bidSz`，以及 24h 统计字段（open/high/low/vol 等）

### 8.4 Candlesticks channel（K线频道）

- channel 枚举（文档原文节选）：`sprd-candle1m`, `sprd-candle5m`, `sprd-candle1H`, `sprd-candle1D`, ... 以及对应 `utc` 版本
- 推送频率（文档原文）：最快间隔 1 秒推送一次
- 备注（文档原文）：使用 business WebSocket，不需鉴权

对 V12 的落盘要求（与本仓库证据纪律对齐）：
- 若我们在 v1 引入 WS：必须把 `subscribe/unsubscribe` 请求与每条推送消息落盘（append-only），并能关联到 `market_snapshot.snapshot_id`（或未来的 `market_event_ref`）。
- 基因/维度仍对齐 canonical schema（`market_snapshot.jsonl`）；WS 独有字段只能 additive 追加到 schema，否则必须作为 `null + reason_code` 处理。

---

## 9) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- Scanner SSOT (V11 anchor): `docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
- OKX contract SSOT: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`


