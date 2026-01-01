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

## 6) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- Scanner SSOT (V11 anchor): `docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
- OKX contract SSOT: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`


