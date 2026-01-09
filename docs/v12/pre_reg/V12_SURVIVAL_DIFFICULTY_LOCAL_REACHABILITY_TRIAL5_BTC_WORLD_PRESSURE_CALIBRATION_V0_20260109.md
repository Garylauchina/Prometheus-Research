# V12 Pre-reg — Local Reachability — Trial-5 BTC World-Pressure Calibration (single-dataset, do-or-die) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Hard constraint from operator (frozen):
- **Lock Quant commit** (runner already modified): `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- **Single dataset only** (BTC 2021–2022)
- **No parallel / no expansion / no cross-comparison**:
  - no cross-dataset
  - no ablation comparisons
  - no new knobs / no new lens
  - only “does this lens measure world pressure within one world?” verdict

References:
- Trial-4 archived artifacts (source of the 3 runs): `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

We need a **single-world calibration verdict**:

> Under locked runner commit and a single BTC world, does the current Local Reachability lens (Trial-2 impedance-proxy reachability) produce a stable, auditable readout of “world pressure”?

This is a do-or-die trial:
- If it fails ⇒ the **current lens** is engineering-rejected (tool exits, no patching inside this claim).
- If it passes ⇒ we accept the lens as a measurable world-pressure readout (within this contract only).

---

## 1. Frozen inputs

Dataset (single, frozen):
- BTC 2021–2022:
  - `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`

Runs (frozen; **full mode only**, 3 seeds):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full`

Required evidence per run_dir (fail-closed):
- `interaction_impedance.jsonl` with `metrics.world_u`
- `local_reachability.jsonl` with `neighborhood.feasible_ratio`
- tick alignment via `tick_index` (or equivalent join key available in both)

---

## 2. Frozen definition of “world pressure” proxy

We define world pressure at tick t as:
- `u_t := interaction_impedance.metrics.world_u` (already computed from `last_px` inside runner)

No other E-fields are used.

---

## 3. Frozen readout

Reachability readout at tick t:
- `fr_t := local_reachability.neighborhood.feasible_ratio`

We treat “pressure increases” as “actionability contracts”, i.e. `fr_t` should drop.

Define:
- `y_t := 1 - fr_t`  (contraction magnitude)

---

## 4. Frozen evaluation (per run)

We compute:

1) **Spearman correlation** between `u_t` and `y_t` over ticks:
- `rho_run := spearman(u, y)`

2) **Quantile separation**:
- Let `U_hi` be ticks with `u_t` in top 10%
- Let `U_lo` be ticks with `u_t` in bottom 10%
- Compute:
  - `delta_run := mean(fr | U_lo) - mean(fr | U_hi)`
  - Expectation: `delta_run > 0`

3) **Epoch robustness** (no re-binning illusion):
- Evaluate items (1)(2) on epoch windows of size:
  - 1000, 5000, 10000 ticks
- Accept only if the sign and rough magnitude are stable (see thresholds below).

---

## 5. Frozen accept / reject thresholds (do-or-die)

PASS requires **all**:
- **Sign consistency**:
  - For each run: `rho_run > 0` and `delta_run > 0`
  - Across 3 runs: signs do not flip.
- **Minimum effect** (per run, full-series):
  - `rho_run >= 0.15`
  - `delta_run >= 0.02`
- **Epoch robustness**:
  - For each run and each window size in {1000,5000,10000}:
    - `rho_window >= 0.10`
    - `delta_window >= 0.015`

FAIL if any violated.

Notes (frozen):
- Thresholds are intentionally modest; we only need to prove the lens is not dominated by probe/friction self-shape at this calibration scale.
- We do not claim causality, only an auditable monotone association under frozen contract.

---

## 6. Stop rule (frozen)

- If FAIL ⇒ stop. **No patching inside Trial-5.** Tool exits (current lens rejected).
- If PASS ⇒ lock this calibration result as a contract for subsequent D1 work (but does not imply cross-world generalization).

---

## 7. Completion anchors (append-only)

- quant_commit_locked:
- analysis_tool:
- artifacts_dir:
- per_run_reports:
- aggregate_report:
- verdict:


---

## 8. Completion record (append-only)

- quant_commit_locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- analysis_tool: `tools/v12/calibrate_local_reachability_world_pressure_v0.py` (strict implicit-order join; requires local_reachability.tick_index == implicit index)
- artifacts_dir: `docs/v12/artifacts/local_reachability/trial5_btc_world_pressure_calibration_v0_20260109/`
- per_run_reports:
  - `docs/v12/artifacts/local_reachability/trial5_btc_world_pressure_calibration_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full.json`
  - `docs/v12/artifacts/local_reachability/trial5_btc_world_pressure_calibration_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full.json`
  - `docs/v12/artifacts/local_reachability/trial5_btc_world_pressure_calibration_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full.json`
- aggregate_report: `docs/v12/artifacts/local_reachability/trial5_btc_world_pressure_calibration_v0_20260109/aggregate.json`
- verdict: **FAIL** (all 3 runs: `rho < 0.15` under frozen thresholds)
