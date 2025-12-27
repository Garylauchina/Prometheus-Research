# V10 Gate 4 (Mac) — DEPRECATED: moved to VPS-only

> **Status**: Deprecated (2025-12-25).  
> Reason: Mac domestic connectivity to OKX is not reliable; proxy routing risks exchange risk-control and observation-channel drift.  
> Canonical execution spec: `docs/v10/V10_GATE4_OKX_DEMO_EVOLUTION_VPS.md`

# V10 Gate 4 (Mac): OKX Demo Evolution Core (Real Orders, No Artificial Fences)

> Contract version: 2025-12-24.2  
> Scope: Mac local + Docker, OKX **Demo** account only (no live funds)

## 0) Purpose

On a Mac environment (local + Docker), drive the multi-Agent evolutionary loop with **OKX Demo real order placement** and produce an auditable evidence chain for:

- lifecycle evolution (death / reproduction / seed pool)
- restart consistency (audit replay vs crash restart)
- execution & reconciliation in an **exchange-truth** world
- incident handling & degradation telemetry (ops-only)

This gate **does not require** a predefined trading frequency. We do **not** add “must trade every N ticks” fences to force Agent behavior.

## 1) Hard Semantics (non-negotiable)

- **S1. Real orders only (OKX Demo)**: any order intent must go through OKX Demo real order APIs.
- **S2. No fake trades**: forbidden to generate simulated fills/acks when API placement fails.
- **S3. Exchange is the truth source**: equity/positions/fills must be treated as externally observable truth (with auditable reconciliation).
- **S4. No artificial fences**: do not introduce “frequency fences” that force Agents to place orders for the sake of passing a gate.
  - Allowed: **ecological fences** for system safety (STOP/kill-switch/rate limit/capital conservation) and **post-hoc audit labels**.
  - Forbidden: injecting “must trade” constraints into Agent decision paths.

## 1.1) Interaction impedance (what we must be able to evidence)

“Impedance” is the measurable friction between the system and the exchange world (network + auth + API semantics + rate limits). It is **not** market data and cannot be reconstructed reliably after-the-fact unless it is recorded.

Tier-1 (screening, minimal, low cost) requires auditable impedance telemetry:

- `execution_fingerprint.json` must include:
  - `api_calls` (or `api_calls_derived_min` with a source note)
  - `error_count` + `error_events` (must differentiate at least: `timeout` / `connection_error` / `request_exception` / `http_error` / `api_error`)
  - `latency_stats_ms` (min/max/mean/p95 or equivalent)
  - `rate_limit_hits` (if detectable)

Tier-2 (promotion, optional, higher fidelity) may additionally include sampled raw evidence:

- `api_call_samples.jsonl` (append-only): a small, rate-limited sample of request/response metadata with strict redaction
  - must include at least: `ts_utc`, `method`, `endpoint`, `http_status`, `okx_code`/`sCode` (if present), `latency_ms`
  - may include: `request_hash` / `response_hash` to allow integrity checks without storing full payloads

## 2) Preconditions (must already be satisfied)

- OKX Demo account enabled, Demo API key available.
- Gate 4 execution prerequisites already validated (by separate drills / evidence bundles):
  - Startup Preflight & Bootstrap contract
  - Execution Engine contract (ops-only probe available)
  - Reconciliation module contract (observe-only default, evidence refs supported)
  - Incident runbook & STOP semantics

References:
- `docs/v10/V10_STARTUP_PREFLIGHT_AND_BOOTSTRAP_CONTRACT_20251223.md`
- `docs/v10/V10_EXECUTION_ENGINE_CONTRACT_OKX_DEMO_LIVE.md`
- `docs/v10/V10_RECONCILIATION_MODULE_CONTRACT_OKX_EXECUTION_WORLD.md`
- `docs/v10/V10_INCIDENT_RUNBOOK_C2_0_20251222.md`

## 3) Step 1 — One judgment window on Mac (96 ticks @ 15m)

### Goal

Prove the system can run **a full 96-tick judgment window** in OKX Demo execution world and produce complete artifacts (evidence-first).

### Required behavior

- Runs end-to-end without crash loops; any crash is recorded and recoverable under the restart policy.
- Any placed order must satisfy S1/S2 and be traceable across artifacts (see Evidence Contract).
- If **no orders happen**:
  - The run must explicitly be classified as **NO_TRADE** in its summary (evidence-based).
  - NO_TRADE is **not a failure of Step 1** (strategy may rationally abstain), but it is **inconclusive** for claims about “execution fills/fees behavior under real trading.”

### Evidence contract (minimum artifacts)

### Evidence sampling principle (record-first, analysis-later)

Analysis methods and conclusions may evolve after the 24h window, but **evidence sampling and artifact contracts must be fixed up-front**. Step 1 is evaluated primarily on whether the run produces the agreed evidence with stable semantics.

Tier-1 (screening, required) focuses on the minimum set needed for read-only clustering readiness:

- **Lifecycle truth**: `death_events.jsonl` / `birth_events.jsonl` (or equivalents), evidence-backed even if 0 events
- **Decision chain truth**: `decision_trace.jsonl` (tick-indexed, append-only)
- **Exchange truth**: `exchange_snapshots.jsonl` + `capital_reconciliation_events.jsonl`
- **Interaction impedance truth**: `execution_fingerprint.json` (api_calls + errors + latency + rate-limit)
- **Minimal market context (alignment anchor)**: per tick, store enough to align lifecycle/decision records to an exchange time axis:
  - recommended: `instId`, `source_endpoint`, `source_ts`, and `mark_price` (or `mid`)
  - allowed implementation: embed into `decision_trace.jsonl` tick summaries, or a dedicated `market_observations.jsonl`

Tier-2 (promotion, optional) upgrades evidence for stronger causal attribution:

- **Genome evidence**: `genomes_snapshot.jsonl` (hash-only allowed; vectors optional)
- **Event-window microstructure sampling**: limited-depth bid/ask or small trade windows around key ticks (death/birth/trade intents), not full-day orderbook capture
- **Historical data as evidence input (optional)**: allowed only if “evidence-ized” (fixed source + fixed params + file hashed and referenced); otherwise it is reference-only and must be labeled as such

Each Step 1 run produces a dedicated `run_dir/` containing at least:

- `run_manifest.json`
  - includes: `mode=okx_demo_api`, `exchange_id=okx`, `env=demo`, `symbol_in_use`, `git_commit`, `config_hash`
  - includes bootstrap & allocation fields (as per preflight contract)
- `startup_preflight.json` (or `skipped + reason`, but must be honest)
- `exchange_snapshots.jsonl` (append-only, tick-indexed)
- `capital_reconciliation_events.jsonl` (append-only, tick-indexed, `reconciliation_mode=observe_only` by default)
- `execution_fingerprint.json` (api_calls, error_events/error_count, latency stats)
- `errors.jsonl` (structured errors, if any)
- **Decision chain trace (append-only, tick-indexed)**:
  - `decision_trace.jsonl` (or equivalent) must exist to support the claim “NO_TRADE was a genuine Agent decision”.
  - Minimal fields per record: `ts_utc`, `tick`, `run_id`, `agent_id_hash` (or `agent_id`), `action` (e.g., hold/open/close/none), and optional `reason_code`.
- Evolution core evidence (existing project artifacts; names may vary but must be present and referenced):
  - seed/pool state snapshots (pre/post)
  - `death_events.jsonl` (or equivalent) with minimal fields (cluster-ready)
  - `birth_events.jsonl` (or equivalent) with minimal fields (cluster-ready)
- Genome evidence (required **only** for gene-level clustering claims):
  - `genomes_snapshot.jsonl` (or equivalent) must exist if the run claims “death clustering by genome / gene pool analysis”.
  - Minimal fields per record: `ts_utc`, `run_id`, `tick` (recommended `1` or `96`), `agent_id_hash`, and `genome_hash`.
  - Optional fields (if feasible): genome vector encoding/version/shape. If vectors are omitted, the run must explicitly state “hash-only snapshot; vectors not reconstructable” and why.
- Integrity:
  - `FILELIST.ls.txt`
  - `SHA256SUMS.txt`

For any `ack_received=true` order, `capital_reconciliation_events.jsonl` must contain `evidence_refs` linking at least:

- an exchange snapshot record around the trade
- the local execution record (order submit intent + response)
- the exchange order status / fills record (or explicit absence + reason)

### Pass/Fail

- **PASS**: 96 ticks complete + artifacts complete + no fake trades + evidence integrity (`FILELIST` + `SHA256SUMS`) OK.
- **FAIL**: missing required artifacts; simulated fills/acks; evidence integrity missing; uncontrolled crash loop with no recoverable continuation.
- **INCONCLUSIVE (execution-fee closure only)**: run is NO_TRADE (still PASS for Step 1 stability & lifecycle; but cannot claim execution fills/fees closure was exercised in this run).
  - Note: “cluster-ready” means lifecycle evidence exists; if no death/birth occurred, the run must evidence that as 0 events.
  - Note: If `decision_trace.jsonl` (or equivalent) is missing, the claim “Agent chose to hold” is **Inconclusive** (cannot distinguish from “decision loop did not run”).
  - Note: If `genomes_snapshot.jsonl` (or equivalent) is missing, **gene-level** death/birth clustering is **Inconclusive**. Only behavior/ecology-level clustering may be performed from decision/lifecycle evidence.

## 4) Step 2 — Fault handling drills on Mac (ops-only)

### Goal

Intentionally create representative failures and confirm the system is:

- non-silent (errors are recorded)
- auditable (IEB can be packaged)
- recoverable (restart policy produces a consistent continuation)

### Required drill types (at least one each)

1) **Exchange-layer faults**: timeout/connection_error/request_exception OR explicit OKX API `sCode/sMsg`
2) **System-logic faults**: NaN/Inf/div-by-zero/illegal state (must be structured in `errors.jsonl`)
3) **Docker/process faults**: STOP semantics, controlled shutdown, IEB
4) **Mac “VPS-like” faults**: disk-full / permission errors / wrong mode-symbol-endpoint config (must fail-fast with clear reason)

Pass requires evidence bundles per drill: run_dir + report + hashes.

## 5) Step 3 — Long-run stability & seed pool sustainability (real-time)

### Goal

Run longer than one judgment window and verify:

- seed pool does not explode uncontrollably
- the system remains observable and operable (STOP/IEB)
- disk growth is measurable and within an agreed envelope

### Note on time acceleration

Time acceleration is **not compatible** with OKX Demo real trading. If acceleration is required, it must be defined as a separate **offline/replay gate** (different world; cannot be mixed with this gate).

## 5.1) Deferred validation items (do not block the current 24h run)

The following items are recognized as high-risk evidence gaps when transitioning from **simulated/offline market inputs** to **live OKX API market inputs**. They should be addressed **after** the current 24h judgment window finishes, without intervening mid-run.

- **D1. Market→Decision input closure (hardening)**:
  - Risk: market data is fetched, but not correctly passed into the decision module; or passed with wrong time alignment/fields; or silently degraded to defaults.
  - Required evidence (next iteration):
    - In `decision_trace.jsonl` (or equivalent), add auditable input-binding fields such as:
      - `instId_used`, `source_ts_used`, `mark_price_used` (or `mid_used`)
      - `market_context_hash` (or `features_hash`)
      - `policy_version` / `decision_contract_version`
    - Provide (or embed) a tick-indexed market anchor record (`market_observations.jsonl` or tick-summary embedding) so hashes/fields can be cross-checked.
- **D2. Silent fallback detection**:
  - Risk: API errors/timeouts cause implicit fallbacks (stale price, zero price, cached last value) without explicit evidence.
  - Required evidence (next iteration): explicit `reason_code` / `input_quality_flags` in decision traces when degraded inputs are used.

## 6) Reviewer authority

Each Step requires an explicit **Accepted/Rejected** note by the reviewer. Without written acceptance, the next Step must not start.

## 7) VPS entry rule (hard)

These **three Steps are executed in Mac Docker**. Only after **Step 1 + Step 2 + Step 3 are all Accepted** (with evidence bundles) may the project enter any **VPS deployment** workstream.


