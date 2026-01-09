# V12 Pre-reg — World Pressure via EDoF-CR — Trial-6 BTC Do-or-Die Calibration v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Operator hard constraints (frozen):
- Single dataset only (BTC 2021–2022)
- Full only
- No parallel / no expansion / no comparisons
- Do-or-die: either calibrate successfully or tool exits

SSOT candidate:
- `docs/v12/V12_SSOT_WORLD_PRESSURE_EFFECTIVE_DOF_V0_20260109.md`

---

## 0. Purpose (frozen)

Test whether EDoF-CR yields a **continuous** world-pressure readout within a single BTC world under frozen evidence contract:

- world proxy: `u_t = interaction_impedance.metrics.world_u`
- action vectors: \(a_t=[interaction_intensity, post_gate_intensity, action_allowed]\)
- rolling window EDoF(t) and collapse rate EDoF-CR(t)

If the frozen acceptance thresholds fail ⇒ the tool is rejected (stop; no patching within Trial-6).

---

## 1. Frozen inputs

Quant commit locked (runner already produces `world_u` in impedance):
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

## 2. Frozen computation

Window sizes:
- `W = 200` (rolling window; frozen)

Compute per tick \(t \ge W-1\):
- EDoF(t) using correlation-matrix eigenvalues participation ratio (see SSOT)
- EDoF-CR(t) = -(EDoF(t) - EDoF(t-1))

World pressure proxy:
- u_t = metrics.world_u

---

## 3. Frozen evaluation (per run)

We evaluate association between world pressure and collapse rate:

- `rho_run = spearman(u_t, EDoF-CR(t))` over valid ticks

Quantile separation:
- top/bottom 10% by u_t:
  - `delta_run = mean(EDoF-CR | u in top10%) - mean(EDoF-CR | u in bottom10%)`
  - expectation: `delta_run > 0`

Epoch robustness:
- Evaluate the same on windows of size {1000, 5000, 10000} ticks (segment-wise statistics).

---

## 4. Frozen accept / reject thresholds (do-or-die)

PASS requires all 3 runs satisfy:
- Sign:
  - `rho_run > 0` and `delta_run > 0`
- Minimum effect:
  - `rho_run >= 0.15`
  - `delta_run >= 1e-4`  (EDoF-CR units; keep tiny but positive as minimal separation)
- Epoch robustness:
  - for each segment window size in {1000,5000,10000}:
    - median `rho_seg >= 0.10`
    - median `delta_seg >= 1e-4`

FAIL if any violated.

Rationale (frozen):
- We want a continuous pressure gauge; therefore `rho` is the primary gate.
- `delta` is secondary (must remain positive but not over-tuned).

---

## 5. Stop rule (frozen)

- If FAIL ⇒ **tool exits** (engineering-rejected). No patching inside Trial-6.
- If PASS ⇒ accept this candidate tool within this evidence contract (no cross-world claims).

---

## 6. Completion anchors (append-only)

- quant_commit_locked:
- analysis_tool:
- artifacts_dir:
- per_run_reports:
- aggregate_report:
- verdict:


---

## 7. Completion record (append-only)

- quant_commit_locked: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- analysis_tool: `tools/v12/calibrate_world_pressure_edof_cr_v0.py`
- artifacts_dir: `docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/`
- per_run_reports:
  - `docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full.json`
  - `docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full.json`
  - `docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/per_run_run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full.json`
- aggregate_report: `docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/aggregate.json`
- verdict: **FAIL** (3/3 runs: sign check fails; rho negative/near-zero)
