# INCIDENT-20251223: C2.3 rerun telemetry gate PASSED — okx_demo_api

## What happened（现象，1–3句）

We reran C2.3 after an **ops/evidence-layer telemetry enhancement** and the hard telemetry gate is now **PASS**:

- `execution_fingerprint.error_count > 0` OR `len(error_events) > 0`

This proves the telemetry mechanism is working and the gate is now **achievable without touching core**.

---

## Context（时间 / run_id / mode）

- **Mode**: `okx_demo_api`
- **Run ID**: `run_20251223_022650_unknown`
- **Telemetry summary (operator report)**:
  - `api_calls = 9`
  - `orders_sent = 9`
  - `error_count = 9`
  - `error_events_len = 9`
  - latency: `min≈2.36ms`, `max≈194.54ms`, `mean≈117.45ms`, `p95≈194.54ms`
- **Hard gate**:
  - `(error_count > 0) = TRUE`
  - `(len(error_events) > 0) = TRUE`
  - **TELEMETRY_OK = PASS**

Audit note:

- `git_commit` / `docker_image_tag` are `unknown` in this run’s manifest naming; this is a known ops audit weakness for these ad-hoc drills and should be normalized later (ops-only).

---

## Severity（等级）

- Drill / Controlled test — **PASSED telemetry gate**

---

## Ops-only change summary（仅 ops/证据层改动，非 core）

Files changed (per operator report):

- `prometheus/v10/ops/okx_api_connector.py` (+128 lines)
- `prometheus/v10/ops/run_v10_service.py` (+10 lines)

Change intent:

- record network exceptions and API errors into:
  - `execution_fingerprint.error_count`
  - `execution_fingerprint.error_events[]` (with structured context)

Git (Prometheus-Quant) commit (operator report):

- commit: `50af110`
- message: `ops: record network exceptions into execution_fingerprint (C2.3 telemetry)`

Constraints respected:

- **No changes to `prometheus/v10/core/`**
- Telemetry-only; must not alter decision logic or trading behavior.

---

## Evidence bundle（IEB 交付物：路径 + sha256）

- **IEB archive**: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251223_022650_unknown_C2_3_RERUN_20251223_102649.tar.gz`
- **archive_sha256**: `e9e9468758ee4b361ba4623e00f1edfcc5dc466f175e581360b6fb016802e781`
- **Drill report**: `/Users/liugang/Cursor_Store/Prometheus-Quant/C2_3_TELEMETRY_RERUN_20251223_102649.report.txt`

---

## Important audit clarification（重要澄清）

This rerun demonstrates that **telemetry is now observable**, but the captured events in this run were primarily:

- `api_error` (OKX business/API-level errors)

Therefore:

- **PASS**: telemetry mechanism + hard gate achievability
- **NOT PROVEN (yet)**: “network degradation” telemetry specifically (timeouts/connection errors under injected degradation)

If the next goal is to validate network degradation measurability, the drill must explicitly trigger `timeout/connection_error` events during an injection window.

---

## Example error event（示例）

From operator report:

- `type = api_error`
- `where = POST /api/v5/trade/order`
- `message = OKX API error: 1 - All operations failed`


