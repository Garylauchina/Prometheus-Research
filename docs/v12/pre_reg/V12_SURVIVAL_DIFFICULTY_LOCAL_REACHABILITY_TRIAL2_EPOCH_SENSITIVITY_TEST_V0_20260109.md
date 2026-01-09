# V12 Pre-reg — Local Reachability — Trial-2 Epoch Sensitivity Test v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-2 pre-reg: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- Trial-2 grouped sweep: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V1_GROUPED_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

We test whether the Trial-2 reachability readout is an **epoch-scale illusion**:

> If we change the aggregation granularity (epoch chunk size) while keeping the same world contract + same run evidence, does the “compression structure” reorder?

This is post-hoc only; we do not rerun the world.

---

## 1. Frozen inputs

One Quant run_dir (absolute path) containing:
- `local_reachability.jsonl` (Trial-2 impedance proxy; probe_on)

---

## 2. Frozen method (tool + parameters)

Tool (Research):
- `python3 tools/v12/epoch_sensitivity_local_reachability_v0.py`

Frozen parameters:
- `k_list = 100,500,1000,5000`

The tool computes window-mean feasible_ratio series for each k and compares series by time-aligned Spearman correlation.

---

## 3. Falsification criterion (frozen)

Define:
- For each comparable pair (k_small divides k_big), compute Spearman rho after time alignment.

Fail condition (epoch sensitivity triggered):
- If any aligned pair has `spearman_rho < 0.90` ⇒ FAIL (structure is not stable across epoch granularity).

Stop rule:
- If FAIL triggers ⇒ stop (do not patch within this claim).

---

## 4. Outputs (frozen)

We must archive:
- report_json
- report_md

---

## 5. Completion anchors (append-only)

### 5.1 Run anchors

- quant_run_dir:
- command:
- report_json:
- report_md:

### 5.2 Result anchors

- verdict (PASS|FAIL):
- notes:


## 6. Completion record (appended, 2026-01-09)

### 6.1 Run anchors

- quant_run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T065121Z_seed60001_full`
- command:
  - `python3 tools/v12/epoch_sensitivity_local_reachability_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T065121Z_seed60001_full --k_list 100,500,1000,5000 --output_json docs/v12/artifacts/local_reachability/trial2_epoch_sensitivity_v0_20260109/epoch_sensitivity_report.json --output_md docs/v12/artifacts/local_reachability/trial2_epoch_sensitivity_v0_20260109/epoch_sensitivity_report.md`
- report_json: `docs/v12/artifacts/local_reachability/trial2_epoch_sensitivity_v0_20260109/epoch_sensitivity_report.json`
- report_md: `docs/v12/artifacts/local_reachability/trial2_epoch_sensitivity_v0_20260109/epoch_sensitivity_report.md`

### 6.2 Result anchors

- verdict: PASS
- notes:
  - All aligned Spearman rhos for k_list=[100,500,1000,5000] were 1.0 (>=0.90).
