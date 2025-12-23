# INCIDENT-20251223: C2.1 STOP drill (ops-only) — okx_demo_api

## What happened（现象，1–3句）

We ran an **ops-only STOP fault-injection drill** and confirmed that the system:

- detects STOP quickly
- exits gracefully
- writes an auditable `run_manifest.json` with explicit STOP semantics (`status=interrupted`, `stop_*` fields)

---

## Context（时间 / run_id / mode）

- **Mode**: `okx_demo_api`
- **Run ID**: `run_20251223_015051_unknown` (from `runs/` directory name)
- **Start (UTC)**: `2025-12-23T01:50:51.346556Z`
- **End (UTC)**: `2025-12-23T01:53:01.353207Z`
- **Stop detected (UTC)**: `2025-12-23T01:53:01.341709Z`
- **Stop reason**: `stop_file`
- **api_calls (manifest)**: `7`

> Note: This drill is about **STOP semantics + evidence packaging**, not about trading outcomes.

---

## Severity（等级）

- Drill / Controlled test (not a production incident)

---

## Timeline（时间线）

From the operator report (local time +08):

- `09:50:51` container started (`okx_demo_api`)
- `09:53:00` STOP injected (control STOP file created)
- `09:53:01` system detected STOP (≈ 0.34s detection latency)
- `09:53:01` graceful exit; manifest `status=interrupted`

Overall response time: ~1s (STOP injection → detected → exit)

---

## Evidence bundle（IEB 交付物：路径 + sha256）

Packaged by Programmer-AI (Prometheus-Quant), read-only process:

- **IEB archive**: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251223_015051_unknown_C2_1_STOP_20251223_095044.tar.gz` (≈ 6.1KB)
- **archive_sha256**: `0f303ff74d33edd0296150d6598c3f092c4f46eaad661187414ac40100a79ce2`
- **Drill report**: `/Users/liugang/Cursor_Store/Prometheus-Quant/C2_1_STOP_DRILL_20251223_095044.report.txt` (≈ 11KB)

Key required STOP fields (from `run_manifest.json`):

- `status = interrupted`
- `stop_detected = true`
- `stop_time = 2025-12-23T01:53:01.341709Z`
- `stop_reason = stop_file`

---

## Rules respected（规则遵守声明）

- No changes to `prometheus/v10/core/` during the drill.
- Ops-only actions (STOP file) + evidence packaging.
- No deletion or mutation of `runs/` artifacts.

---

## Next step（下一步）

- Proceed to the next ops-only drill candidate: **rate-limit / timeout burst** (Degradation) and ensure we can still produce an IEB with explicit error counters and raw samples.


