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

方法论提醒（冻结）：
- 即使同时跑百万 Agent、跑万次实验，整体仍然只是演化空间中的**极小碎片**；V12 不追求“覆盖空间”，而追求在证据链约束下的 **可复现、可比较、可迁移的局部规律**。
- 因此，V12 的优先级始终是：先把世界输入/证据落盘/NOT_MEASURABLE 边界冻结成合同，再谈机制（新陈代谢/分裂繁殖）与基因维度。
- 任何新维度进入决策前必须先通过 **可审计+可测+可消融** 的验证；否则一律视为 NOT_READY（见：`docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`）。

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

- **V12.3 — Dual-pipe evidence closure (Downlink DSM + Uplink Broker)**
  - 对应：M0.5 → M1 的桥接
  - 目标：把“双管道信息流”跑通且可 join（下行 market_snapshot_id ↔ 决策 ↔ 上行 order_attempts/api_calls）
  - 验收：双管道证据文件齐全（见 `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`）+ join keys 可机验 + 关键缺失必须 NOT_MEASURABLE

- **V12.4 — Modeling SSOT v1 + genome alignment table v0 (no genome design yet)**
  - 对应：M1
  - 验收：建模文档（E dims contract + API parameter spaces）通过验收；`genome_alignment_table.json` 可从证据推导且自洽
  - 硬门槛：基因维度设计/重构仍后置（见 Start Here 的硬 gate）

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


