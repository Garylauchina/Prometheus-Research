# V10 Probe HealthCheck Contract (OKX native) / 探针健康校验契约（OKX原生）

Date: 2025-12-26  
Scope: `truth_profile=degraded_truth` (okx_demo_api) first  
Freeze target: after PROBE acceptance (interface_locked)

---

## 0) Purpose

We must prevent “silent probe failures” (静默市场/静默探针失效).  
This module defines a **single, versioned** probe healthcheck with two modes:

- **Startup full check**: comprehensive, may STOP (hard gate).
- **Per-tick light check**: lightweight, usually log-only; may STOP only for safety/chain violations.

We do **not** cross-reference other APIs; we only validate the chosen canonical OKX native endpoints.

---

## 1) Module boundary (locked)

Module name: `ProbeHealthCheck`  
Allowed IO: **read-only** (OKX native via Connector), write evidence files under `run_dir`.

Forbidden:
- placing orders
- modifying core state
- fabricating values (no silent 0)

---

## 2) Inputs

Common inputs:
- `run_id`, `run_dir`
- `inst_id` (e.g., `BTC-USDT-SWAP`)
- `truth_profile` (demo: `degraded_truth`)
- `okx_connector` (native REST)

Per-tick inputs:
- `tick`
- (optional) last-known probe snapshot (for anomaly detection)

---

## 3) Outputs (evidence, append-only)

### 3.1 Startup artifact

`probe_startup_full.json` (one file per run)

Required fields:
- `ts_utc`, `run_id`, `inst_id`, `truth_profile`
- `checks`: per endpoint result list
- `summary`: `status=pass|fail|partial`, `stop_required=true|false`

### 3.2 Per-tick artifact

`probe_health_ticks.jsonl` (append-only, one line per tick)

Required fields (minimum):
- `ts_utc`, `run_id`, `tick`
- `e_status`: `ok|degraded|unavailable`
- `e_reason_code` (nullable; required if not ok)
- `source_endpoint_used`, `source_ts_used`, `source_ts_ms_used`
- `stop_required` (boolean)

---

## 4) Canonical checks (OKX native)

### 4.1 Startup full check (may STOP)

Checks (minimum):
- **E-ticker**: `GET /api/v5/market/ticker?instId=...`
- **E-books**: `GET /api/v5/market/books?instId=...&sz=5`
- **Account config**: `GET /api/v5/account/config` (read-only)
- **Balance/equity**: `GET /api/v5/account/balance` (read-only)
- **Positions**: `GET /api/v5/account/positions?instType=SWAP` (demo may be unreliable; must label)

STOP rules at startup (demo):
- If **E-ticker OR E-books unavailable** → `stop_required=true` (hard gate)
- If evidence write fails (run_dir not writable / cannot write probe artifacts) → STOP

Non-STOP at startup (demo):
- Positions unreliable/unavailable → allowed but must mark `positions_truth_quality != ok`

### 4.2 Per-tick light check (log-only by default)

Checks (minimum):
- ticker success + exchange timestamp present (or explicit degraded label)

STOP rules per tick (demo):
- E becomes unavailable **AND** execution attempts to place orders in same tick → STOP
- evidence chain violations (e.g., order submitted but no order_attempts evidence) → STOP
- any silent fallback (missing but filled as 0 without mask/quality) → STOP

Otherwise:
- write degraded/unavailable status and continue

---

## 5) Versioning / Freeze

Contract fields:
- `contract_name = V10_PROBE_HEALTHCHECK_OKX_NATIVE`
- `contract_version = 2025-12-26.1`

After acceptance:
- additive-only changes allowed
- any field removal/semantic change requires version bump + re-PROBE


