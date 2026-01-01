# V12 Research Index / V12 研究入口（中文为主）

定位（冻结）：
- **V10 = 证据链诞生**
- **V11 = 证据链工业化**
- **V12 = 世界建模与生命系统上线**

本 index 是 V12 的唯一指挥台（SSOT index）。从现在开始，V12 新增文档只写入 `docs/v12/`（additive-only）。

---

## Start Here

V12 的第一阶段只做一件事：**世界建模**，并将其变成可复现事实，避免基因维度设计漂移成主观拍脑袋。

---

## V12 Work Plan (ordered, fail-closed)

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


