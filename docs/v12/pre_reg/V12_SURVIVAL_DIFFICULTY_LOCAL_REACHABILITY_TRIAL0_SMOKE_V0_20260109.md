# V12 Pre-reg — Survival Difficulty via Local Reachability — Trial-0 Smoke (v0, 2026-01-09)

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Survival Space SSOT (for shared evidence conventions only): `docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md`

---

## 0. Purpose (frozen)

This is a **smoke test** to prove we can produce a strict, auditable evidence file:

- `local_reachability.jsonl`

that measures (descriptively) the **next-step local feasibility neighborhood** under a frozen world contract **M**, without drifting into:

- “how to survive”
- “which behavior is better”
- rollout / search / planning

This trial is not about showing an effect size. It is about producing a **clean measurement artifact**.

---

## 1. Frozen inputs

We run **post-hoc** on an existing Quant run directory that already contains:

- `run_manifest.json`
- `survival_space.jsonl` (or an equivalent per-tick `L_imp` truth)
- `decision_trace.jsonl` (or an equivalent per-tick `proposed_intensity` truth)

No new market data is introduced.

---

## 2. Frozen neighborhood definition \(A(s)\)

At each tick/state, we define a fixed-size neighborhood using micro-variations around the recorded proposed intensity:

- `N = 9`
- `deltas = [-0.40, -0.20, -0.10, -0.05, 0.00, +0.05, +0.10, +0.20, +0.40]`
- `candidate_intensity_i = clip(proposed_intensity * (1 + deltas[i]), 0.0, 1.0)`

Prohibited:
- expanding N adaptively
- using feasibility outputs to generate more candidates in the same tick

---

## 3. Frozen feasibility definition (M-frozen proxy)

Feasibility is computed using **M-only actionability proxy**:

- Use `L_imp` from `survival_space.jsonl` at the same tick (no lookahead).

Define:

- `feasible = 1` if `candidate_intensity_i > 0` AND `L_imp > 0`
- otherwise `feasible = 0`

Notes (frozen):
- This is intentionally minimal and deterministic for Trial-0.
- Downshift/suppression is **not** used to define feasibility in Trial-0 (avoid threshold creep).

---

## 4. Frozen outputs

Write:

- `<RUN_DIR>/local_reachability.jsonl` (strict JSONL, append-only)

Required fields must match SSOT v0:
- `snapshot_id`, `account_id_hash`, `tick_index`, `state_id`
- `world_contract.M_frozen=true` and `world_epoch_id` from `run_manifest.json` (if present; else `"unknown"`)
- `neighborhood.candidate_count`, `feasible_count`, `feasible_ratio`
- `graph_optional.enabled=false` and other graph fields set to null
- `death_label_ex_post.enabled=false` and `dead_at_or_before_tick=null`

Fail-closed:
- Any missing required input file ⇒ tool exits non-zero (FAIL).

---

## 5. Frozen descriptive readouts (no thresholds)

We will compute and report (post-hoc, non-contract):

- `feasible_ratio` time series
- distribution of `feasible_ratio`
- first differences `Δ feasible_ratio`

No threshold-based “pass/fail” is allowed on these readouts in Trial-0.

---

## 6. Falsification criteria (Trial-0)

This tool is considered **NOT_READY** (Trial-0 FAIL) if any of:

- Evidence cannot be generated as strict JSONL under the required schema.
- Required join keys (`snapshot_id`, `account_id_hash`) cannot be produced deterministically.
- The implementation needs rollout/search to define feasibility (drift).

---

## 7. Completion anchors (append-only)

### 7.1 Run anchors

- quant_run_dir:
- command:
- local_reachability_jsonl:

### 7.2 Output sanity

- lines_count:
- candidate_count_expected (N):
- notes:


### 7.3 Completion record (appended, 2026-01-09)

- quant_run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e`
- local_reachability_jsonl: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e/local_reachability.jsonl`
- command (verify):
  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_local_reachability_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e`
  - verdict: `PASS`
- command (summary; descriptive only):
  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_report_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e --output_json /tmp/local_reachability_report_seed50099_no_e.json`
  - output_json: `/tmp/local_reachability_report_seed50099_no_e.json`
- lines_count: 50000
- candidate_count_expected (N): 9
- notes:
  - For this run bundle (ablation mode `no_e`), the measured `feasible_ratio` is 0.0 for all ticks under the Trial-0 frozen feasibility proxy.
