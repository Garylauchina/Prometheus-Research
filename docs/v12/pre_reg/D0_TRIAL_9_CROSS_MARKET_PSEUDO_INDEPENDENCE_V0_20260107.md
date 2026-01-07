# D0 Trial-9 Pre-registration — Cross-market pseudo-independence knife v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_9_cross_market_pseudo_independence_v0`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) Purpose (frozen; minimal)

Test whether the D0 effect is **market-specific** or **cross-market stable** under identical knobs.

Hard rule:
- No retuning: g_hi list, penalties, k_window, steps, energy knobs are frozen.

---

## 2) World inputs (frozen)

Reference (already established):
- dataset_dir_ref_eth: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- inst_id_ref_eth: `ETH-USDT-SWAP`

Target (new world input, but same market type SWAP, same bar=1m):
- dataset_dir_target_btc: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m`
- inst_id_target_btc: `BTC-USDT-SWAP`

Tick interval:
- dataset_tick_interval_ms_effective: `60000` (bar=1m)

W0 requirement:
- Must reuse existing W0 PASS reports for each dataset (if BTC report missing, STOP and run W0 first; do not sweep).
  - ETH: `docs/v12/artifacts/d0/d0_trial_3/w0_report.json`
  - BTC: (TBD; if not present, must be generated and archived before any sweep)

---

## 3) Signal + visibility (frozen)

Signal:
- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- k_window: `500`

Visibility (front-end):
- signal_window_ticks: `500` (W = k; legal and sufficient per Trial-7)

---

## 4) Pressure mapping (frozen; NO reward)

Same as D0 baseline:
- `g_t = clamp(signal_t / signal_p99_anchor, 0, 1)`
- `r_t = r_{t-1} + 1 if g_t >= g_hi else 0`
- `cluster_penalty = uniform(0, 8) * max(0, r_t - 2)`

---

## 5) Controls / modes (frozen)

Modes:
- ON: mode=`on`
- SHUFFLE: mode=`shuffle`, deterministic with `shuffle_seed = 1000003 + seed`
- (optional) BLOCK_SHUFFLE: NOT INCLUDED unless explicitly added by append-only amendment before execution

---

## 6) Metrics + decision rule (frozen)

Per dataset D in {ETH, BTC}:
- `gap_D = extinction_tick_A - extinction_tick_B`
- `reduction_ratio_full_D = (gap_on_D - gap_shuffle_D) / max(1, abs(gap_on_D))`

Pseudo-independence decision rule (frozen; no narrative):
- If ETH shows `reduction_ratio_full_ETH >= 0.5` but BTC shows `reduction_ratio_full_BTC < 0.5`, record outcome as: `market_specific_candidate`.
- If both satisfy `>= 0.5`, record outcome as: `cross_market_supported_candidate`.
- If either dataset fails W0, record: `NOT_MEASURABLE`.

---

## 7) Run plan (frozen)

We run the same knob set on each dataset.

- seeds: `10001–10020` (20 seeds; disjoint from Trial-1..8)
- g_hi sweep: `0.55, 0.60, 0.65` (frozen)
- steps_target: `50000`
- allow_dataset_wrap: `YES`
- runs_root_eth: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_9_cross_market_eth/`
- runs_root_btc: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_9_cross_market_btc/`

Expected run counts:
- Per dataset: 20 seeds × 3 g_hi × 2 modes = 120 runs
- Total: 240 runs

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

- runs_root_eth: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_9_cross_market_eth/` (120 run_dirs)
- runs_root_btc: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_9_cross_market_btc/` (120 run_dirs)
- operator_summary_json_path: `docs/v12/artifacts/d0/d0_trial_9/D0_TRIAL_9_CROSS_MARKET_PSEUDO_INDEPENDENCE_SUMMARY_from_operator.json`
  - operator_summary_sha256: `6e2ff158dbd61a904d15fa23742d8b75d9b3601e30ccbea2f76254a974f2ef91`
- recomputed_summary_json_path: `docs/v12/artifacts/d0/d0_trial_9/trial_9_cross_market_recomputed_summary.json`
  - recomputed_summary_sha256: `e8f98ecabc845841d7d7abe38691e8354fffa192907ce7b3bdb2e1331e158ec9`
- notes: (append-only)


