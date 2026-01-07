# D0 Trial-7 Pre-registration — W ≥ k visibility degradation staircase v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_7_signal_window_ge_k_staircase_v0`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) World input (frozen for this trial)

- dataset_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- inst_id: `ETH-USDT-SWAP`
- dataset_tick_interval_ms_effective: `60000` (bar=1m)

W0 requirement:
- Must reuse existing PASS report:
  - `docs/v12/artifacts/d0/d0_trial_3/w0_report.json`

---

## 2) World signal (frozen; identical base signal)

- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- k_window: `500` (frozen)
- normalization_anchor: `dataset_precomputed` (same semantics as current runner)

---

## 3) Pressure mapping (frozen; NO reward)

Same as D0 baseline:
- `g_t = clamp(signal_t / signal_p99_anchor, 0, 1)`
- `r_t = r_{t-1} + 1 if g_t >= g_hi else 0`
- `cluster_penalty = uniform(0, 8) * max(0, r_t - 2)`
- strict ban: positive energy update = `YES`

---

## 4) Knife definition (frozen): visibility degradation staircase in the **legal** range W ≥ k

Knife parameter:
- signal_window_ticks ∈ {500, 625, 750, 1000, 1500}
  - With bar=1m, ticks == minutes
  - All values satisfy W ≥ k_window (legal, computable)

Critical definition (front-end blindness; frozen):
- For each tick t, raw history visibility is limited to `[t - signal_window_ticks, t]`.
- When computing `signal_t = abs(log(px_t / px_{t-500}))`:
  - If `(t - 500) < (t - signal_window_ticks)` (should not happen here by construction), treat as NOT VISIBLE and set `signal_t=0.0` (fail-closed).
  - Otherwise compute baseline formula.

Note:
- This trial intentionally avoids W < k (already covered by Trial-6).

---

## 5) Controls / modes (frozen)

Modes:
- ON: mode=`on`
- SHUFFLE: mode=`shuffle`, deterministic with `shuffle_seed = 1000003 + seed`
- BLOCK_SHUFFLE: mode=`block_shuffle`
  - block_size_ticks: `60` (frozen)
  - perm_seed: `shuffle_seed = 1000003 + seed` (frozen)

---

## 6) Metrics + falsification criterion (frozen)

Gap:
- `gap = extinction_tick_A - extinction_tick_B`

For each (W, mode-pair):
- `reduction_ratio_full(W) = (gap_on(W) - gap_shuffle(W)) / max(1, abs(gap_on(W)))`
- `reduction_ratio_block(W) = (gap_on(W) - gap_block_shuffle(W)) / max(1, abs(gap_on(W)))`

Falsification gate (use existing D0 threshold):
- If there exists W* in the staircase such that `reduction_ratio_full(W*) < 0.5`, record as a D0-relevant kill attempt outcome.

---

## 7) Run plan (frozen)

- seeds: `8001–8020` (20 seeds; disjoint from Trial-1..6)
- g_hi sweep: `0.55, 0.60, 0.65`
- signal_window_ticks_values: `500, 625, 750, 1000, 1500`
- block_size_ticks: `60`
- steps_target: `50000`
- allow_dataset_wrap: `YES`
- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_7_signal_window_ge_k_staircase/`

Expected run count:
- 20 seeds × 3 g_hi × 3 modes × 5 windows = 900 runs

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_7_signal_window_ge_k_staircase/` (900 run_dirs)
- operator_summary_json_path: `docs/v12/artifacts/d0/d0_trial_7/D0_TRIAL_7_W_GE_K_STAIRCASE_SUMMARY_from_operator.json`
  - operator_summary_sha256: `4016b3f7e541fbb43d3d3895a57ebac4f87f47b43ec1f1bec951996f95010168`
- recomputed_summary_json_path: `docs/v12/artifacts/d0/d0_trial_7/trial_7_w_ge_k_staircase_recomputed_summary.json`
  - recomputed_summary_sha256: `f750ba46783b3ac8e79b626659f525026ba8b538b003b053e6fa6dc86517a62b`
- notes: (append-only)


