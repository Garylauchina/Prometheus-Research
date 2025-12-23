# INCIDENT-20251223: C2.2 Degradation drill (network disconnect fallback) — okx_demo_api

## What happened（现象，1–3句）

We ran an **ops-only degradation drill** by injecting a short network outage (fallback method: Docker network disconnect/connect).

We successfully produced a complete **IEB bundle** with hashes, and the run ended with auditable STOP semantics.

However, the “degradation measurement evidence” (e.g., error counters / timeouts recorded in `execution_fingerprint`) is **insufficient** in this run due to low traffic and timing.

---

## Context（时间 / run_id / mode）

- **Mode**: `okx_demo_api`
- **Run ID**: `run_20251223_015749_unknown`
- **Start (UTC)**: `2025-12-23T01:57:49.709738Z`
- **End (UTC)**: `2025-12-23T02:00:54.545258Z`
- **Status**: `interrupted` (STOP)
- **Stop detected (UTC)**: `2025-12-23T02:00:54.540096Z`
- **Stop reason**: `stop_file`

Audit note:

- `git_commit` and `docker_image_tag` in `run_manifest.json` are `unknown` for this run. This weakens auditability and should be fixed in the ops wrapper (not core).

---

## Severity（等级）

- Drill / Controlled test (Degradation)

---

## Injection method（注入方式：ops-only）

Target (preferred):

- add outbound delay via `tc netem` (1500ms delay)

Observed on this environment:

- `tc` not available in container → fallback used:
  - Docker network disconnect for ~60 seconds, then reconnect.

From operator report (local time +08):

- inject_start_local: `2025-12-23 09:58:59 CST`
- inject_end_local: `2025-12-23 10:00:24 CST`
- fallback: `docker network disconnect/reconnect`

---

## Degradation evidence（退化证据：本次不足）

Expected evidence (what we want to see in a successful degradation measurement):

- `execution_fingerprint.json` records non-zero `error_count` and/or `error_events`
- increased latency stats and/or explicit timeout/retry counters

What we actually got in this run:

- `execution_fingerprint.json` exists at end, but shows:
  - `error_count = 0`
  - `error_events = []`
  - `api_calls = 3`, `orders_sent = 3`
- During the “post-injection check” window, the drill report shows:
  - `execution_fingerprint.json not found yet` (so we did not capture mid-run degradation counters)

Interpretation:

- The outage likely occurred when there were very few in-flight calls, so the system did not accumulate measurable errors in the fingerprint.
- This drill still validates the **evidence packaging / IEB workflow**, but does **not yet** validate “degradation telemetry correctness”.

Decision:

- **Partial Pass**:
  - PASS: IEB production + STOP audit semantics
  - NOT PROVEN: degradation error telemetry under real call pressure

---

## Evidence bundle（IEB 交付物：路径 + sha256）

Packaged by Programmer-AI (Prometheus-Quant), read-only process:

- **IEB archive**: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251223_015749_unknown_C2_2_DEGRADATION_20251223_095749.tar.gz` (≈ 6.3KB)
- **archive_sha256**: `5eb76f12935bbd144aaca2b6fe7e645c34fa0ad74d9fe779fc9e2aa0c747cec0`
- **Drill report**: `/Users/liugang/Cursor_Store/Prometheus-Quant/C2_2_DEGRADATION_TIMEOUT_DRILL_20251223_095749.report.txt` (≈ 5.7KB)

Key STOP fields (from `run_manifest.json`):

- `status = interrupted`
- `stop_detected = true`
- `stop_time = 2025-12-23T02:00:54.540096Z`
- `stop_reason = stop_file`

IEB completeness:

- `missing_required_files_count = 0`

---

## Rules respected（规则遵守声明）

- No changes to `prometheus/v10/core/` during the drill.
- Ops-only actions (network disconnect/reconnect + STOP file) + evidence packaging.
- No deletion or mutation of `runs/` artifacts.

---

## Next step（下一步：让退化证据“必然发生”）

To make degradation evidence measurable and auditable in the next drill (still ops-only):

- Ensure **sustained API call pressure** during the injection window (longer baseline warm-up, avoid injecting too early).
- Prefer an injection method that does not fully disconnect (e.g., `tc netem` in container, or host-level netem against container interface).
- Add a drill rule: do not accept the run unless `execution_fingerprint.error_count > 0` (or equivalent explicit error telemetry) during the injection window.


