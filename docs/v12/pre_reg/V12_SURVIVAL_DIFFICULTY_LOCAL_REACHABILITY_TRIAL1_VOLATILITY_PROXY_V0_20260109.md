# V12 Pre-reg — Local Reachability — Trial-1 (Volatility proxy; E-only) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Trial-0 (smoke): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL0_SMOKE_V0_20260109.md`

---

## 0. Purpose (frozen)

Trial-0 showed the evidence chain can be produced, but under current run bundles:
- M (impedance) is frequently **NOT_MEASURABLE** when there are no attempts.
- This makes an M-based feasibility proxy collapse to 0, providing little structure.

Therefore Trial-1 freezes a minimal **E-only** proxy to measure **local actionability neighborhood compression speed** without relying on attempt-driven M.

This trial is still measurement-only:
- no rollout
- no search
- no “better behavior”
- no thresholds used for success/fail decisions

---

## 1. Frozen inputs

Operate post-hoc on an existing Quant run directory that contains:

- `run_manifest.json`
- `market_snapshot.jsonl` (must contain `last_px`)
- `decision_trace.jsonl` (for `market_snapshot_id` join and `interaction_intensity`)

No new world data is introduced.

---

## 2. Frozen neighborhood definition \(A(s)\) (same as Trial-0)

At each tick/state, define a fixed-size neighborhood using micro-variations around the recorded intensity:

- `N = 9`
- `deltas = [-0.40, -0.20, -0.10, -0.05, 0.00, +0.05, +0.10, +0.20, +0.40]`
- `candidate_intensity_i = clip(interaction_intensity * (1 + deltas[i]), 0.0, 1.0)`

Prohibited:
- adaptive expansion
- feasibility-guided candidate generation

---

## 3. Frozen E-only compression proxy (no thresholds)

We define a continuous compression factor \(L_v \in [0,1]\) from 1-step log return:

- `r_t = abs(log(last_px_t / last_px_{t-1}))` (for t>0)
- for `t=0`, define `r_0 = 0`

Frozen mapping:

- `L_v = exp(-k * r_t)`
- `k = 500.0` (frozen)

This is a monotone compression (higher volatility ⇒ smaller local actionability neighborhood).

No threshold is used to decide “pass/fail”; \(k\) is part of the lens definition.

---

## 4. Frozen feasibility definition (E-only; set size without thresholds)

We convert \(L_v\) into an integer feasible set size:

- `candidate_count = N`
- `feasible_count = floor(N * L_v)`
- `feasible_ratio = feasible_count / N`

Notes (frozen):
- This defines a *local neighborhood width* as an integer without using a hard threshold on the world signal.
- `feasible_count` may be 0; that is a measurement outcome, not a failure.

---

## 5. Frozen outputs

Write:

- `<RUN_DIR>/local_reachability.jsonl` (strict JSONL, append-only)

Required schema: must match SSOT v0.

Additional reason codes (allowed, deterministic):
- `reachability_proxy:volatility_exp`
- `reachability_proxy:k=500`

Graph optional fields: disabled (nulls).
Death label: disabled (nulls).

Fail-closed:
- missing required input files ⇒ FAIL (non-zero exit)
- missing `last_px` parseability ⇒ FAIL

---

## 6. Falsification criteria (Trial-1)

This tool is considered **rejected** if any triggers (must be checked post-hoc, not repaired):

- **Epoch sensitivity failure**: reachability time series changes radically under different epoch chunking without any world contract change.
- **Seed instability**: across seeds in the same dataset, the reachability compression signature is fully reordered with no stable structure.
- **Triviality**: `feasible_ratio` is constant (or near-constant) across the entire run bundle across multiple seeds (suggesting the proxy carries no usable structure).

Stop rule (hard):
- If falsification triggers ⇒ stop (no patching within this claim).

---

## 7. Completion anchors (append-only)

### 7.1 Run anchors

- quant_run_dir:
- command:
- local_reachability_jsonl:

### 7.2 Output sanity

- lines_count:
- k:
- feasible_ratio_summary_path:
- verifier_verdict:
- notes:


## 8. Completion record (appended, 2026-01-09)

- quant_run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e`
- tool_path (Quant): `/Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v1_volatility_proxy.py`
- command (Quant):
  - `python3 tools/v12/posthoc_local_reachability_v1_volatility_proxy.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e`
- local_reachability_jsonl:
  - `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e/local_reachability.jsonl`
- lines_count: 50000
- k (frozen): 500.0
- verifier (Research):
  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_local_reachability_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e`
  - verdict: `PASS`
- feasible_ratio_summary_path (Research, descriptive only):
  - `/tmp/local_reachability_report_trial1_seed50099_no_e.json`
  - feasible_ratio.mean: 0.7722955555555555
  - feasible_ratio.p50: 0.8888888888888888
  - feasible_ratio.p99: 1.0
- notes:
  - This completion record is produced under Trial-1 E-only volatility proxy. No rollout, no search, no death label.
