# V10 Execution Freeze on Reconciliation Failure Contract / 不平账→冻结交易契约

Date: 2025-12-26  
Scope: okx_demo observation (`truth_profile=degraded_truth`)  
Purpose: If books do not balance in realtime, **freeze execution** (no orders) to avoid evidence contamination.

---

## 0) Principle

- **Realtime**: If reconciliation is not balanced (beyond tolerance) or truth is unavailable, we must **stop trading for this tick / window**.
- **Post-run**: Still must produce a traceable audit report (no fabrication).

This is a **finance safety rule**, not a strategy fence.

---

## 1) Definitions

- `execution_frozen`: boolean, indicates the system must not place any new orders.
- `freeze_scope`: `tick` (default) or `review_window` (100 ticks) depending on severity.
- `reconciliation_delta`: `exchange_equity - (sum_agent_energy + system_reserve)` (or equivalent contracted delta).

---

## 2) Trigger conditions (freeze)

Freeze MUST be triggered if any of the following occurs at tick `t`:

### 2.1 Balance truth unavailable
- `exchange_equity` query failed OR `equity_source` unavailable.

### 2.2 Unexplained delta beyond tolerance
- `abs(reconciliation_delta) > tolerance_usdt`
- AND the delta cannot be explained by available evidence categories (bills/fills/order_status) under current truth_profile.

### 2.3 Evidence chain broken (execution safety)
- An order is attempted but required evidence is missing (e.g., `order_attempts.jsonl` not written).

### 2.4 Probe health failure for E (market probes)
- E probes `unavailable` (ticker/books) for this tick (per ProbeHealthCheck contract).

---

## 3) Action when frozen

When `execution_frozen=true`:

- Core continues:
  - decision cycle runs
  - intents are logged
- ExecutionEngine MUST NOT place orders:
  - `orders_sent_this_tick` must remain 0
  - any attempt to place orders is a hard violation

---

## 4) Unfreeze conditions

Default (tick-scope freeze):
- next tick passes:
  - equity truth available
  - reconciliation delta within tolerance (or explicitly explainable)
  - E probes healthy

Optional (window-scope freeze):
- require `N` consecutive healthy ticks (e.g., N=2) before unfreezing.

---

## 5) Required evidence (append-only)

### 5.1 `execution_gating_events.jsonl`

On every freeze/unfreeze decision, append one record:

- `ts_utc`, `run_id`, `tick`
- `event_type`: `freeze_on` | `freeze_off`
- `freeze_scope`
- `trigger_reason_codes[]`
- `reconciliation_delta`, `tolerance_usdt`
- `truth_profile`, `impedance_fidelity`
- `evidence_refs[]` (paths to reconciliation/probe error artifacts)

### 5.2 Manifest fields (final)

`run_manifest.json` must include:
- `execution_frozen_ticks_count`
- `first_freeze_tick` (nullable)
- `freeze_reasons_summary` (top reason codes)

---

## 6) Status under demo truth profile

Under `truth_profile=degraded_truth`:
- Freezing is allowed and expected when truth is degraded.
- The run remains usable for “mechanism observation” but any affected claim categories must be marked **NOT_MEASURABLE**.


