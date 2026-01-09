# V12 Pre-reg — World Pressure as Boundary Signal — Trial-8 BTC Do-or-Die (Changepoint) v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Operator constraints (frozen):
- Single dataset only (BTC 2021–2022)
- Full only
- No parallel / no expansion / no comparisons
- Boundary detector only (changepoint), not a continuous gauge
- Do-or-die: either boundary structure is measurable or tool exits

SSOT candidate:
- `docs/v12/V12_SSOT_WORLD_PRESSURE_BOUNDARY_SIGNAL_V0_20260109.md`

---

## 0. Purpose (frozen)

Given that `world_u` behaves like a regime/boundary signal, we accept that goal and test:

> Does `world_u` contain **non-trivial, auditable changepoints** within a single BTC world, and are they structurally consistent across seeds?

If FAIL ⇒ tool rejected (stop; no patching within Trial-8).

---

## 1. Frozen inputs

Quant commit locked (world_u exists):
- `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

Dataset (single, frozen):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`

Runs (full only, frozen; 3 seeds):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full`

Required evidence per run_dir (fail-closed):
- `interaction_impedance.jsonl` (10000 records, contains metrics.world_u)

---

## 2. Frozen detector (algorithm + params)

Algorithm:
- Greedy binary segmentation on `u_t` with SSE cost + penalty beta (see SSOT §3).

Frozen parameters:
- `min_segment_len = 200`
- `max_changepoints = 10`
- `beta = 0.5`  (units: SSE; frozen v0)

Notes (frozen):
- beta is intentionally modest; this is a *detectability* test, not a denoising contest.

---

## 3. Frozen acceptance criteria (do-or-die)

Per-run requirements:
- At least **1** changepoint found: `cp_count >= 1`
- Explained variance threshold:
  - Let `SSE0 = SSE(0,N)` (no split)
  - Let `SSEk = sum SSE(segments)` (piecewise constant fit)
  - Require `R2 = 1 - SSEk/SSE0 >= 0.05`
- Segment effect size:
  - For each adjacent segment pair, mean jump `|μ_{k+1}-μ_k|`
  - Require median jump `>= 0.05 * std(u)` (within run)

Cross-seed structural consistency:
- Let each run’s changepoints be ordered by time.
- Let `K = min(cp_count across runs)` (K>=1 required).
- For k=1..K, compare normalized positions `p_k = t_k / N` across 3 runs:
  - Require `std(p_k) <= 0.05` (±5% of timeline)

FAIL if any violated.

---

## 4. Stop rule (frozen)

- If FAIL ⇒ **tool exits** (engineering-rejected). No patching inside Trial-8.
- If PASS ⇒ accept boundary-detector tool within this evidence contract (no cross-world claims).

---

## 5. Completion anchors (append-only)

- quant_commit_locked:
- analysis_tool:
- artifacts_dir:
- per_run_reports:
- aggregate_report:
- verdict:


---

## 6. Completion record (append-only)

- quant_commit_locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- analysis_tool: `tools/v12/detect_world_pressure_boundaries_v0.py`
- artifacts_dir: `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/`
- per_run_reports:
  - `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full.json`
  - `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full.json`
  - `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full.json`
- aggregate_report: `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/aggregate.json`
- verdict: **PASS**
