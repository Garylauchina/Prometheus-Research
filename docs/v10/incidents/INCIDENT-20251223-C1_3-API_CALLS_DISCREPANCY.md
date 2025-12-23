# INCIDENT-20251223: C1.3 audit discrepancy (api_calls mismatch)

## What happened（现象，1–3句）

During C1.3 (24h) post-run audit, we observed a **1-call discrepancy** between `run_manifest.api_calls` and `execution_fingerprint/api raw index` counts.

This is a **Degradation** (audit consistency issue), not a trading failure.

---

## Context（时间 / run_id / mode / version）

- **When (local)**: 2025-12-23 09:34 CST (audit time)
- **Run ID**: `run_20251222_012118_4974080`
- **Mode**: `okx_demo_api`
- **Commit**: `4974080` (from `run_manifest.json`)
- **Image**: tag=`4974080`, digest=`to-be-set-at-runtime` (from `run_manifest.json`)
- **Protocol**: `docs/v10/V10_C_STAGE_C1_3_24H_LONG_RUN_PROTOCOL_20251222.md`
- **Milestone**: `docs/v10/V10_MILESTONE_C1_3_24H_LONG_RUN_PASSED_20251223.md`

---

## Severity（等级）

- **Degradation** (allowed to proceed, but must be recorded and later clarified)

---

## Stop action taken（止血动作）

- No STOP / no kill switch. This was a post-run audit discrepancy, not an active incident.

---

## Evidence bundle（证据包路径 + 文件清单）

**Host run directory (Mac)**:

- `/Users/liugang/Cursor_Store/Prometheus-Quant/volumes/runs/run_20251222_012118_4974080/`

**IEB archive delivered (Mac host, packaged by Programmer-AI / Prometheus-Quant)**:

- Archive: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251222_012118_4974080_20251223_094446.tar.gz` (≈ 51K)
- `archive_sha256`: `e8dd07f60a59ceeccc08d2fe38110feb355cd037da62fbee35c2762ae9c79537`
- Packaging report: `/Users/liugang/Cursor_Store/Prometheus-Quant/IEB_run_20251222_012118_4974080_20251223_094446.report.txt`
- Summary (from report):
  - `missing_required_files_count = 0`
  - `m_execution_shards = 8`
  - `positions_reconstruction_shards = 8`
  - Included: `SHA256SUMS.txt` (per-file hashes)

Mandatory artifacts (subset referenced):

- `run_manifest.json`
- `execution_fingerprint.json`
- `multiple_experiments_summary.json`
- `m_execution_raw_index.json` + `m_execution_raw_part_*.json`
- `positions_reconstruction_raw_index.json` + `positions_reconstruction_raw_part_*.json`

Audit report (read-only verifier output):

- `/Users/liugang/Cursor_Store/Prometheus-Quant/C1_3_24H_REPORT_20251223_093404.txt`

---

## Initial hypothesis（最多3条）

1) A single **connect/probe** request was counted in `run_manifest.api_calls` but not written as a raw record (or not counted in fingerprint).
2) Off-by-one due to final flush timing (wrapper writes manifest after some counters increment but before raw index finalization), or vice versa.
3) The system intentionally counts “non-trading calls” in manifest but raw evidence only records “order loop calls”.

---

## Next action owner（下一步）

- Owner: Engineering (ops/evidence layer)
- Action: unify the definition of `api_calls` across `run_manifest` / `execution_fingerprint` / raw index, and document the rule (“what is counted, what is excluded”).
- Constraint: must be an **ops/evidence-layer** change; do not touch `prometheus/v10/core/` during incident handling.


