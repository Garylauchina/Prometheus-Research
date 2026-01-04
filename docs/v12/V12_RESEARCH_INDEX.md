# V12 Research Index / V12 研究入口（中文为主）

定位（冻结）：
- **V10 = 证据链诞生**
- **V11 = 证据链工业化**
- **V12 = 世界建模与生命系统上线**

本 index 是 V12 的唯一指挥台（SSOT index）。从现在开始，V12 新增文档只写入 `docs/v12/`（additive-only）。

---

## Start Here

V12 的第一阶段只做一件事：**世界建模**，并将其变成可复现事实，避免基因维度设计漂移成主观拍脑袋。

硬 gate（冻结）：
- **基因扩维后置**：必须等“世界扫描器分批实现到阶段性全功能 + tools 验证通过 + 建模文档（SSOT）验收通过”，才能进入“新增维度/扩维”。否则一律视为 NOT_READY（避免先验基因导致漂移）。
- **允许的最小基因重构（v0）**：仅做“对齐/分类/命名收敛”（例如 `control_class`、映射表、悬空旋钮扫描），不引入未经验证的新维度语义。

演化宪法（冻结入口）：
- **Epoch Constitution（语义不变的最大连续区间）**：`docs/v12/V12_SSOT_EPOCH_CONSTITUTION_20260102.md`
  - Epoch 不是时间切片，只在“语义断裂”时切换（算子/世界合同/观测口径任一变化即切 epoch）

指导性公理（冻结入口；不作为当前版本的工具验收项）：
- **System-level vs Engineering-level axioms**：`docs/v12/V12_SSOT_AXIOMS_SYSTEM_AND_ENGINEERING_20260103.md`

个体 balance（Δ事件驱动，冻结入口）：
- **Agent Balance Delta + Exchange Auto Events**：`docs/v12/V12_SSOT_AGENT_BALANCE_DELTA_AND_EXCHANGE_AUTO_EVENTS_20260102.md`
  - Broker 只推送 Δbalance（幂等 event_id + evidence_ref），交易所自动处置必须如实落盘（account-level truth）

方法论提醒（冻结）：
- 即使同时跑百万 Agent、跑万次实验，整体仍然只是演化空间中的**极小碎片**；V12 不追求“覆盖空间”，而追求在证据链约束下的 **可复现、可比较、可迁移的局部规律**。
- 因此，V12 的优先级始终是：先把世界输入/证据落盘/NOT_MEASURABLE 边界冻结成合同，再谈机制（新陈代谢/分裂繁殖）与基因维度。
- 任何新维度进入决策前必须先通过 **可审计+可测+可消融** 的验证；否则一律视为 NOT_READY（见：`docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`）。

证据路径约定（冻结）：
- V12 统一 `runs_root/run_id`：见 `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md` 的 “Evidence path convention”。

---

## V12 Mainline (light) — 版本目标（轻装上阵）

本阶段把目标收敛为 6 件事（按依赖顺序）：

- **World Feature Scanner（建模工具，独立）**
  - 定位：建模/测量工具，不是系统运行必备；不要求部署到 VPS 容器（见 Scanner SSOT）。
  - 口径：只负责“API 可直接获取/返回的参数结构与字段空间”（request/response/schema + NOT_MEASURABLE 边界）；不承担订单生命周期/微结构推断（例如 fill_ratio）。
  - 产物：`market_snapshot.jsonl` + `okx_api_calls.jsonl` + `scanner_report.json` + `run_manifest.json`（strict JSONL / 可回放 / fail-closed）。

- **Interaction impedance probe（并入 Scanner，独立测量）**
  - 定位：account-local truth（执行摩擦/延迟/拒单/限速桶），用于建模与后续裁决输入；不依赖 Broker。
  - 产物：`interaction_impedance.jsonl`（strict JSONL, append-only）+ 对应 probes 的证据回指（见 SSOT）。

- **Genome refactor（对齐/分类，不扩维）**
  - 目标：把“可表达/可提议/系统事实”分清（`control_class`），并完成悬空旋钮扫描与对齐表模板落盘。

- **Tick 周期轮询（世界输入主循环）**
  - 目标：先采用 tick + REST snapshot 的方式驱动世界输入（不依赖 DSM/event-driven）。

- **简单死亡判定（v0）**
  - 目标：定义一个最小、可审计、fail-closed 的死亡裁决接口（不引入复杂老化/不可逆损伤机制）。

- **ROI 翻倍繁殖（v0）**
  - 目标：定义繁殖触发与证据接口（不追求短期必然出现翻倍样本；验收以证据闭环为主）。

SSOT 入口：
- Scanner（工具定位 + probes + 可选阻抗探针）：`docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
- Scanner E schema（REST snapshot）：`docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- Interaction impedance evidence（v0 schema 入口）：`docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`（§1.1.1）
- Alignment / control_class：`docs/v12/V12_SSOT_OKX_ORDER_PARAMETER_SPACE_V1_20260103.md` + `docs/v12/V12_SSOT_OKX_ACCOUNT_POSITION_AND_PRETRADE_PARAMETER_SPACE_V1_20260103.md`

## V12 mini-releases (recommended cadence)

目的：把 V12 拆成可控的小版本，每个版本只完成一个“可验收闭环”，避免目标爆炸。

### 主线 mini-releases（light, recommended）

为了避免复杂度指数叠加，当前主线以“建模工具 + tick + life v0”推进，DSM/event-driven 封存后置。

- **V12.0 — Scanner v0 (REST snapshot, candidate schema, tools verification PASS)**
  - 对应：Mainline/Scanner
  - 验收：`market_snapshot.jsonl` 非空 + schema_verification PASS + evidence 可回放（source_call_ids 等）
  - 备注：schema `status` 仍为 `candidate`（不提前宣称 verified）

- **V12.0.1 — Scanner impedance probe v0 (optional write probes, independent)**
  - 对应：Mainline/Impedance（并入 Scanner，但默认关闭）
  - 验收：启用时必须生成 `interaction_impedance.jsonl`（strict JSONL）且每条具备 `account_id_hash + window + metrics + evidence_refs + verdict`；未启用时必须显式 NOT_MEASURABLE（不得伪造 0）。

- **V12.1 — Scanner hardening (repeatability + strict evidence replayability)**
  - 对应：Mainline/Scanner 迭代
  - 验收：在多次 runs 下稳定通过；缺测字段必须 `degraded + reason_codes`，禁止 “overall=ok 但存在 null”

- **V12.2 — Genome refactor v0 (alignment + control_class, no expansion)**
  - 对应：Mainline/Genome refactor
  - 验收：对齐表模板可机读；`control_class` 分类明确；悬空旋钮扫描可运行且结果可解释。

- **V12.3 — Tick loop v0 (polling world, evidence-first)**
  - 对应：Mainline/Tick
  - 验收：tick 轮询产生可回放的 `market_snapshot` 序列；失败必须 NOT_MEASURABLE 可见。

- **V12.4 — Life v0 (simple death + ROI doubling reproduction, interface-first)**
  - 对应：Mainline/Life
  - 验收：死亡/繁殖的“事件接口 + 证据落盘 + fail-closed”存在；不要求短期必然出现翻倍样本（避免上帝视角）。

---

### 封存/后置（capability sealed or deferred）

以下能力保留为“已验证/可选扩展”，但不作为当前主线依赖：

- DSM/WS ingestion（封存能力 + 长期稳定并入门槛）：`docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`
- 双管道 join（DSM↔Decision↔Broker）：后置到 DSM 长期稳定通过之后
- Settlement/账户级自动事件：保留为 life-system 的真值来源能力面，但不作为当前“建模工具 + tick + life v0”必备依赖

### M0 — World Feature Scanner v0（E: market info, single instId）

- **Scope (frozen)**:
  - Only `BTC-USDT-SWAP`
  - Read-only market info first (E/exogenous)
- **SSOT**:
  - World Feature Scanner: `docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
  - Scanner v0 E schema (V12): `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
  - OKX contract + order parameter space: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`（§12）
- **Acceptance**:
  - Scanner produces a run_dir with `run_manifest.json`, `okx_api_calls.jsonl`, `errors.jsonl`, `scanner_report.json`
  - Must produce non-empty `market_snapshot.jsonl`
  - Any endpoint failure must be NOT_MEASURABLE (with reason_code), never silent
  - Tools verification must pass for canonical schema (candidate→verified) before modeling can consume it

### M0.5 — WS ingestion only (event stream evidence, tick-consumable)

目的：解决“不用 WS 会限制后续事件驱动/新陈代谢/繁殖；直接上 WS 又是大工程”的两难：  
先把 WS 变成**可审计事件流输入**，但决策/演化系统先不强制改为 event-driven（仍可按 tick/采样消费）。

- **Scope (frozen)**:
  - OKX public WS (`/ws/v5/public`) only
  - Evidence-only ingestion: subscribe + message stream persisted
  - Map WS messages → canonical `market_snapshot.jsonl` (or future `market_event_ref`) with mask discipline
- **SSOT**:
  - Scanner v0/v0.5 schema: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
  - Downlink subscription manager (DSM): `docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`
  - Uplink/Downlink pipes + evidence + join keys: `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`
- **Acceptance**:
  - WS sessions/requests/messages evidence exists (append-only)
  - `market_snapshot.jsonl` can be produced from WS without breaking schema_verification rules
  - No silent reconnect/subscription loss (must be visible as NOT_MEASURABLE reasons)

### M0.5 实施状态快照（只增不改，事实记录）

已实现（VPS REAL WS 验收通过）：
- 下行 evidence：`okx_ws_sessions.jsonl` / `okx_ws_requests.jsonl` / `okx_ws_messages.jsonl`
- canonical：`market_snapshot.jsonl`（含 `source_message_ids` 回放锚点）
- verifier：`tools/v12/verify_dsm_ws_ingestion_v0.py` 输出 PASS 时，manifest 必须同步 `verdict="PASS"`；若存在 `not_measurable:*` reason_codes，则 verdict 必须为 NOT_MEASURABLE（fail-closed）

当前冻结的最小通道集（v0.9.1 参考实现）：
- `tickers`（instId=`BTC-USDT-SWAP`）→ `last_px`
- `mark-price`（instId=`BTC-USDT-SWAP`）→ `mark_px`
- `books5`（instId=`BTC-USDT-SWAP`）→ `bid_px_1/ask_px_1/bid_sz_1/ask_sz_1`
- `index-tickers`（instId=`BTC-USDT`）→ `index_px`（注意 underlying 映射）
- `funding-rate`（instId=`BTC-USDT-SWAP`）→ `funding_rate/next_funding_ts_ms`

### M1 — Modeling docs from scanner (SSOT, additive-only)

- Freeze:
  - Market feature schema (E dims) + mask/quality/reason_code
  - Exchange API parameter spaces (order/cancel/replace, etc.)
  - NOT_MEASURABLE conditions and ecological fences (rate limits, endpoint availability)
- **SSOT**:
  - Modeling docs pipeline + genome alignment table: `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`

### M2 — Genome refactor aligned to parameter spaces

- Freeze:
  - Genome dimensions must map to exchange parameter spaces (no invented knobs)
  - Separate: agent expresses vs system defaults vs gate decisions

### M3 — Event-driven (initial)

- Market data: WS push (with evidence discipline)
- Trading: REST (request/response evidence)

### M4 — Life system (metabolism + split reproduction)

- Metabolism replaces “death judgment”
- Capital-doubling split reproduction replaces “reproduction judgment”

---

## Cross-version anchors (read-only)

- V11 index: `docs/v11/V11_RESEARCH_INDEX.md`
- Agent probing + Proxy Trader: `docs/v11/V11_SSOT_AGENT_PROBING_AND_PROXY_TRADER_MODEL_20260101.md`
- Trade chain evidence: `docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_20251231.md`


