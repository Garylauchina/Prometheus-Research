# V12 Pre-reg — Local Reachability — Trial-4 World-Conditioned Impedance (E→M coupling) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-2 grouped sweep (probe-on baseline): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V1_GROUPED_V0_20260109.md`
- Trial-3 cross-dataset transfer (observed “identical across datasets”): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL3_CROSS_DATASET_TRANSFER_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

Trial-3 showed the Trial-2 reachability readout can be **identical across datasets** under the current mock/probe impedance generator. This indicates the readout is dominated by the probe/friction model rather than the world.

Trial-4 introduces a minimal, auditable, monotone **E→M coupling**:

- World volatility proxy from `market_snapshot.last_px` drives the impedance friction model.

Goal:
- Make the impedance time series (and thus reachability) **world-conditioned**, so cross-dataset transfer becomes a meaningful test.

Hard boundaries (frozen):
- measurement only
- no rollout / planning / search
- no reward / PnL
- probe attempts are measurement only (must not affect survival/reward/gate semantics)
- death label disabled

---

## 1. Frozen inputs

Quant run_dir must contain:
- `market_snapshot.jsonl` (must include `last_px`)
- `interaction_impedance.jsonl` (produced by the world-conditioned impedance generator)
- `order_attempts.jsonl` (must tag probe attempts)
- `local_reachability.jsonl` (Trial-2 impedance proxy posthoc; unchanged lens)

Runner requirements (frozen):
- `probe_attempts_per_tick = 1`
- steps = 10000
- modes = `full`, `no_e`, `no_m`, `null` (grouped)
- seeds = 3 (minimum) per dataset

Datasets:
- Dataset A: BTC 2021–2022 (2y)
- Dataset B: ETH 2024-Q4 (3m)

---

## 2. Frozen world volatility proxy (E-only)

For tick t:
- `px_t = float(last_px_t)` (must be > 0)
- `r_t = abs(log(px_t / px_{t-1}))` for t>0
- `r_0 = 0`

Clamp:
- `r_cap = 0.01` (frozen)
- `r_hat = min(r_t, r_cap)`
- `u_t = r_hat / r_cap` ∈ [0,1]

---

## 3. Frozen world-conditioned impedance mapping (monotone)

We modify the mock friction probabilities and latency as monotone functions of `u_t`:

- `p_http_t = clamp(p_http_base + a_http * u_t, 0, 0.20)`
- `p_rl_t   = clamp(p_rl_base   + a_rl   * u_t, 0, 0.80)`
- `p_rej_t  = clamp(p_rej_base  + a_rej  * u_t, 0, 0.80)`

Latency (monotone):
- `latency_ms_t = latency_ms_base + a_lat_ms * u_t`

Frozen coefficients (v0):
- `a_http = 0.02`
- `a_rl   = 0.10`
- `a_rej  = 0.05`
- `a_lat_ms = 200.0`

Notes (frozen):
- These parameters are **not tuned** for performance; they are a measurement lens.
- Monotonicity is the only design guarantee.

Evidence requirement (frozen):
- `interaction_impedance.jsonl` MUST record `world_u` (or equivalent) per tick in metrics, so the coupling is auditable.

---

## 4. Reachability lens (frozen)

We keep Trial-2 reachability lens unchanged:
- `local_reachability.jsonl` generated via Trial-2 impedance proxy posthoc tool.

---

## 5. Falsification / stop conditions (frozen)

Reject Trial-4 E→M coupling if any triggers:

- **Still identical across datasets**: grouped per-run mean feasible_ratio distributions are near-identical between dataset A and B (despite different world inputs).
- **Non-monotone coupling bug**: evidence shows higher `world_u` does not increase friction probabilities/latency (audit failure).
- **Probe drift**: probe affects survival/reward/gate semantics (hard failure).

Stop rule:
- If triggered ⇒ stop (no patching within this claim).

---

## 6. Completion anchors (append-only)

### 6.1 Implementation anchors

- quant_commit:
- runner_flags:
- coupling_params (a_http/a_rl/a_rej/a_lat_ms, r_cap):

### 6.2 Dataset anchors

- dataset_A_path:
- dataset_B_path:

### 6.3 Run anchors

- run_dirs_file_A:
- grouped_report_json_A:
- run_dirs_file_B:
- grouped_report_json_B:

### 6.4 Notes

- notes:

### 6.5 Completion record (2026-01-09)

- quant_commit: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`
- runner_flags: `world_conditioned_impedance=1, world_r_cap=0.01, world_a_http=0.02, world_a_rl=0.10, world_a_rej=0.05, world_a_lat_ms=200.0, probe_attempts_per_tick=1, steps=10000, seeds=71001/71002/71003, modes=full/no_e/no_m/null`
- dataset_A_path: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`
- dataset_B_path: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- artifacts_dir: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/`
- run_dirs_file_A: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/run_dirs_A.txt`
- grouped_report_json_A: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/grouped_A.json`
- run_dirs_file_B: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/run_dirs_B.txt`
- grouped_report_json_B: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/grouped_B.json`
- verifier_reports_jsonl: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/verify_local_reachability_reports.jsonl`
- programmer_completion_report: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/PROGRAMMER_COMPLETION_REPORT.md`
- sample_coupling_stats: `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/world_u_latency_sample_stats.json`
