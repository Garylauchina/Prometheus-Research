# Trial-9 — BTC Epoch Annotation (from world_u changepoints) — Archived Artifacts (v0, 2026-01-09)

Purpose (annotation-only):
- Convert Trial-8 changepoints `{t_k}` into **epoch candidate boundaries**.
- Produce per-epoch descriptive stats and cross-seed consistency audit.
- No downstream mechanism changes.

Inputs:
- Trial-8 per-run changepoints:
  - `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/per_run_*.json`
- Quant run_dirs (full only, 3 seeds): `run_dirs.txt`

Tool:
- `tools/v12/build_epoch_candidates_from_changepoints_v0.py`

Outputs:
- `epoch_candidates.json` (consensus boundaries + cross-seed audit)
- `per_run_epoch_stats.json` (per-run boundaries and epoch stats on u)
- `consensus_epoch_stats_by_run.json` (apply consensus boundaries to each run)

