# D0 Trial-4 Pre-registration — Temporal causality break (block-wise permutation knife) v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_4_temporal_causality_break_block_permute_knife_v0`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) World input (frozen for this trial)

This knife is executed on an already-materialized replay dataset (no regeneration).

- dataset_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`
- dataset_id_effective: `SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31` (see Trial-3 pre-reg for dataset hashes)
- inst_id: `ETH-USDT-SWAP`
- dataset_tick_interval_ms_effective: `60000` (bar=1m; frozen)

### 1.1 W0 gate

This trial is permitted to run only if the dataset W0 verdict is `PASS`.

- w0_report_path: `docs/v12/artifacts/d0/d0_trial_3/w0_report.json` (must exist and be PASS)

---

## 2) World signal (frozen)

- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- window(s)/params: `k=500`

Normalization anchor (must be shared across all modes):
- signal_p99_anchor source: `dataset_precomputed`
- signal_p99_anchor value: `dataset_specific` (must use the per-run computed anchor from the dataset; no carry-over)

---

## 3) Pressure mapping (frozen; NO reward)

Same as V0.6.3:
- `g_t = clamp(signal_t / signal_p99_anchor, 0, 1)`
- `r_t = r_{t-1} + 1 if g_t >= g_hi else 0`
- `cluster_penalty = uniform(0, 8) * max(0, r_t - 2)`
- `cost_A = -(base_cost + linear_exposure)`
- `cost_B = -(base_cost + linear_exposure + cluster_penalty)`
- strict ban: positive energy update = `YES`

---

## 4) Projection definition (frozen)

- projection_kind: `binary A/B` (fixed 50/50; no learning)
- what is being adjudicated: `survival gap A_minus_B under time-aligned pressure vs time-structure breaks`

---

## 5) Controls / modes (frozen)

We run 3 modes on the SAME dataset, SAME seeds, SAME g_hi sweep:

- ON:
  - meaning: use g sequence as-is (time aligned)
- SHUFFLE (full):
  - meaning: deterministic full-length permutation of g sequence
  - shuffle_seed rule: `1000003 + seed`
  - algorithm: `random.Random(shuffle_seed).shuffle(g_sequence_full_len_N)`
- BLOCK_PERMUTE (knife):
  - meaning: break *global* temporal causality while preserving *within-block* order
  - block_size_ticks \(B\): `60` (60 minutes)
  - perm_seed rule: `1000003 + seed`
  - algorithm (frozen):
    - partition g_sequence into contiguous blocks of length B
    - keep order inside each block
    - permute block order with `random.Random(perm_seed)`
    - concatenate blocks (length preserved)

Notes:
- This knife is additive-only and does not change the core metric definition.
- This knife is expected to be **less destructive** than full SHUFFLE; it is used to test whether the effect depends on long-range causality vs merely local structure.

---

## 6) Primary metric + falsification criteria (frozen)

Gap metric:
- `gap = extinction_tick_A - extinction_tick_B`

We compute 2 reduction ratios (both must be reported):
- `reduction_ratio_full = (gap_on - gap_shuffle) / max(1, abs(gap_on))`
- `reduction_ratio_block = (gap_on - gap_block) / max(1, abs(gap_on))`

PASS/FAIL rule (frozen):
- Primary falsification target remains time-alignment break:
  - Require `reduction_ratio_full >= 0.5` on campaign aggregate (same as D0 baseline rule).
- Knife diagnostic:
  - If `reduction_ratio_block` is consistently close to `reduction_ratio_full`, record `warning:knife_block_break_not_more_informative_than_full_shuffle` (does not flip PASS/FAIL by itself).

---

## 7) Run plan (frozen)

- seeds: `5001–5020` (20 seeds; disjoint from Trial-1/2/3)
- g_hi sweep: `0.55, 0.60, 0.65`
- modes: `on`, `shuffle`, `block_shuffle` (block permutation)
- steps_target: `50000`
- allow_dataset_wrap: `YES`
- runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_4_block_knife/`

Expected run count:
- 20 seeds × 3 g_hi × 3 modes = 180 runs

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

- runs_root: (TBD)
- summary_json_path: (TBD)
- summary_sha256: (TBD)
- verifier_output_path: (TBD)
- notes: (append-only)


