# INCIDENT-20251223: C2.3 degradation telemetry gate FAILED — okx_demo_api

## What happened（现象，1–3句）

We ran **C2.3 ops-only degradation drill** with a hard gate:

- `execution_fingerprint.error_count > 0` OR `len(error_events) > 0`

The IEB package was produced successfully (complete + hashed), but the hard gate was **not met** (`error_count=0`, `error_events=[]`).

---

## Context（时间 / run_id / mode）

- **Mode**: `okx_demo_api`
- **Run ID**: `run_20251223_020620_unknown`
- **Status**: `interrupted` (STOP)
- **Duration**: ~648 seconds (from operator report)
- **Manifest (key fields)**:
  - `status = interrupted`
  - `stop_detected = true`
  - `stop_reason = stop_file`
  - `api_calls = 13` (manifest)
- **Fingerprint summary (operator report)**:
  - `api_calls = 10`, `orders_sent = 10`
  - `error_count = 0`
  - `error_events = []`
  - `latency_stats_ms.mean ≈ 146.75`, `p95 ≈ 235.62`

Audit note:

- `git_commit` / `docker_image_tag` are `unknown` in this run’s manifest, which weakens auditability and should be fixed in ops wrapper (not core).

---

## Severity（等级）

- Drill / Controlled test (Degradation) — **FAILED hard telemetry gate**

---

## Hard gate（硬门槛）

- Condition: `(error_count > 0) OR (len(error_events) > 0)`
- Result: **FALSE**

Decision:

- **FAIL** for “degradation telemetry proof”
- **PASS** for “IEB evidence packaging workflow” (deliverables exist + hashed)

---

## Root cause analysis（根因分析，按事实）

### 1) Call pressure was too low / injection timing mismatch

From operator report:

- warm-up `api_calls` stayed `0` for a long time (~483s), then started to increase.
- final `api_calls` still far below target, so the injection window could miss active API calls.

### 2) Telemetry may not record network-level failures (ops limitation)

Even with a ~90s network disconnect injection, the system did not emit error events.

Most plausible explanation (needs verification in ops connector):

- only records “HTTP response errors” (4xx/5xx),
- but does not record exceptions such as `ConnectionError` / `Timeout` / DNS failures.

If true, then this hard gate cannot be satisfied by ops-only injection without enhancing ops-layer telemetry.

---

## Evidence bundle（IEB 交付物：路径 + sha256）

Packaged by Programmer-AI (Prometheus-Quant), read-only process:

- **IEB archive**: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251223_020620_unknown_C2_3_DEGRADATION_20251223_100620.tar.gz` (≈ 6.4KB)
- **archive_sha256**: `f0f2696d6fc8bd212ef24113b04a590e2eab53d219d2e870b17427a37d71abe2`
- **Drill report**: `/Users/liugang/Cursor_Store/Prometheus-Quant/C2_3_DEGRADATION_TELEMETRY_DRILL_20251223_100620.report.txt` (≈ 7.0KB)

IEB completeness (operator report):

- `missing_required_files_count = 0`

---

## Rules respected（规则遵守声明）

- No changes to `prometheus/v10/core/` during the drill.
- Ops-only injection + STOP + IEB packaging.
- No deletion or mutation of `runs/` artifacts.

---

## Next step（下一步：让硬门槛“可达成”）

To make the C2.3 hard gate achievable **without touching core**:

1) **Enhance ops-layer error telemetry**:
   - In the OKX connector / request wrapper, catch and record:
     - connection failures (`ConnectionError`)
     - timeouts (`Timeout`)
     - DNS failures (if surfaced)
   - Ensure these count toward `execution_fingerprint.error_count` / `error_events`.

2) Re-run the same C2.3 drill with the same hard gate.


