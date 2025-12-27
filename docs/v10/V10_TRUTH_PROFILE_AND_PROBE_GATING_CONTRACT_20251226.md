# V10 Truth Profile + ProbeGating Contract (v2) / 真值画像 + 探针激活契约

Date: 2025-12-26  
Scope: execution_world first (`okx_demo_api`), later (`okx_live`)  
Status: Draft contract for v2 rewrite (to be frozen after probe acceptance)

---

## 0) One-line summary

Core does **not** choose probes and does **not** do IO.  
World modules produce a fixed probe vector and a truth profile; **ProbeGating** decides what is usable, what is unknown, and when to STOP.

---

## 1) Two layers (hard boundary)

- **Core / Individual**
  - `Genome` + `DecisionEngine` + `Agent(state machine + intent)`
  - No IO, no exchange calls, no hidden defaults that fabricate truth

- **World / Environment Interface**
  - `Connector` (OKX native)
  - `Ledger` (truth aggregation, Tier-1 evidence)
  - `ExecutionEngine` (order lifecycle)
  - `Reconciliation`, `RunArtifacts`
  - Produces probes + quality + evidence

---

## 2) `truth_profile` (the symbolic “live switch”)

`truth_profile` is a **contract-level switch** that changes validity requirements (not a casual runtime flag).

Allowed values:

- `degraded_truth` (demo observation mode)
  - missing probes allowed (must be labeled)
  - conclusions about real PnL / real impedance are **NOT_MEASURABLE**

- `full_truth_pnl` (live observation mode)
  - critical truth probes must be available
  - missing critical truth → **STOP + IEB**

Required manifest fields (per run):

- `mode` (`okx_demo_api` / `okx_live`)
- `truth_profile`
- `impedance_fidelity` (`simulated` / `demo_proxy` / `real` / `unknown`)
- `feature_contract_version` / `genome_schema_version` / `pool_namespace` (v2)

---

## 3) ProbeGating (single, explicit activation method)

### 3.1 Responsibilities

Given:
- `truth_profile`
- `ledger_snapshot` (truth + quality)
- `raw_probes` (E/M/C raw & derived allowed by contract)

ProbeGating MUST output:
- `probe_values` (fixed dimension)
- `probe_quality` (or `mask`) and `reason_code` for any unknown/degraded probe
- `gating_decision`: `continue` or `stop`

### 3.2 Hard rules

- **Unknown must not be fabricated as 0**
  - If a numeric vector requires a placeholder, `value=0` is allowed **only if** `mask=1` and `reason_code` are present and auditable.

- **History does not enter the vector as a sequence**
  - Only “history projection” state probes are allowed (e.g., exposure_ratio, capital_health_ratio).

- **Core never branches on demo/live to drop dimensions**
  - Core consumes fixed probes; ProbeGating handles availability via quality/mask.

---

## 4) Minimal “history projection” probes (allowed derived-only)

These are the minimal derived probes that compress trading history without dimension explosion:

- `capital_health_ratio = equity / bootstrap_equity`
- `position_exposure_ratio = abs(pos_size * mark_price) / equity_or_bootstrap`

Constraints:
- derived from **raw truth fields** only
- no complex inference/modeling
- missing inputs → unknown (not 0)

---

## 5) STOP policy

### 5.1 Always STOP (both demo & live)

- evidence chain missing for execution (e.g., orders sent but no `order_attempts.jsonl`)
- ledger tick evidence missing (`ledger_ticks.jsonl` not written / tick mismatch)
- world mixing (core mutates positions/capital as if fills happened)

### 5.2 Demo policy (`degraded_truth`)

- missing I/M probes → allowed, but must be labeled `unknown` with `truth_quality + reason_code`
- the run is judgeable only for “structure/mechanism observation”, not real PnL claims

### 5.3 Live policy (`full_truth_pnl`)

- missing critical truth probes (positions/fills/fees required by the run’s claim set) → STOP + IEB

---

## 6) Evidence requirements (minimum)

ProbeGating decisions must be evidence-backed:

- `decision_trace.jsonl`: must include probe provenance summary (or references)
- `ledger_ticks.jsonl`: Tier-1 truth snapshots each tick
- `execution_fingerprint.json`: IO/latency/error telemetry
- `errors.jsonl`: any gating/STOP reasons (append-only)


