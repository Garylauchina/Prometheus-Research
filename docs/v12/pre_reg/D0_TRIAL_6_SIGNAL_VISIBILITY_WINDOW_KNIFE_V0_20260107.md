# D0 Trial-6 Pre-registration — Signal visibility window knife v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_6_signal_visibility_window_knife_v0`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) World input (frozen for this trial)

We reuse the same replay dataset (no regeneration, no post-processing).

- dataset_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- inst_id: `ETH-USDT-SWAP`
- dataset_tick_interval_ms_effective: `60000` (bar=1m)

W0 requirement:
- Must use the existing PASS report:
  - `docs/v12/artifacts/d0/d0_trial_3/w0_report.json`

---

## 2) World signal (frozen)

Base signal (same as V0.6.3 / Trial-3):
- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- k_window: `500` (frozen; NOT a knob in this trial)

Normalization anchor:
- source: `dataset_precomputed` (computed from the full dataset per run; as current runner does)
- MUST be shared across ON/SHUFFLE for the same (seed, g_hi, visibility_window)

---

## 3) Pressure mapping (frozen; NO reward)

Same as V0.6.3:
- `g_t = clamp(signal_t / signal_p99_anchor, 0, 1)`
- `r_t = r_{t-1} + 1 if g_t >= g_hi else 0`
- `cluster_penalty = uniform(0, 8) * max(0, r_t - 2)`
- strict ban: positive energy update = `YES`

---

## 4) Projection definition (frozen)

- projection_kind: `binary A/B` (fixed 50/50; no learning)
- what is being adjudicated: `robustness of ON vs SHUFFLE under front-end signal visibility constraints`

---

## 5) Controls / modes + knife parameter (frozen)

Modes (same as baseline):
- ON: mode=`on`
- SHUFFLE: mode=`shuffle` with `shuffle_seed = 1000003 + seed` (full-length permutation, deterministic)

Knife parameter (visibility window):
- signal_window_ticks ∈ {None, 120, 60, 30, 15}
  - None means unbounded (baseline semantics)
  - With bar=1m, ticks == minutes

Critical definition (this is the knife; frozen):
- For each tick t, raw history visibility is limited to `[t - signal_window_ticks, t]`.
- When computing `signal_t = abs(log(px_t / px_{t-500}))`:
  - If `signal_window_ticks` is None: use baseline (no restriction).
  - Else, if `(t - 500) < (t - signal_window_ticks)` i.e. `signal_window_ticks < 500`:
    - `signal_t` is treated as **NOT VISIBLE** and MUST be set to `0.0` (fail-closed; no NaN).
    - Increment `signal_visibility_clipped_count`.
  - Otherwise, compute baseline formula.

Notes:
- This is **front-end blindness**, not “back-end cap”.
- We do not change the world sequence; we change whether the agent/system can access the required historical point.

Fail-closed:
- signal_window_ticks must be positive if provided; else exit non-zero.

---

## 6) Primary metric + falsification criteria (frozen)

Gap metric:
- `gap = extinction_tick_A - extinction_tick_B`

For each visibility window W:
- `reduction_ratio_full(W) = (gap_on(W) - gap_shuffle(W)) / max(1, abs(gap_on(W)))`

Use existing D0 criterion (no new verdict language):
- If `reduction_ratio_full(W)` (campaign aggregate) drops below 0.5 for some bounded W while baseline W=None is >=0.5:
  - record `evidence:signal_visibility_required_at_window_W`

---

## 7) Run plan (frozen)

- seeds: `7001–7020` (20 seeds; disjoint from Trial-1..5)
- g_hi sweep: `0.55, 0.60, 0.65`
- visibility windows: `None, 120, 60, 30, 15`
- steps_target: `50000`
- allow_dataset_wrap: `YES`
- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_6_signal_visibility_knife/`

Expected run count:
- 20 seeds × 3 g_hi × 2 modes × 5 windows = 600 runs

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_6_signal_visibility_knife/` (600 run_dirs)
- operator_summary_json_path: `docs/v12/artifacts/d0/d0_trial_6/D0_TRIAL_6_SIGNAL_VISIBILITY_WINDOW_KNIFE_SUMMARY_from_operator.json`
  - operator_summary_sha256: `3ed0d09ce239157593661e680e501014a0eba4ab117d579faa3f7d7fff5af3e4`
- recomputed_summary_json_path: `docs/v12/artifacts/d0/d0_trial_6/trial_6_signal_visibility_window_knife_recomputed_summary.json`
  - recomputed_summary_sha256: `2bb7182365770f4f1299d723bd5b09c4e3ace3167350fc4ed0b05d115ad0cd20`
- notes: (append-only)


