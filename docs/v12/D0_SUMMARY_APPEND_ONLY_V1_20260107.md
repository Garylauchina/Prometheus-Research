# D0 Summary (append-only) v1 — 2026-01-07

Scope: this document is a **freeze-frame summary** for future review. It contains:
- frozen assumptions,
- machine-verifiable facts (with artifact pointers),
- explicit “do-not-misread” constraints,
- a boundary statement (what this summary does not claim).

No explanatory narrative. Additive-only: append new versions rather than editing this one.

---

## §1 Frozen assumptions (contract-level)

- **Market type**: `USDT-SWAP`
- **Bar**: `1m` (`tick_interval_ms=60000`)
- **Signal**: `abs_log_return_k500`
  - `signal_t = abs(log(px_t / px_{t-500}))`
  - `k_window = 500` (frozen)
- **Visibility knobs**:
  - `signal_window_ticks` controls whether the k-lookback point is visible
  - `r_horizon_ticks` is a back-end cap (applied after run-length is computed)
- **Primary gap metric**: `gap = extinction_tick_A - extinction_tick_B`
- **Primary ratio metric**:
  - `reduction_ratio_full = (gap_on - gap_shuffle) / max(1, abs(gap_on))`
- **Protocol**:
  - pre-registration required
  - strict JSON / strict JSONL required
  - fail-closed (missing evidence => stop)

Authoritative SSOT for stop-rule semantics:
- `docs/v12/V12_SSOT_D0_FALSIFICATION_DEATH_VERDICT_V0_20260107.md`

---

## §2 Hard facts (by evidence path; no interpretation)

### §2.1 Time-structure sensitivity (local structure knife)

- **Trial-4 (block permutation knife; ETH)**:
  - Anchors in SSOT ledger: `§6.4.1`
  - Audit summary: `docs/v12/artifacts/d0/d0_trial_4/trial_4_block_knife_recomputed_summary.json`

### §2.2 Back-end memory cap does not eliminate ON vs SHUFFLE

- **Trial-5 (r_horizon cap; ETH)**:
  - Anchors in SSOT ledger: `§6.5.1`
  - Audit summary: `docs/v12/artifacts/d0/d0_trial_5/trial_5_visibility_knife_recomputed_summary.json`
  - Fact: `reduction_ratio_full` remains ~1 across tested `r_horizon_ticks` values (see per-H stats in the audit summary).

### §2.3 Front-end signal visibility is a gating condition (W < k)

- **Trial-6 (signal visibility window; ETH)**:
  - Anchors in SSOT ledger: `§6.6.1`
  - Audit summary: `docs/v12/artifacts/d0/d0_trial_6/trial_6_signal_visibility_window_knife_recomputed_summary.json`
  - Facts (aggregate):
    - For `signal_window_ticks ∈ {15,30,60,120}`:
      - `clip_ratio_on.mean = 1.0`
      - `reduction_ratio_full.mean = 0.0`
    - For `signal_window_ticks = None`:
      - `clip_ratio_on.mean = 0.0`
      - `reduction_ratio_full.mean = 0.9789436040`

### §2.4 W ≥ k staircase: no degradation beyond k for this signal definition

- **Trial-7 (W ≥ k staircase; ETH)**:
  - Anchors in SSOT ledger: `§6.7.1`
  - Audit summary: `docs/v12/artifacts/d0/d0_trial_7/trial_7_w_ge_k_staircase_recomputed_summary.json`
  - Facts (aggregate):
    - For `signal_window_ticks ∈ {500,625,750,1000,1500}`:
      - `clip_ratio_on.mean = 0.0` (all W)
      - `reduction_ratio_full.mean = 0.9993094388` (identical across W)

### §2.5 Time reversal negative control: ON and SHUFFLE become statistically similar

- **Trial-8 (time reversal; ETH; runner-internal transform)**:
  - Anchors in SSOT ledger: `§6.8.1`
  - Pre-reg includes execution Amendment A1: `docs/v12/pre_reg/D0_TRIAL_8_TIME_REVERSAL_NEG_CONTROL_V0_20260107.md`
  - Audit summary: `docs/v12/artifacts/d0/d0_trial_8/trial_8_time_reversal_neg_control_recomputed_summary.json`
  - Facts (aggregate):
    - `world_transform.kinds = ["time_reversal_replay_v0"]`
    - `world_transform.base_dataset_hash_unique = 1`
    - `world_transform.missing_count = 0`
    - `gap_on.mean = -69.65`, `gap_shuffle.mean = -66.3`

### §2.6 Cross-market pseudo-independence (ETH vs BTC): non-identical measurability regime

- **Trial-9 (cross-market; same knobs; ETH vs BTC)**:
  - Anchors in SSOT ledger: `§6.9.1`
  - Audit summary: `docs/v12/artifacts/d0/d0_trial_9/trial_9_cross_market_recomputed_summary.json`
  - Facts (aggregate):
    - ETH:
      - `reduction_ratio_full.mean = 0.9442991455`
      - `gap_on.mean = 1293.75`
    - BTC:
      - `gap_on.mean = 308.1833333333` (smaller magnitude than ETH under this setup)
      - `denom_eq_1_count = 2` out of 60 pairs (RR has a known structural amplification when `denom=1`)
      - Extreme RR examples exist where `gap_on` is ±1 (see `rr_abs_top5` in the audit summary).

---

## §3 Do-not-misread constraints (explicit)

- **Do not claim**: “D0 formal kill switch (F2) was triggered.”  
  - This summary is not a stop-rule verdict; the formal rule lives in the SSOT.
- **Do not claim (Trial-9)**: “BTC has stronger effect because RR mean/std is larger.”  
  - RR can enter a structural amplification regime when `denom = max(1, |gap_on|) = 1`.
- **Do not claim (Trial-7)**: “W > k improves effect.”  
  - For `abs_log_return_k500`, audit shows identical aggregates across `W ∈ {500..1500}`.
- **Do not claim (Trial-6)**: “W < k is a subtle degradation.”  
  - Under the frozen fail-closed semantics, it produces `clip_ratio=1.0` and `reduction_ratio_full=0.0`.

---

## §4 Boundary statement (methodology)

- This summary **does not** claim that other falsification methods are logically impossible.
- It records that under the strong constraint set in §1 (no change to signal definition, verdict function, market type, or metrics), additional experiments are expected to have rapidly diminishing marginal information and higher risk of introducing new degrees of freedom.

---

## §5 Review pointers (auditability)

- Full append-only trial ledger and artifact anchors:
  - `docs/v12/V12_SSOT_D0_FALSIFICATION_DEATH_VERDICT_V0_20260107.md` (§6)
- Trial-4..9 audit summaries:
  - `docs/v12/artifacts/d0/d0_trial_4/trial_4_block_knife_recomputed_summary.json`
  - `docs/v12/artifacts/d0/d0_trial_5/trial_5_visibility_knife_recomputed_summary.json`
  - `docs/v12/artifacts/d0/d0_trial_6/trial_6_signal_visibility_window_knife_recomputed_summary.json`
  - `docs/v12/artifacts/d0/d0_trial_7/trial_7_w_ge_k_staircase_recomputed_summary.json`
  - `docs/v12/artifacts/d0/d0_trial_8/trial_8_time_reversal_neg_control_recomputed_summary.json`
  - `docs/v12/artifacts/d0/d0_trial_9/trial_9_cross_market_recomputed_summary.json`


