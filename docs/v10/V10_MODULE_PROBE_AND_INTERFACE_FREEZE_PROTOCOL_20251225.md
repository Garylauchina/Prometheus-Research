# V10 Module PROBE + Interface Freeze Protocol (C-stage execution world)

> Version: 2025-12-25  
> Scope: Prometheus-Research (contract) → constrains Prometheus-Quant (implementation)  
> Goal: after modularization, we must be able to **audit** and then **freeze** module interfaces so the execution world becomes reproducible and judgeable.

## 0) Why this exists

When exchange communication/execution logic is embedded in a “test runner” (e.g., `run_v10_service.py`), the system tends to silently mix worlds:

- offline internal state machine mutates `positions/state` as if fills happened
- execution world requires exchange-truth evidence for any position change

This protocol enforces:

- **module boundaries** (Connector / ExecutionEngine / Reconciliation / PositionTruth / RunArtifacts)
- **PROBE** (ops-only minimal proofs per module)
- **Interface Freeze** (schema/version lock after acceptance)

## 1) Definitions

- **Execution world**: `okx_demo_api` / `okx_live`. Exchange is truth.
- **Intent-only**: core/decision produces intents (`open/close/hold`) but must not mutate positions without exchange evidence.
- **PROBE**: minimal, ops-only run that exercises a module and produces a small evidence bundle + hashes.
- **Freeze**: schema + semantics are locked; only backward-compatible extensions allowed.

## 2) Hard rules (non-negotiable)

1) **No world mixing**
- In execution world, any change to `positions/state` must be attributable to exchange evidence (`order_status/fills/positions truth`) or explicitly marked `null + reason`.
- Internal simulated fills/positions are forbidden.

2) **Probe before long-run**
- A new/changed module must pass PROBE before it is used in a 96-tick window.

3) **Freeze after acceptance**
- After a module PROBE is accepted, its artifacts’ schema and semantics are frozen.
- Only additive changes allowed. Breaking changes require:
  - version bump, and
  - re-run PROBE acceptance.

## 3) Modules that MUST be encapsulated (minimum set)

### 3.1 ExchangeConnector (communication)

Responsibilities:
- signing/auth, HTTP transport, retries/backoff, timeout, rate-limit detection
- returns raw responses + minimal parse, does NOT decide business semantics

PROBE artifacts (minimum):
- `connector_probe.json` (request/response metadata, redacted)
- `connector_stats.json` (api_calls, error_events, latency)

Freeze scope:
- response metadata schema, error taxonomy, latency stats fields

### 3.2 ExecutionEngine (order lifecycle)

Responsibilities:
- submit order intent → ack → status → (fills if available)
- never fakes ack/fill
- correlation keys: `clOrdId` + `ordId_hash`

PROBE artifacts (minimum):
- `public_instruments_probe.json`
- `public_ticker_probe.json`
- `account_config_snapshot.json`
- `order_attempts.jsonl`
- `order_status_samples.json`
- `FILELIST.ls.txt`, `SHA256SUMS.txt`

Freeze scope:
- `order_attempts.jsonl` / `order_status_samples.json` schema

### 3.3 Reconciliation (capital truth)

Responsibilities:
- record exchange equity truth + reconciliation events (observe-only default)
- never “patch balances” without contracted mode/version

PROBE artifacts (minimum):
- `startup_preflight.json`
- `capital_reconciliation_events.jsonl`
- `FILELIST.ls.txt`, `SHA256SUMS.txt`

Freeze scope:
- reconciliation event schema + reason_codes vocabulary (versioned)

### 3.4 PositionTruth (positions & state binding)

Responsibilities:
- define the only truth source for “positions present?” under demo constraints
- if exchange positions are unreliable, must provide:
  - explicit `positions_truth_quality` and
  - an evidence-backed fallback (from fills/order_status) OR `unavailable` labeling

PROBE artifacts (minimum):
- `positions_truth_probe.json` (truth_quality + reason + sample)

Freeze scope:
- truth_quality enum + evidence fields

### 3.5 RunArtifacts (run_dir, hashes, STOP/IEB)

Responsibilities:
- create run_dir, manifest, filelist, sha256, STOP semantics, IEB packaging
- enforce tick monotonicity and no tick reset contamination

PROBE artifacts (minimum):
- `run_manifest.json`
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `errors.jsonl` (if any)

Freeze scope:
- manifest versioning fields, revision policy, tick monotonicity policy

### 3.6 CoreWorldLock (Agent/SystemManager semantics)

Responsibilities:
- enforce **world separation** at the lowest layer that all programs must traverse
- prevent “internal position simulation” in execution world (no `positions/state` mutation that pretends fills happened)
- restrict core to **intent-only** in execution world; all position/state truth must be applied from evidence (PositionTruth / exchange evidence)

Hard semantics (execution world):
- **world MUST be explicit** (no silent defaults): `world ∈ {execution_world, offline_sim}`
  - `execution_world`: intent-only; `positions` must remain empty; `state` must not change from desired_state
  - `offline_sim`: legacy internal simulation allowed (but cannot be used for Gate4 execution evidence)
- `Agent.step()` in `execution_world` MUST:
  - call decision logic to compute `signal + desired_state`
  - return intent fields (e.g., `intent_action`, `intent_desired_state`, `executed=false`)
  - **MUST NOT** call `open_position()` / `close_positions()`
  - **MUST NOT** mutate `positions` or simulate PnL/capital changes
- **Hard gate**: if `len(positions) > 0` at any tick in `execution_world` → immediate failure (STOP + errors.jsonl + IEB requirement)
- `Agent.state` updates in `execution_world` MUST be applied only via a dedicated truth interface (e.g., `apply_position_truth(position_exposure_ratio, positions_truth_quality)`), and only with evidence.
  - `position_exposure_ratio` is the single continuous truth feature for "position present + magnitude" (0.0 means flat).
  - `positions_truth_quality` MUST gate usage: if not `ok`, `position_exposure_ratio` MUST be `null` (or explicitly labeled `unknown`) to avoid silent truth fabrication.

PROBE artifacts (minimum):
- core intent-only probe output (script or run_dir evidence) proving:
  - execution_world: `positions==0` invariant holds across steps
  - intent fields exist and evolve (`intent_action` not necessarily all hold)
  - hard gate triggers on injected pollution
- decision trace sample showing `intent_action` / `intent_desired_state` recorded (not hardcoded “hold”)

Freeze scope:
- core world semantics contract version (header + probe acceptance)
- intent fields schema in decision trace (additive-only after freeze)

### 3.7 BrokerTrader (execution + registry facade)

Responsibilities:
- provide the **only public trading entrypoint** for runner programs in execution world
- accept agent intents and ensure:
  - `clOrdId` binding to `agent_id`
  - ack/status/(optional fills/bills) are recorded as append-only evidence
- provide two query entrypoints:
  - per-agent query (agent→orders evidence refs)
  - global audit query (run-level confirmation stats + anomaly list)
- enforce the order confirmation protocol (P0–P5) and trigger execution freeze on broken evidence chain

Contract:
- `docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`
- `docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`

PROBE artifacts (minimum):
- `order_attempts.jsonl` (must include agent_id_hash + clOrdId + ordId_hash)
- `order_status_samples.jsonl` (append-only; at least one follow-up query per ack)
- `FILELIST.ls.txt`, `SHA256SUMS.txt`

Freeze scope:
- BrokerTrader public API + evidence schemas + reason_code taxonomy (additive-only)

### 3.8 ExchangeAuditor (read-only cross-check)

Responsibilities:
- independently query the exchange (read-only) to audit BrokerTrader’s evidence completeness
- detect broken joins and missing evidence caused by network/asynchrony/paging gaps
- never place/cancel/amend/close any order (no write endpoints)
- this version is **evidence-only** (no runtime intervention/freeze/stop). Any intervention requires a separate contract + acceptance gate.

Contract:
- `docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`
- uses the same confirmation vocabulary: `docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`

PROBE artifacts (minimum):
- `auditor_report.json`
- `auditor_discrepancies.jsonl`
- `FILELIST.ls.txt`, `SHA256SUMS.txt`

Freeze scope:
- auditor report/discrepancy schemas + reason_code taxonomy (additive-only)

### 3.9 LifecycleJudge (death/reproduction adjudication)

Responsibilities:
- adjudicate end-of-review-window lifecycle decisions: `KEEP/DEATH/REPRODUCE`
- must be **evidence-first** in execution world: uses ledger/registry-derived metrics with `truth_quality`
- does not trade, does not connect to exchange write endpoints
- writes append-only lifecycle evidence for post-run clustering and audit

Contract:
- `docs/v10/V10_LIFECYCLE_JUDGE_MODULE_CONTRACT_20251226.md`

PROBE artifacts (minimum):
- `lifecycle_events.jsonl`
- `lifecycle_judge_report.json`
- `FILELIST.ls.txt`, `SHA256SUMS.txt`

Freeze scope:
- lifecycle event/report schemas + reason_code taxonomy (additive-only)

## 4) Acceptance workflow

For each module:

1) implement module boundary
2) implement PROBE runner (ops-only)
3) produce PROBE run_dir + hashes
4) reviewer marks **Accepted/Rejected**
5) upon acceptance: freeze schema + bump `contract_version`

## 5) Regression rule

Any change to a frozen module requires:

- re-run the module’s PROBE, and
- update `contract_version` in artifacts (or file header), and
- update Research docs with the new version note.


