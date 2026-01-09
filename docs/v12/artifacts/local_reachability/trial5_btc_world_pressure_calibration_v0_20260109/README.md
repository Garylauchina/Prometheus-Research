# Trial-5 — BTC World-Pressure Calibration (single-dataset, do-or-die) — Archived Artifacts (v0, 2026-01-09)

Scope (frozen by pre-reg):
- Quant commit locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- Dataset: BTC 2021–2022 only
- Runs: full mode only, seeds 71001/71002/71003
- No cross-dataset, no ablation comparisons, no new knobs.

Pre-reg:
- `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL5_BTC_WORLD_PRESSURE_CALIBRATION_V0_20260109.md`

Inputs:
- `run_dirs.txt`

Tool:
- `tools/v12/calibrate_local_reachability_world_pressure_v0.py`

Outputs:
- `aggregate.json` (final verdict + aggregate stats)
- `aggregate_stdout.json` (stdout mirror)
- `per_run_*.json` (per-run detailed checks)

Audit note:
- `interaction_impedance.jsonl` in these Quant runs does not include `tick_index`.
  - The tool joins by strict implicit ordering (line index 0..N-1), and simultaneously enforces that `local_reachability.jsonl.tick_index` matches implicit ordering.
  - The earlier strict `tick_index` assumption is preserved as `aggregate_fail_missing_tick_index.json`.

