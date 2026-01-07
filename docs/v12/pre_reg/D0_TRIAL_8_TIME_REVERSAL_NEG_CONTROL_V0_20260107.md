# D0 Trial-8 Pre-registration — Time reversal negative control v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_8_time_reversal_neg_control_v0`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) World input (frozen)

Base dataset:
- dataset_dir_base: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- inst_id: `ETH-USDT-SWAP`
- dataset_tick_interval_ms_effective: `60000` (bar=1m)

W0 requirement:
- Must reuse existing PASS report:
  - `docs/v12/artifacts/d0/d0_trial_3/w0_report.json`

---

## 2) World transform (knife; frozen)

Transform kind:
- `time_reversal_replay_v0`

Definition (frozen; fail-closed):
- The replay order is reversed: index t uses world record at index (T-1-t).
- No resampling, no interpolation, no filtering.
- `ts_utc` may become non-monotonic relative to original direction; this is allowed because replay index order is the driver.
- If an implementation requires a materialized dataset, it MUST:
  - write a new dataset dir (separate from base) and record hashes before any run.
  - remain strict JSON/JSONL and 1:1 row reuse (only order changes).

Evidence requirement:
- Each run MUST record:
  - `world_transform.kind = "time_reversal_replay_v0"`
  - `world_transform.base_dataset_dir`
  - `world_transform.base_dataset_hash`
  - `world_transform.reversed_record_count`

---

## 3) World signal + pressure mapping (frozen)

Signal:
- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- k_window: `500` (frozen)
- anchor: `dataset_precomputed` (on the transformed replay index order; no additional knobs)

Pressure mapping:
- same as baseline D0 (no reward)

---

## 4) Controls / modes (frozen)

Modes:
- ON: mode=`on`
- SHUFFLE: mode=`shuffle`, deterministic with `shuffle_seed = 1000003 + seed`
- (optional) BLOCK_SHUFFLE: NOT INCLUDED unless explicitly added by append-only amendment before execution

---

## 5) Metrics + negative control logic (frozen)

Gap:
- `gap = extinction_tick_A - extinction_tick_B`

Primary:
- `reduction_ratio_full = (gap_on - gap_shuffle) / max(1, abs(gap_on))`

Interpretation constraint (frozen):
- This trial is a **negative control** for time arrow sensitivity.
- It does NOT change any energy rule or add rewards.
- It only asks whether the effect survives when the world time direction is inverted.

---

## 6) Run plan (frozen)

- seeds: `9001–9020` (20 seeds; disjoint from Trial-1..7)
- g_hi sweep: `0.55, 0.60, 0.65`
- steps_target: `50000`
- allow_dataset_wrap: `YES`
- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_8_time_reversal_neg_control/`

Expected run count:
- 20 seeds × 3 g_hi × 2 modes = 120 runs

---

## 7) Post-run evidence anchors (fill after completion; do not change above)

- runs_root: (TBD)
- summary_json_path: (TBD)
- summary_sha256: (TBD)
- notes: (append-only)


