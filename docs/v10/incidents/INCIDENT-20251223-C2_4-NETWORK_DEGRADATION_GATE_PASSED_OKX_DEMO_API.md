# INCIDENT-20251223: C2.4 network degradation telemetry gate PASSED — okx_demo_api

## What happened（现象，1–3句）

We ran **C2.4 network-degradation drill** (ops-only) and passed the hard gate:

- in `execution_fingerprint.error_events`, at least one event type ∈ `{timeout, connection_error, request_exception}`
- and `error_count >= 1`

This run captured **real network-layer exceptions** (`connection_error`) with full context and produced a complete IEB bundle with hashes.

---

## Context（run_id / mode / gate）

- **Mode**: `okx_demo_api`
- **Run ID**: `run_20251223_024252_unknown`
- **NET_TELEMETRY_OK**: `1` (PASS)
- **Fingerprint summary (operator report)**:
  - `api_calls = 10`, `orders_sent = 10`
  - `error_count = 10`, `error_events_len = 10`
  - error types:
    - `api_error = 8`
    - `connection_error = 2`  ✅ (network-layer)

Hard gate check:

- `error_count > 0` ✅ (10)
- network error types found includes `connection_error` ✅

Audit note:

- `git_commit` / `docker_image_tag` are `unknown` in manifest naming for this ad-hoc drill. This is an ops audit gap (not core) and should be normalized later.

---

## Injection method（注入方式：ops-only）

- Method: `docker network disconnect` for ~120 seconds, then `docker network connect`
- Rationale: reliable, reversible, no host-level privileges required; forces `ConnectionError` under call attempts.

Injection window (operator report, local time +08):

- `10:51:03` → `10:53:04` (~120s)

---

## Network-layer evidence（网络层异常证据）

Captured `connection_error` events (2 samples, from operator report):

- Event #1:
  - `ts_utc`: `2025-12-23T02:51:53.436438+00:00`
  - `type`: `connection_error`
  - `where`: `POST /api/v5/trade/order`
  - `exception_type`: `ConnectionError`
  - `url`: `https://www.okx.com/api/v5/trade/order`
- Event #2:
  - `ts_utc`: `2025-12-23T02:52:53.678655+00:00`
  - `type`: `connection_error`
  - `where`: `POST /api/v5/trade/order`
  - `exception_type`: `ConnectionError`
  - `url`: `https://www.okx.com/api/v5/trade/order`

Interpretation:

- During the network disconnect window, the system attempted API calls and hit `requests.exceptions.ConnectionError`.
- These were recorded into `execution_fingerprint` (ops telemetry path works end-to-end).

---

## Evidence bundle（IEB 交付物：路径 + sha256）

- **IEB archive**: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251223_024252_unknown_C2_4_NETWORK_20251223_104245.tar.gz`
- **archive_sha256**: `9fe204733ec072c424af80b19e420d8562914c647ee4de44734f8490904b90b1`
- **Drill report**: `/Users/liugang/Cursor_Store/Prometheus-Quant/C2_4_NETWORK_DEGRADATION_DRILL_20251223_104245.report.txt`
- **IEB completeness**: `missing_required_files_count = 0`

---

## Ops telemetry prerequisite（前置条件：ops-only telemetry enhancement）

This drill relies on the ops telemetry enhancement commit (Prometheus-Quant):

- commit: `50af110`
- summary: record Timeout / ConnectionError / RequestException into `execution_fingerprint.error_events` with structured context
- constraint: **no core changes**

---

## Rules respected（规则遵守声明）

- No changes to `prometheus/v10/core/` during the drill.
- Ops-only injection + evidence packaging.
- No deletion or mutation of `runs/` artifacts.


