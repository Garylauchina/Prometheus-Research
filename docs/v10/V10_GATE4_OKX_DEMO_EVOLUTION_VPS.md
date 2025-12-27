# V10 Gate 4 (VPS): OKX Demo Evolution Core (Real Orders, No Proxies, Evidence-First)

> Contract version: 2025-12-25.1  
> Scope: VPS + Docker, OKX **Demo** account only (no live funds)

## 0) Why this doc exists (update)

Mac domestic networks cannot reliably access OKX directly. Routing through proxies introduces a non-negligible risk of exchange risk-control and observation-channel drift. Therefore, **Gate 4 execution is VPS-only**.

Mac can still be used for **offline** work (docs, replay, analysis), but **must not** be treated as the execution world for Gate 4 when it depends on proxy routing.

## 1) Hard Semantics (non-negotiable)

- **S1. Real orders only (OKX Demo)**: any order intent must go through OKX Demo real order APIs.
- **S2. No fake trades**: forbidden to generate simulated fills/acks when API placement fails.
- **S3. Exchange is the truth source**: equity/positions/fills must be treated as externally observable truth (with auditable reconciliation).
- **S4. No artificial fences**: do not introduce “frequency fences” that force Agents to place orders for the sake of passing a gate.
  - Allowed: ecological fences for safety (STOP/kill-switch/rate limit/capital conservation) and post-hoc audit labels.
  - Forbidden: injecting “must trade” constraints into Agent decision paths.
- **S5. No proxy path for OKX execution**: the run must not depend on an opaque proxy/VPN layer for OKX connectivity.
  - If the network path is proxy-dependent or frequently altered, the run must be labeled **Not Measurable** (observation channel drift).

- **S6. Execution-world modularization + audit + freeze (hard)**:
  - Exchange communication and trading execution must be encapsulated (Connector / ExecutionEngine / Reconciliation / PositionTruth), not embedded in the test runner.
  - Before any 96-tick Step 1 run, the required module PROBEs must be passed and accepted.
  - After acceptance, module artifact schemas are frozen (only backward-compatible extensions allowed).
  - Protocol: `docs/v10/V10_MODULE_PROBE_AND_INTERFACE_FREEZE_PROTOCOL_20251225.md`

- **S7. No internal position simulation in execution world (hard)**:
  - In `okx_demo_api` / `okx_live`, core/decision is **intent-only**.
  - It is forbidden for the decision/core state machine to mutate internal `positions/state` as if a fill occurred, unless backed by exchange evidence (order_status/fills/positions truth) or explicitly labeled `unavailable + reason`.
  - This rule exists to prevent “world mixing” and to keep the system measurable.

## 2) Step 1 — One judgment window on VPS (96 ticks @ 15m)

### Goal

Prove the system can run **a full 96-tick judgment window** in OKX Demo execution world on VPS and produce complete artifacts (evidence-first).

### Required behavior

- Runs end-to-end without uncontrolled crash loops.
- Decision chain must be executed each tick and evidenced (even if all agents choose HOLD).
- Any placed order must satisfy S1/S2 and be traceable across artifacts.
- If **no orders happen**:
  - The run must explicitly be classified as **NO_TRADE** in its summary (evidence-based).
  - NO_TRADE is **not a failure of Step 1**, but it is **Inconclusive** for claims about “fills/fees closure under real trading.”

### Interruption & restart semantics (hard)

- **If interrupted (power/network/process): STOP and package an IEB**.
- **Do not continue writing into the same `run_id` with tick reset**.
  - If a restart happens and tick indices restart from 1 under the same `run_id`, the evidence becomes **ambiguous** (tick collisions) and the run must be labeled **Invalid / Not Measurable** for Step 1 judgment-window claims.
  - Allowed recovery policies:
    - A) start a **new run_id** (clean judgment window), or
    - B) continue with a monotonic `restart_index` + monotonic tick timeline with explicit segment boundaries (requires a frozen contract; must be evidence-backed).

## 3) Evidence contract (minimum artifacts)

Tier-1 (screening, required):

- `run_manifest.json`
- `startup_preflight.json`
- `capital_reconciliation_events.jsonl` (append-only, tick-indexed)
- `decision_trace.jsonl` (append-only, tick-indexed)
- `execution_fingerprint.json` (api_calls + errors + latency + rate-limit)
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`

Module PROBE evidence (required before Step 1 long-run):

- PROBE + acceptance for:
  - Connector (communication)
  - ExecutionEngine (order lifecycle)
  - Reconciliation (capital truth)
  - PositionTruth (positions binding under demo constraints)
- Protocol: `docs/v10/V10_MODULE_PROBE_AND_INTERFACE_FREEZE_PROTOCOL_20251225.md`

Market alignment anchor (Tier-1, required for “live input” sanity):

- In `decision_trace.jsonl` tick summaries, record (recommended minimum, to prevent “silent market”):
  - `inst_id_used`
  - `source_endpoint_used`
  - `source_ts_used` (ISO8601 derived from OKX `ts` if available)
  - `source_ts_ms_used` (ms epoch from OKX `ts` if available)
  - `mark_price_used`
  - `input_quality_flags` (`ok` / `degraded` / `stale` / `default`)
  - `reason_code` (required when not `ok`)
- Provide a minimal exchange evidence anchor file (example): `okx_rest_raw_samples.json` + `okx_rest_alignment_report.json`

Preflight honesty (hard):

- `startup_preflight.json.preflight_status == "success"` is only allowed if:
  - order cancel step is **actually executed** (not `skipped`), OR
  - the run explicitly marks the step as `skipped` **and** marks overall preflight as `partial/failed` (must not claim `open_orders_after_count==0` without evidence).

## 4) Deferred validation items (must be addressed after the next Step 1 run)

- **D1. Market→Decision input closure (hardening)**: evidence the exact market input used by decision (instId/source_ts/mark_price + hash).
- **D2. Silent fallback detection**: evidence `reason_code` / `input_quality_flags` when degraded inputs are used.


