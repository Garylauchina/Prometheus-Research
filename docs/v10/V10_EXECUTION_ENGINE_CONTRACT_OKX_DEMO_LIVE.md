---
title: V10 Execution Engine Contract (OKX Demo/Live)
version: "2025-12-23"
scope_repo: Prometheus-Research
owner: Architect AI
status: active
---

# V10 交易执行模块合同（OKX Demo/Live）

> 本文件是 **Prometheus-Research** 的“合同/验收口径”，用于约束 **Prometheus-Quant** 的实现。  
> 目标：把“真实执行”从散落的主程序逻辑中抽离，形成可复用、可审计、可复盘的 **Execution Engine**（执行引擎）。

---

## 0) 为什么必须封装

若执行逻辑散落在主程序（如 `run_v10_service.py`）内，将必然导致：

- **语义污染**：下单失败却“模拟成交/推进仓位”，导致交易所世界与本地世界脱钩。
- **审计断裂**：无法形成“本地证据 ↔ 交易所可回查证据”的闭环。
- **维护失控**：每次修一个 OKX 细节，主程序越改越乱，演练与筛选互相干扰。

因此必须引入统一的执行层：`ExecutionEngine`，主程序只做编排。

---

## 1) 模块边界（Hard Scope）

### 1.1 Execution Engine 负责

- **所有与交易所交互的调用**（public + private）
  - public：instruments/ticker 等（不得带鉴权头）
  - private：balance/config/order/cancel/status/fills 等（鉴权签名）
- **执行证据落盘**（append-only / sharded）
- **交易所可回查证据闭环**
  - 至少：order ack（ordId）+ order status（state/fillSz）
- **失败语义保持为失败**（不允许伪造 fill/ack）
- **最小化执行能力探针 PROBE**（ops-only、独立标签）
- **交付打包**：`FILELIST.ls.txt` + `SHA256SUMS.txt`

### 1.2 Execution Engine 不负责

- Agent 决策（不得为了“满足门槛”强迫交易）
- core 演化逻辑（`prometheus/v10/core/` 的状态机/基因表达）
- 策略实现（不写“阈值策略”）

---

## 2) 不可违反的语义（Hard Semantics）

### 2.1 禁止伪造交易（No Fake Trades）

在 `okx_demo_api` / `okx_live`：

- `place_order` 失败（HTTP 非 200 / OKX `code!=0` / data 内 `sCode!=0`）时：
  - **ack_received = false**
  - **fill_observed = false**
  - **不得**生成 simulated fill / 假 ack / 假 fill / 假仓位推进

### 2.2 fill_observed 的定义

- 只能来自交易所回查证据（order status / fills）
- 不允许通过“本地假设 market order 一定成交”来判定

### 2.3 public endpoint 的调用规则

- 对 `GET /api/v5/public/*`、`GET /api/v5/market/*`：
  - **不得**携带 `OK-ACCESS-*` 鉴权头
  - **不得**签名
  - 必须证据化 HTTP status + 响应体摘要（失败也要落盘）

---

## 3) 统一接口（Contracted API）

以下接口为“合同接口”，Prometheus-Quant 可以实现为类或函数，但对外语义必须一致。

### 3.1 public 探针

- `public_instruments(instType) -> (ok, evidence_path, parsed_minimal)`
  - 必须落盘：`public_instruments_probe.json`
  - `parsed_minimal` 至少包含：候选 `instId/state/instType`

- `public_ticker(instId) -> (ok, evidence_path, parsed_minimal)`
  - 必须落盘：`public_ticker_probe.json`
  - 注意：ticker 允许失败，但必须证据化；不得为了“省事”跳过 instruments。

### 3.2 private 基础能力

- `read_account_config() -> (ok, posMode, evidence_path)`
  - 必须落盘：`account_config_snapshot.json`

- `read_balance_equity_usdt() -> (ok, equity, field_used, evidence_path)`
  - 必须复用“统一 equity 解析逻辑”

### 3.3 订单闭环

- `submit_order(intent) -> (ok, clOrdId, ordId, ack_evidence_path)`
  - ack 证据必须包含：顶层 `code/msg` + data `sCode/sMsg` + `ordId_hash`

- `get_order_status(instId, ordId/clOrdId) -> (ok, status, evidence_path)`
  - 必须落盘：`order_status_samples.json`（append-only）

- `cancel_order(instId, ordId/clOrdId) -> (ok, cancel_evidence_path)`
  - 必须证据化撤单响应（失败也落盘）

---

## 4) instId 规则（51001 类错误必须可审计）

### 4.1 instId 选择硬门槛

下单前必须满足：

- `public_instruments(instType=SWAP)` 成功
- 选定 `instId` 必须存在且 `state == live`
- 若 instruments 查询失败或 instId 不存在：
  - **禁止继续下单**
  - 直接进入“交付打包”

### 4.2 51001 的证据化要求

若发生 `api_error:51001`（或同类 instId 错误）：

- 必须落盘：
  - `public_instruments_probe.json`
  - `public_ticker_probe.json`（若调用）
  - 下单请求摘要 + 返回摘要（脱敏）
- 报告必须能回答：instId 是否存在、是否 live、错误发生在哪个调用。

---

## 5) 最小化执行能力探针（PROBE）合同

### 5.1 PROBE 的定位

- **ops-only**
- `probe=true` 明确标注
- 不计入筛选表现（避免干预 Agent 决策）

### 5.2 PROBE 的最小闭环

对一个 `instId`：

1) `public_instruments(SWAP)`（证据化）
2) 选 `instId`（证据化）
3) `read_account_config()`（证据化）
4) LIMIT 下单（固定价格可用；不依赖 ticker 定价）
5) `get_order_status()`（至少 1 次）
6) `cancel_order()`（建议）
7) `get_order_status()`（撤单后再查 1 次）
8) 打包：`FILELIST.ls.txt` + `SHA256SUMS.txt`

### 5.3 PROBE 的交付物（最低集合）

run_dir 内必须至少包含：

- `public_instruments_probe.json`
- `probe_selected_inst.json`
- `account_config_snapshot.json`
- `probe_execution.jsonl` 或 `m_execution_raw_part_0001.json + index`
- `order_status_samples.json`（若下单成功，至少 2 条）
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `OKX_PROBE_MINIMAL_EVIDENCE_REPORT.md`（No Conclusions）

---

## 6) 主程序瘦身规则（防止“改得乱七八糟”）

主程序（service wrapper）只允许：

- 创建 run_dir + manifest
- 初始化 ExecutionEngine
- 编排（调用 engine 的公开接口）
- STOP/IEB 等事故流程

主程序 **禁止**：

- 直接 `requests.get()` public endpoint
- 直接写 `order_status_samples.json` / `m_execution_raw_*`
- 任何“失败时模拟成交”的逻辑

---

## 7) 审计裁决口径（No Conclusions）

Prometheus-Quant 在交付报告中不得输出 PASS/FAIL 结论；必须只输出：

- 文件路径 + SHA256 引用
- 字段对照（clOrdId/ordId_hash ↔ order_status.state/fillSz）
- 错误的证据化（HTTP status + response 摘要）

---

## 8) 接口冻结（Interface Freeze）

当 Execution Engine 在 Gate 4 通过验收后：

- `public_instruments_probe.json / public_ticker_probe.json / probe_execution.jsonl(or m_execution_raw*) / order_status_samples.json` 的 **schema 必须冻结**
- 允许向后兼容扩展：只能新增字段，不得更改字段含义/类型，不得删除字段
- 如需破坏性变更：必须提升 `contract_version`（或文件头 version）并重做 Gate 4 的最小 PROBE 证据包


