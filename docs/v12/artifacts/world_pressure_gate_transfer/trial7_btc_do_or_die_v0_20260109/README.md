# Trial-7 — World Pressure via Gate Transfer Function (Suppression) — BTC Do-or-Die Calibration — Archived Artifacts (v0, 2026-01-09)

Scope (frozen by pre-reg):
- Quant commit locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- Dataset: BTC 2021–2022 only
- Runs: full only, seeds 71001/71002/71003
- No parallel, no expansion, no comparisons.

Pre-reg:
- `docs/v12/pre_reg/V12_WORLD_PRESSURE_GATE_TRANSFER_TRIAL7_BTC_DO_OR_DIE_CALIBRATION_V0_20260109.md`

SSOT candidate:
- `docs/v12/V12_SSOT_WORLD_PRESSURE_GATE_TRANSFER_V0_20260109.md`

Tool:
- `tools/v12/calibrate_world_pressure_gate_transfer_v0.py`

Outputs:
- `aggregate.json` (final verdict)
- `aggregate_stdout.json` (stdout mirror)
- `per_run_*.json` (per-run checks)

Audit note:
- join uses strict implicit ordering with line-by-line `ts_utc` equality (`decision_trace.jsonl` vs `interaction_impedance.jsonl`).

