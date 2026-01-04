# V11 SSOT — World Feature Scanner（世界特征扫描器）— 2026-01-01

目标：为“全部接口对 Agent 开放”的建模路线提供一个**可审计、可迁移、可复现**的外部事实来源。  
Scanner 通过真实对接 execution_world（OKX demo/live）扫描“世界特征/可用能力/生态围栏”，输出建模文档与证据包，作为后续基因维度设计与 gate 设计的对齐参照。

本文件只允许追加（additive-only）。

---

## 1) Scanner 的定位（冻结）

Scanner 是一个 **read-mostly** 的建模工具：
- **查询世界特征**（exchange/account/instrument/limits/headers/mode）
- **测试交互功能**（最小可控写入：例如下单最小量 one-shot、撤单、设置杠杆等 —— 可配置、默认关闭）
- **输出证据包（run_dir）**：把“世界返回了什么、我们调用了什么”落盘，供后续 SSOT/基因维度对齐

口径统一（冻结入口，重要）：
- **Scanner 只负责“API 接口可直接获取/返回的参数结构与字段空间”**：
  - request params 结构、response 字段结构（含 `code/sCode/sMsg`）、枚举/精度/条件字段、NOT_MEASURABLE 边界。
- Scanner **不负责**订单生命周期/微结构推断：
  - 例如 `fill_ratio`、部分成交/拆单/队列位置、成交统计推断等需要跨多次查询与统计才能得到的“推断型真值”。
  - 这类内容应由后续独立工具或生产系统证据链承载（避免 Scanner 膨胀为“微结构探测器”）。

基本维度原则（冻结入口，重要）：
- Scanner 获取并落盘的“维度特征/字段集合”属于 **基本维度（base dimensions）**：
  - 它们可以被后续演化/训练机制**自然筛选**（例如权重趋近 0、mask 长期为 0、在统计意义上不重要）。
  - 但不得由工程人员/策略人员**人为删减/裁剪字段集合**来“优化表现”（这会污染可观测空间并破坏可比较性）。
- 允许的处理方式只有：
  - **mask discipline**：不可测时用 `null + reason_codes` 明确标注 NOT_MEASURABLE；
  - additive-only：只允许新增字段与新增 reason_codes，不改旧语义、不删除旧字段。

硬边界（hard）：
- Scanner 不做策略，不做训练，不做收益评估。
- Scanner 输出是“世界事实快照”，不得伪造成稳定规则；规则冻结必须回写到 SSOT（例如 OKX 合约规则 SSOT）。

部署边界（冻结，重要）：
- Scanner 是**建模工具/测量工具**，用于定义系统演化模型与参数空间（SSOT 对齐），**不是系统运行必备组件**。
- 因此 Scanner **不要求部署到 VPS 容器**；它可以在本机/开发机运行，只要证据包（run_dir）可复现、可审计、可回放。
- 若未来在 VPS 运行 Scanner，仅作为测量环境差异的事实样本（不改变其“非必备工具”定位）。

独立性要求（冻结）：
- Scanner 必须能独立完成其 probes 与证据落盘，**不得依赖 Broker 的运行或 Broker 的 run_dir**。
- 允许复用底层 OKX connector 代码（签名/请求/证据落盘库），但不得依赖“系统角色链路”（Agent→Broker→Exchange）。

证据隔离（冻结入口，重要）：
- Scanner 的 run_dir 证据包只用于建模/对齐（tooling evidence），不得与生产系统 run_dir 混用（避免证据污染）。
- 推荐使用独立 runs_root（示例）：`./runs_v12_modeling_tool/`（见 V12 证据路径约定：`docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md` §0.1）。
- 建议在 `run_manifest.json` 写入 `run_kind="modeling_tool"` 以便 verifier 与人类审阅快速判别。

---

## 2) 输出物（run_dir 证据包，冻结）

Scanner 每次运行必须产生独立 `run_dir`，至少包含：
- `run_manifest.json`
  - `run_id`
  - `mode`（okx_demo_api / okx_live_api）
  - `run_start_ts_ms` / `run_end_ts_ms`
  - `scanner_version` / `contract_version`
  - `inst_id`（若扫描限定产品）
  - `capabilities_summary`（见 §4）
  - `verification`（pass/fail/not_measurable + reasons）
- `okx_api_calls.jsonl`（或统一的 `exchange_api_calls.jsonl`）
  - 每次请求/响应都必须落盘（含 headers 的必要字段：例如 demo 的 `x-simulated-trading` 是否存在）
  - 必须记录 OKX 的 `code/msg` 与 `sCode/sMsg`（见 OKX SSOT）
- `errors.jsonl`（任何异常都必须落盘；禁止只有 stdout）
- `scanner_report.json`
  - 结构化汇总（机器可读）：环境、接口可用性、限制、枚举/精度、建议的 gene 对齐表

可选（按需开启）：
- `paging_traces.jsonl`（如果扫描涉及分页接口）
- `positions_snapshot.json`（若读取持仓相关）

原则：
- **fail-closed**：缺证据/不可测必须显式 NOT_MEASURABLE，不得默认 PASS。
- **additive-only**：同一 run_dir 内禁止覆盖旧文件；只追加新行/新文件。

---

## 3) Scanner 功能分解（冻结）

### 3.1 查询世界特征（read-only probes）

必须覆盖（最小集合）：
- **交易环境**：
  - demo 是否要求 `x-simulated-trading: 1`
  - endpoint base（REST/WS）是否为 demo 专用域名（记录为事实，不主张对错）
- **账户与模式能力**：
  - 账户持仓模式（posSide 是否可用/是否必须）
  - `tdMode` 可用值（cross/isolated）
- **产品与合约基础信息（inst_id 维度）**：
  - ctVal/面值、最小下单量、价格精度/px 规则、sz 单位语义
  - 杠杆范围/精度（如 0.01~100.00）
- **生态围栏**：
  - 限速错误码（例如 50011/50061）
  - 挂单上限/单产品挂单上限（若能从接口获得则记录；否则标记为 NOT_MEASURABLE 并引用 SSOT 的人工来源段落）

### 3.1.1 v0 优先级：E（外显）— 市场信息查询（read-only, frozen）

动机：先从外显特征（E）开始——“查询市场信息”是最稳定、最可迁移、最容易做真值落盘的入口；也最适合作为后续基因维度/决策输入的公共基座。

范围（v0 最小集合，按 inst_id）：
- **v0 约束（冻结）**：当前只锁定单一产品 `BTC-USDT-SWAP`（永续合约）。
  - 理由：算力/探索规模受限；扩大市场意味着需要探索的 Agent 数量暴增，节奏会失控。
  - 该约束不改变模型：未来扩展到多 inst_id 时，只做 additive 追加（增加 allowlist），不改 v0 结论。
- **标记价格/指数价格/资金费相关（perp 关键外显）**
- **盘口/最新成交/行情快照（微观结构外显）**
- **K 线（时间尺度外显）**

OKX public（候选）接口清单（字段以“事实落盘”为先，后续可按用户粘贴的官方文档做 additive 扩充/纠正）：
- Instruments（产品信息，public）
- Ticker / Mark price / Index price（行情/标记/指数）
- Funding rate（资金费率/下一次结算时间等）
- Order book（深度）
- Trades（最新成交）
- Candles（K 线：多粒度）

落盘要求（冻结）：
- 每个 endpoint 的 request/response 必须记录在 `okx_api_calls.jsonl`（含 query params，例如 instId/bar）。
- Scanner 必须额外生成：
  - `market_snapshot.jsonl`：按时间追加的“结构化抽取结果”（以 `inst_id` 为主键）
  - `market_feature_vector.jsonl`：可选，将 snapshot 映射为固定维度的 E 向量（含 mask/quality/reason_code）

`market_snapshot.jsonl` 最小字段建议（语义冻结，字段名允许实现差异）：
- `ts_utc`
- `inst_id`
- `last_px`（若可得）
- `bid_px_1` / `ask_px_1`（若可得）
- `bid_sz_1` / `ask_sz_1`（若可得）
- `mark_px`（perp）
- `index_px`（perp）
- `funding_rate`（perp，若可得）
- `next_funding_ts_ms`（perp，若可得）
- `source_endpoints`（本条 snapshot 由哪些 endpoint 构成）
- `quality`（per field 或 per record；至少要有整体 quality）
- `not_measurable_reasons`（若缺失）

基因/维度对齐原则（冻结）：
- E 维度来自 **scanner 可复现的 market_snapshot**；DecisionEngine 不得把 unknown 写成 0，必须 mask=0。
- E 维度不等于策略：E 只是“世界外显”，不做主观意图注入。

验收（v0，冻结）：
- 在 OKX demo/live 任一环境中，Scanner 能在单次运行中产出 >=1 条 `market_snapshot.jsonl`（非空）
- 对每个调用过的 endpoint，`okx_api_calls.jsonl` 中必须可回放 request/response
- 若某 endpoint 不可用：必须 NOT_MEASURABLE（含 reason_code），不得静默跳过
- `run_manifest.json.inst_id` 必须为 `BTC-USDT-SWAP`

### 3.2 测试交互功能（write probes，默认关闭）

原则：写探针只用于“验证接口链路/能力开关/真值可落盘”，不是为了成交质量。

建议提供的可选写探针（逐项可启用）：
- `probe_set_leverage`：对指定 instId/tdMode/posSide 设置杠杆（用于 leverage truth binding）
- `probe_place_order_min_sz`：按最小 sz 下一个可控订单（例如 limit 到远离市场价，避免成交；或 market 极小量，按风险承受配置）
- `probe_cancel_order`：对上一单撤单验证（证明取消接口可用）

交互阻抗（interaction impedance）探针（v0，独立测量入口，默认关闭）：
- 目标：在不依赖 Broker 的前提下，测量 account-local 的交互摩擦（延迟/拒单/限速/回执桶），并落盘为建模事实。
- 建议新增产物（run_dir 内）：
  - `interaction_impedance.jsonl`：窗口聚合指标（strict JSONL，append-only）
  - `probe_attempts.jsonl`（或等价）：每个 probe 的抽象记录（action/result/reason_code + evidence_refs）
- 若 write probes 未启用：与写侧相关的阻抗指标必须判为 NOT_MEASURABLE（不得伪造 0）。

每个写探针必须：
- 有独立开关（默认 off）
- 有独立 `gate_reason_code`（如果因为系统资源/生态围栏拒绝）
- 把 request/response 作为证据落盘（可被后续审计复核）

---

## 4) Scanner → 建模文档输出（冻结）

Scanner 必须生成一个“建模对齐表”（写入 `scanner_report.json`）：
- `order_api_parameter_space`：对齐 OKX `POST /api/v5/trade/order` 的参数集合（引用：OKX 合约规则 SSOT §12）
- `agent_expressive_dims`（建议子集）：
  - 哪些字段归 Agent 基因/决策表达（例如 instId/side/posSide/ordType/sz/px/leverage_target）
  - 哪些字段归系统默认/派生（例如 clOrdId/tag/expTime）
  - 哪些字段由 gate 决定或可能被强制拒绝（例如超出资金/限速/接口不可用）
- `capabilities_summary`：
  - `can_read_*` / `can_write_*` / `not_measurable_reasons`

该报告的用途：
- 作为基因维度设计的上游事实（减少“凭感觉做基因维度”）
- 作为多交易所迁移的对齐入口（换交易所只要换扫描器适配层与 SSOT）

---

## 5) 验收标准（冻结）

最小验收（read-only）：
- 必须生成 run_dir 与 manifest/report/api_calls/errors
- 必须能证明 demo 头是否被正确添加（若 mode=demo）
- 对关键接口的可用性给出 PASS/FAIL/NOT_MEASURABLE（并提供 reasons）

增强验收（写探针启用时）：
- `probe_set_leverage` 成功或失败都必须可审计（sCode/sMsg 落盘）
- 若下单探针启用：必须产生可 join 的订单回执证据（clOrdId/ordId），并能被后续 auditor materialize truth（若本仓库 SSOT 要求 truth-first）

---

## 6) 与现有 SSOT 的关系（入口）

- Agent probing + Proxy Trader：`docs/v11/V11_SSOT_AGENT_PROBING_AND_PROXY_TRADER_MODEL_20260101.md`
- OKX 合约规则与下单参数空间：`docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`（§12）
- Trade chain evidence：`docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_20251231.md`
- Error basket：`docs/v11/V11_STEP96_EXCHANGE_ERROR_BASKET_20251231.md`


