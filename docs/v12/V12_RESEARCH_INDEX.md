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
- **基因维度设计/重构后置**：必须等“世界扫描器分批实现到阶段性全功能 + tools 验证通过 + 建模文档（SSOT）验收通过”，才能进入基因设计。否则一律视为 NOT_READY（避免先验基因导致漂移）。

演化宪法（冻结入口）：
- **Epoch Constitution（语义不变的最大连续区间）**：`docs/v12/V12_SSOT_EPOCH_CONSTITUTION_20260102.md`
  - Epoch 不是时间切片，只在“语义断裂”时切换（算子/世界合同/观测口径任一变化即切 epoch）

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

## V12 Work Plan (ordered, fail-closed)

## V12 mini-releases (recommended cadence)

目的：把 V12 拆成可控的小版本，每个版本只完成一个“可验收闭环”，避免目标爆炸。

- **V12.0 — Scanner v0 (REST snapshot, candidate schema, tools verification PASS)**
  - 对应：M0
  - 验收：`market_snapshot.jsonl` 非空 + schema_verification PASS + evidence 可回放（source_call_ids 等）
  - 备注：schema `status` 仍为 `candidate`（不提前宣称 verified）

- **V12.1 — Scanner v0 hardening (repeatability + strict evidence replayability)**
  - 对应：M0 迭代
  - 验收：在多次 runs 下稳定通过；缺测字段必须 `degraded + reason_codes`，禁止 “overall=ok 但存在 null”

- **V12.2 — WS ingestion only (DSM + evidence stream, tick-consumable)**
  - 对应：M0.5
  - 验收：WS sessions/requests/messages 全量落盘；WS→canonical snapshot 映射通过同一套 verification；订阅丢失/无推送超时必须 NOT_MEASURABLE 可见
  - 里程碑（已完成，记录事实而非叙事）：
    - DSM 已在 **VPS（direct, no proxy）** 上完成 REAL WS 验收闭环：连接→订阅→消息落盘→canonical→replayability join→verifier PASS
    - Canonical `market_snapshot` 的 v0.9.1 版本已实现 **5 通道→9 字段** 的可审计兑现（字段全非 null 时 `quality.overall="ok"`）
    - 关键冻结点：`index-tickers` 的 `instId` 必须使用 **underlying spot**（例如 `BTC-USDT`），而不是 `BTC-USDT-SWAP`（否则可能无推送→NOT_MEASURABLE）
    - 参考 SSOT：`docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`（新增 §7），`docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`（新增 §2.1.1/§4.1）

- **V12.3 — Dual-pipe evidence closure (Downlink DSM + Uplink Broker)**
  - 对应：M0.5 → M1 的桥接
  - 目标：把“双管道信息流”跑通且可 join（下行 market_snapshot_id ↔ 决策 ↔ 上行 order_attempts/api_calls）
  - 验收：双管道证据文件齐全（见 `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`）+ join keys 可机验 + 关键缺失必须 NOT_MEASURABLE

- **V12.3.1 — Settlement v0 (fills/bills truth → account events → Δbalance events)**
  - 目的：把“账户级真值（fills/bills）”物化为事件流，支撑生命系统的能量接口（Δbalance），并保证可机验闭环。
  - 验收（冻结，fail-closed）：
    - `fills.jsonl` + `bills.jsonl` 必须存在且 strict JSONL
    - `exchange_account_events.jsonl` 必须存在且每条可回指 `bills/fills/position_snapshot`
    - `agent_balance_events.jsonl` 必须存在且每条具备幂等 `event_id` + 可 join 的 `evidence_ref`
    - 无法归因到具体 Agent 的事件必须归因到 **System Agent-0**（`agent_id_hash="agent_0_system"`），且显式标注 system scope
    - 费用真值口径：`trade_fee` 必须以 **bills** 为准；若 `bills_missing=true` 但临时用 fills fee 作为候选，则必须标注 `trade_fee_from_fills_candidate`，并且 settlement verdict 必须为 NOT_MEASURABLE（reason_code=`bills_missing`）
    - Settlement 工具必须自行加载 `.env`（不得假设 broker 先跑过），并在 manifest 记录 env 加载统计（不泄露密钥）
    - `run_manifest.json` 的 `verdict` 与 `join_verification.*` 必须一致（禁止 verified=false 但 verdict=PASS）
  - SSOT：
    - Balance delta + exchange auto events: `docs/v12/V12_SSOT_AGENT_BALANCE_DELTA_AND_EXCHANGE_AUTO_EVENTS_20260102.md`（§3.3）
  - VPS demo 事实样例（只增不改）：
    - 当 `bills.jsonl>0`：`fee_truth_source="bills"`，verifier 必须输出 `verdict=PASS`
    - 当 `bills.jsonl==0` 且 `fills.jsonl>0`：`fee_truth_source="fills_candidate"`，verifier 必须输出 `verdict=NOT_MEASURABLE`（`reason_code=bills_missing`）

- **V12.4 — Modeling SSOT v1 + genome alignment table v0 (no genome design yet)**
  - 对应：M1
  - 验收：建模文档（E dims contract + API parameter spaces）通过验收；`genome_alignment_table.json` 可从证据推导且自洽
  - 硬门槛：基因维度设计/重构仍后置（见 Start Here 的硬 gate）

- **V12.1.1 — Candidate dim experiment v0 (“Cloud intensity”, ablation-first, auditable)**
  - 对应：M0→M1 之间的“演化观测实验层”（不改 genome schema）
  - 目标：以 E 维度为基础输入，引入一个“语义未知但强度可测”的候选维度 `cloud_intensity`，先跑可消融的演化/观测实验，验证是否出现可复现的聚类/维度坍缩信号
  - 验收（fail-closed）：
    - `decision_trace.jsonl` 必须落盘：`cloud_intensity`（有界）、`cloud_mask`、`cloud_reason_codes`
    - `run_manifest.json` 必须落盘：`ablation.cloud.enabled` + `ablation.cloud.mode(on|off)`
    - 必须至少完成一次可复现消融对照：`cloud_on` vs `cloud_off`
    - 若 cloud 不可测：必须 `mask=0 + reason_codes`，不得伪装 0；该 run 对 cloud 维度判定为 NOT_MEASURABLE
  - SSOT：
    - Candidate dim gate: `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`（§1.1）
    - Evidence fields: `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`（§3.2.1）

- **V12.5 — Event-driven decision v0 (consume downlink events, still auditable)**
  - 对应：M3（核心）
  - 目标：决策从 tick 轮询升级为“事件驱动消费”（例如 `market_events` 或更高频 snapshot），但仍必须可回放/可审计
  - 验收：Decision evidence 必须引用 `market_event_ref`/`market_snapshot_id`；断连/丢事件必须可见（NOT_MEASURABLE），禁止静默降级

- **V12.6 — Metabolism v0 (truth-profile aware)**
  - 对应：M4 的一部分
  - 验收：新陈代谢触发与证据落盘可审计；不依赖“死亡审判”裁决

- **V12.7 — Split reproduction v0 (capital-doubling)**
  - 对应：M4 的一部分
  - 验收：分裂繁殖触发基于可审计资本增长；证据链闭合

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


