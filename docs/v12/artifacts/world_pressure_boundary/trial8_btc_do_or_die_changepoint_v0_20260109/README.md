# Trial-8 — World Pressure as Boundary Signal — BTC Do-or-Die (Changepoint) — Archived Artifacts (v0, 2026-01-09)

Scope (frozen by pre-reg):
- Quant commit locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- Dataset: BTC 2021–2022 only
- Runs: full only, seeds 71001/71002/71003
- No parallel, no expansion, no comparisons.

SSOT candidate:
- `docs/v12/V12_SSOT_WORLD_PRESSURE_BOUNDARY_SIGNAL_V0_20260109.md`

Pre-reg:
- `docs/v12/pre_reg/V12_WORLD_PRESSURE_BOUNDARY_TRIAL8_BTC_DO_OR_DIE_CHANGEPOINT_V0_20260109.md`

Tool:
- `tools/v12/detect_world_pressure_boundaries_v0.py`

Outputs:
- `aggregate.json` (final verdict + cross-seed checks)
- `aggregate_stdout.json` (stdout mirror)
- `per_run_*.json` (per-run boundaries + fit stats)

