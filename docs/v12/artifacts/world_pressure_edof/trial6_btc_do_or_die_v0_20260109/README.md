# Trial-6 — World Pressure via EDoF-CR — BTC Do-or-Die Calibration — Archived Artifacts (v0, 2026-01-09)

Scope (frozen by pre-reg):
- Quant commit locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- Dataset: BTC 2021–2022 only
- Runs: full only, seeds 71001/71002/71003
- No parallel, no expansion, no comparisons.

Pre-reg:
- `docs/v12/pre_reg/V12_WORLD_PRESSURE_EDOF_TRIAL6_BTC_DO_OR_DIE_CALIBRATION_V0_20260109.md`

SSOT candidate:
- `docs/v12/V12_SSOT_WORLD_PRESSURE_EFFECTIVE_DOF_V0_20260109.md`

Tool:
- `tools/v12/calibrate_world_pressure_edof_cr_v0.py`

Outputs:
- `aggregate.json` (final verdict)
- `aggregate_stdout.json` (stdout mirror)
- `per_run_*.json` (per-run detailed checks)

Audit notes:
- `interaction_impedance.jsonl` lacks `tick_index`; join uses strict implicit ordering with line-by-line `ts_utc` equality against `decision_trace.jsonl`.
- The first attempt failed due to a correlation-matrix normalization edge case (zero-variance dimensions). That initial failure is preserved as:
  - `aggregate_fail_zero_variance.json`
  - `aggregate_stdout_fail_zero_variance.json`
  - The final run tolerates zero-variance dimensions by dropping them (equivalent to zero eigenvalues).

