# D0 Trial-5 Pre-registration — Visibility horizon knife (run-length horizon cap) v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_5_visibility_horizon_r_cap_knife_v0`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) World input (frozen for this trial)

We reuse an existing replay dataset (no regeneration).

- dataset_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- inst_id: `ETH-USDT-SWAP`
- dataset_tick_interval_ms_effective: `60000` (bar=1m)

W0 requirement:
- Must use the existing PASS report:
  - `docs/v12/artifacts/d0/d0_trial_3/w0_report.json`

---

## 2) World signal (frozen)

- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- window(s)/params: `k=500`
- normalization anchor: dataset-specific, computed per run from full dataset (as current runner does)

---

## 3) Pressure mapping (frozen; NO reward)

Same as V0.6.3:
- `g_t = clamp(signal_t / signal_p99_anchor, 0, 1)`
- `r_t = r_{t-1} + 1 if g_t >= g_hi else 0`
- `cluster_penalty = uniform(0, 8) * max(0, r_t - 2)`

This knife adds ONE deterministic constraint (see §5):
- run-length horizon cap: `r_t_effective = min(r_t, r_horizon_ticks)`

Hard red-line:
- no positive energy updates; death is energy-only.

---

## 4) Projection definition (frozen)

- projection_kind: `binary A/B` (fixed 50/50; no learning)
- what is being adjudicated: `time-structure adjudication robustness under limited local observability (horizon cap)`

---

## 5) Controls / modes + knife parameter (frozen)

We run 2 modes × multiple horizons, same dataset, same seeds, same g_hi sweep:

Modes:
- ON: mode=`on`
- SHUFFLE: mode=`shuffle` with `shuffle_seed = 1000003 + seed` (full-length permutation, deterministic)

Knife parameter:
- r_horizon_ticks ∈ {None, 60, 30, 15, 5}
  - None means unbounded (baseline; identical to Trial-3 semantics)
  - With bar=1m, ticks == minutes

Definition (frozen):
- r_t_effective = r_t if r_horizon_ticks is None else min(r_t, r_horizon_ticks)
- cluster_penalty uses r_t_effective (not raw r_t)

Fail-closed:
- r_horizon_ticks must be >= 3 if provided; else exit non-zero (because penalty starts at r_t-2 and horizons below 3 are degenerate).

---

## 6) Primary metric + falsification criteria (frozen)

Gap metric:
- `gap = extinction_tick_A - extinction_tick_B`

For each horizon H:
- `reduction_ratio_full(H) = (gap_on(H) - gap_shuffle(H)) / max(1, abs(gap_on(H)))`

No new PASS/FAIL beyond existing D0 rule; this knife is a diagnostic attempt:
- If `reduction_ratio_full(None) >= 0.5` but `reduction_ratio_full(<=30) < 0.5`, record `evidence:local_visibility_required`.
- If `reduction_ratio_full(<=15)` remains >= 0.5, record `warning:effect_survives_low_visibility` (danger signal; suggests distribution redundancy).

All reporting must be strict JSON.

---

## 7) Run plan (frozen)

- seeds: `6001–6020` (20 seeds; disjoint from Trial-1/2/3/4)
- g_hi sweep: `0.55, 0.60, 0.65`
- horizons: `None, 60, 30, 15, 5`
- steps_target: `50000`
- allow_dataset_wrap: `YES`
- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_5_visibility_knife/`

Expected run count:
- 20 seeds × 3 g_hi × 2 modes × 5 horizons = 600 runs

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_5_visibility_knife/` (600 run_dirs)
- operator_summary_json_path: `docs/v12/artifacts/d0/d0_trial_5/D0_TRIAL_5_VISIBILITY_HORIZON_KNIFE_SUMMARY_from_operator.json`
  - operator_summary_sha256: `fed8bd2702d444e8c1508d2db2bd4653cee04069eb6bb6e48017ad42794e946d`
- recomputed_summary_json_path: `docs/v12/artifacts/d0/d0_trial_5/trial_5_visibility_knife_recomputed_summary.json`
  - recomputed_summary_sha256: `a44f647dd44169836fb8b863d5aabdc177562a4ba871d673287bb2cd1dde3d44`
- notes: (append-only)


