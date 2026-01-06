# D0 Trial-3 Pre-registration — V0.6.3 temporal-only falsification battery v0 — 2026-01-07

Fill this template **before running**. Do not edit after execution (append-only is allowed).

---

## 0) Trial identity

- trial_id: `d0_trial_3_v0_6_3_temporal_only_falsification_battery`
- owner: (TBD)
- date_utc: (TBD)
- repo_commit_quant: (TBD)
- repo_commit_research: (TBD)

---

## 1) World input (frozen for this trial)

- market_type: `SWAP` (same market type as Trial-1/Trial-2)
- inst_id: `universe_B` (must be disjoint from Trial-1/Trial-2)
- dataset_dir: `data/market/SWAP/universe_B/2019-01-01__2020-12-31`
- dataset_id: (TBD; MUST be a stable id)
- tick_interval_ms: (TBD)
- segment/window description:
  - Different `inst_id` universe than Trial-1/Trial-2, same market type SWAP.
  - If dataset does not exist yet: first generate an equivalent dataset via tick loop, then freeze the resulting dataset_dir + dataset_id here.

### 1.1 W0 gate parameters + result (frozen params; result must be recorded)

Command (same params as Trial-1):
- `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir data/market/SWAP/universe_B/2019-01-01__2020-12-31 --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000 --output <W0_REPORT.json>`

Result:
- W0 verdict: (TBD; MUST be PASS, otherwise trial is NOT_MEASURABLE and does not count)
- W0 report path: (TBD)

---

## 2) World signal (frozen)

- signal_name: `abs_log_return_k500`
- formula: `signal_t = abs(log(px_t / px_{t-500}))`
- window(s)/params: `k=500`
- missing-data rules: (TBD; must follow SSOT protocol; fail-closed)

Normalization anchor (must be shared across ON/OFF/SHUFFLE):
- signal_p99_anchor source: `dataset_precomputed`
- signal_p99_anchor value: `0.002507` (frozen; carried from Trial-1 unless re-precomputed on this dataset is explicitly pre-registered)

---

## 3) Pressure mapping (frozen; NO reward)

- energy_update_type: `action_cost`
- mapping formula from signal → g → cost (frozen):
  - `g_t = clamp(signal_t / signal_p99_anchor, 0, 1)`
  - `r_t = r_{t-1} + 1 if g_t >= g_hi else 0`
  - `cluster_penalty = uniform(0, 8) * max(0, r_t - 2)`
  - `cost_A = -(base_cost + linear_exposure)` (no cluster penalty)
  - `cost_B = -(base_cost + linear_exposure + cluster_penalty)` (B-only)
- base_cost distribution: `uniform(1.0, 3.0)`
- linear_exposure distribution: `uniform(0.0, 2.0) * g_t`
- strict ban: positive energy update (confirm): `YES`

---

## 4) Projection definition (frozen)

- projection_kind: `binary A/B`
- strategy: (TBD; must be simple & auditable; no learning)
- what is being adjudicated: `survival difference between A and B under time-aligned pressure`

---

## 5) Controls

- ON: run (required)
- SHUFFLE: run (required)
  - shuffle algorithm: `random.Random(shuffle_seed).shuffle(g_sequence_full_len_5000)`
  - shuffle_seed: (TBD; must be recorded)
- OFF (ablation):
  - status: `NOT_RUN_IN_THIS_TRIAL`
  - evidence_ref: use V0.6.1 OFF evidence (see §8.2)

---

## 6) Primary metric + falsification criteria (frozen)

Primary metric name:
- `reduction_ratio`

Binary projection gap:
- `gap = extinction_tick_A - extinction_tick_B`
- `gap_on = gap(ON)`
- `gap_shuffle = gap(SHUFFLE)`
- `reduction_ratio = (gap_on - gap_shuffle) / max(1, abs(gap_on))`

Falsification rule (frozen):
- PASS criterion for this trial: `reduction_ratio >= 0.5`
- D0 mapping: triggers F2 if the gap is not materially reduced under SHUFFLE by the rule above.

---

## 7) Run plan (frozen)

- seeds: 20 seeds, **disjoint** from Trial-1 and Trial-2 (exact list TBD)
- steps_target: (TBD)
- early_stop: (TBD)
- expected run_dirs naming: (TBD)

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

### 8.1 Trial-3 run anchors (to fill)

- runs_root: (TBD)
- run_ids (ON): (TBD)
- run_ids (SHUFFLE): (TBD)
- summary_json_path: (TBD)
- verifier_output_path: (TBD)

### 8.2 External OFF evidence reference (frozen reference; already archived in Research)

- status: `EXTERNAL_EVIDENCE_REFERENCE`
- evidence_files (archived under Trial-1 artifacts dir):
  - `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_1_WORLD_COUPLING_TEST_SUMMARY_2026-01-06T18:07:35.765714Z.json`
  - `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_1_per_seed_on_off_shuffle_20seeds.json`


