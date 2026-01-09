# V12 Pre-reg — World Pressure via Gate Transfer Function (Suppression) — Trial-7 BTC Do-or-Die Calibration v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Operator hard constraints (frozen):
- Single dataset only (BTC 2021–2022)
- Full only
- No parallel / no expansion / no comparisons
- Do-or-die: either calibrate successfully or tool exits

SSOT candidate:
- `docs/v12/V12_SSOT_WORLD_PRESSURE_GATE_TRANSFER_V0_20260109.md`

---

## 0. Purpose (frozen)

Test whether **suppression(t)** (gate transfer compression) yields a **continuous** world-pressure readout within a single BTC world under a frozen evidence contract:

- world proxy: `u_t = interaction_impedance.metrics.world_u`
- readout: `suppression(t) = 1 - post_gate_intensity / interaction_intensity` (0 if interaction_intensity=0)

If the frozen acceptance thresholds fail ⇒ the tool is rejected (stop; no patching within Trial-7).

---

## 1. Frozen inputs

Quant commit locked (world_u exists in impedance):
- `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

Dataset (single, frozen):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`

Runs (full only, frozen; 3 seeds):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full`

Required evidence per run_dir (fail-closed):
- `decision_trace.jsonl` (10000 records)
- `interaction_impedance.jsonl` (10000 records, contains metrics.world_u)

Join rule (frozen):
- Strict implicit ordering join with **line-by-line `ts_utc` equality check** between the two files.

---

## 2. Frozen evaluation (per run)

Association (continuous):
- `rho_run = spearman(u_t, suppression_t)` over ticks where interaction_intensity>0

Quantile separation:
- top/bottom 10% by u_t:
  - `delta_run = mean(suppression | u in top10%) - mean(suppression | u in bottom10%)`
  - expectation: `delta_run > 0`

Epoch robustness:
- Evaluate the same on segment windows of size {1000, 5000, 10000} ticks.

---

## 3. Frozen accept / reject thresholds (do-or-die)

PASS requires all 3 runs satisfy:
- Sign:
  - `rho_run > 0` and `delta_run > 0`
- Minimum effect:
  - `rho_run >= 0.15`
  - `delta_run >= 0.02`
- Epoch robustness:
  - for each segment size in {1000,5000,10000}:
    - median `rho_seg >= 0.10`
    - median `delta_seg >= 0.015`

FAIL if any violated.

---

## 4. Stop rule (frozen)

- If FAIL ⇒ **tool exits** (engineering-rejected). No patching inside Trial-7.
- If PASS ⇒ accept this candidate tool within this evidence contract (no cross-world claims).

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
- analysis_tool: `tools/v12/calibrate_world_pressure_gate_transfer_v0.py`
- artifacts_dir: `docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/`
- per_run_reports:
  - `docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full.json`
  - `docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full.json`
  - `docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full.json`
- aggregate_report: `docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/aggregate.json`
- verdict: **FAIL** (3/3 runs: `rho < 0.15` under frozen thresholds)
