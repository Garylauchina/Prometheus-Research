# V12 SSOT — D0 falsification “death verdict” (constitution-level) v0 — 2026-01-07

Purpose: convert “falsification-first” into an **executable, auditable stop rule**.

Additive-only.

---

## 0) Scope (frozen)

This SSOT governs the hypothesis:

> **H**: world time structure can **adjudicate** an agent’s projection (output) via auditable pressure mapping, producing measurable survival differences that depend on time alignment (ON vs SHUFFLE).

This SSOT does **not** declare H true. It defines when we must stop and admit failure (in the current framework / projection definition).

---

## 1) Preconditions (must hold)

### 1.1 W0 gate (world structure measurability)

All D0 trials MUST use world inputs with W0 verdict = `PASS`.

Tool:
- `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000`

If W0 is `NOT_MEASURABLE`, the trial is `NOT_MEASURABLE` and does not count toward the “3 independent trials”.

### 1.2 Protocol compliance

Each trial MUST be pre-registered and must follow:
- `docs/v12/V12_SSOT_WORLD_COUPLING_EXPERIMENT_PROTOCOL_V0_20260107.md`

Violations are `FAIL (contract_drift)` and count as a D0 failure (see F3).

---

## 2) The D0 rule (frozen)

**D0**:
- Run **3 independent trials** (see §2.1).
- If **any** of F1/F2/F3 is triggered in **all 3 trials**, we must:
  - label hypothesis H as **FAIL / not provable in the current framework**, and
  - stop further “world-coupling proof” campaigns, and
  - enter redesign/reconstruction of coupling + projection definition.

### 2.1 What counts as “independent trials” (frozen)

Trials must be independent at the world-input level:
- different dataset windows / segments, OR
- different datasets, OR
- different inst_id series,
but all must satisfy W0=PASS.

Seeds can overlap; independence is about world input, not RNG.

---

## 3) Failure conditions (frozen)

### F1) Time-structure adjudication fails (alignment effect not detected)

Under the pre-registered primary metric \(M\):
- `alignment_effect = M(ON) - M(SHUFFLE)`

If ON is **not distinguishable** from SHUFFLE under the pre-registered rule, trigger:
- `FAIL (coupling_not_detected:time_alignment)` for the trial.

### F2) Projection adjudication fails (binary projection test does not depend on time alignment)

For a binary projection test (A vs B), define a pre-registered gap metric \(G\):
- `gap_on = G(ON)`
- `gap_shuffle = G(SHUFFLE)`

If SHUFFLE does **not** materially reduce the gap under the pre-registered rule, trigger:
- `FAIL (projection_not_adjudicated_by_time_structure)`.

### F3) We cannot execute falsification correctly (controls/protocol repeatedly invalid)

If a trial ends as any of:
- `FAIL (contract_drift)`
- `FAIL (control_invalid:*)`
- repeated inability to produce strict evidence

then trigger:
- `FAIL (falsification_protocol_unreliable)`.

---

## 4) Mandatory stop action (frozen)

If D0 triggers:
- stop further “prove H” efforts under the current framework
- record the 3 trial anchors (dataset ids, commits, run dirs, reports) as an append-only factual record
- begin redesign of:
  - projection definition (“what must be adjudicated”)
  - pressure mapping (“how world becomes pressure”)
  - world signal selection (what constitutes structure)

---

## 5) Status fields (for manifests; recommended)

Recommended to record in each trial manifest:
- `d0.enabled=true`
- `d0.trial_id`
- `d0.w0_report_ref`
- `d0.protocol_version_ref`
- `d0.primary_metric_name`
- `d0.f1_f2_f3_status` (one of: `pass|fail:<reason>|not_measurable`)

---

## 6) Trial entry records (append-only factual log; recommended)

This section is a **factual ledger** of D0 trial entries. Add new records only.

### 6.1 Trial-1 — V0.6.3 temporal-only falsification battery (ON vs SHUFFLE)

- **trial_id**: `d0_trial_1_v0_6_3_temporal_only_falsification_battery`
- **entry_ts_utc**: `2026-01-06T19:22:44Z` (campaign generated_at; see PRIMARY JSON)
- **artifacts_dir**: `docs/v12/artifacts/d0/v0_6_3_trial_1/`
- **primary_json**: `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_3_BATTERY_AUDITABLE_COMPLETE_FINAL.json`
  - **sha256**: `eb3c4e2bbf1e15141be7389bad489b12e7ee1c60389f56af3bfc86a7ff00db56`
- **derived_json**: `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_3_DERIVED_SHUFFLE_SEED_COMPLETE_DATA.json`
- **verifier_script**: `docs/v12/artifacts/d0/v0_6_3_trial_1/verify_v0_6_3_reproducibility.py`
- **delivery_manifest**: `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_3_ABSOLUTE_FINAL_DELIVERY.md`

Verification command (stdlib only; run from repo root):
- `python3 docs/v12/artifacts/d0/v0_6_3_trial_1/verify_v0_6_3_reproducibility.py docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_3_BATTERY_AUDITABLE_COMPLETE_FINAL.json`

OFF evidence note (OFF is not included in V0.6.3 dataset; evidence is provided separately):
- **off_mode.status**: `NOT_INCLUDED_IN_THIS_DATASET`
- **off_mode.v0_6_1_reference.evidence_files**:
  - `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_1_WORLD_COUPLING_TEST_SUMMARY_2026-01-06T18:07:35.765714Z.json`
  - `docs/v12/artifacts/d0/v0_6_3_trial_1/V0_6_1_per_seed_on_off_shuffle_20seeds.json`

### 6.2 Trial-2 (planned; pre-registered)

- **trial_id**: `d0_trial_2_v0_6_3_temporal_only_falsification_battery`
- **status**: `COMPLETED`
- **pre_reg_doc**: `docs/v12/pre_reg/D0_TRIAL_2_V0_6_3_TEMPORAL_ONLY_FALSIFICATION_BATTERY_PRE_REG_V0_20260107.md`
- **independence_basis**: `same market type + same inst universe (SWAP/universe_A) + strictly non-overlapping time window vs Trial-1`

### 6.3 Trial-3 (planned; pre-registered)

- **trial_id**: `d0_trial_3_v0_6_3_temporal_only_falsification_battery`
- **status**: `COMPLETED`
- **pre_reg_doc**: `docs/v12/pre_reg/D0_TRIAL_3_V0_6_3_TEMPORAL_ONLY_FALSIFICATION_BATTERY_PRE_REG_V0_20260107.md`
- **independence_basis**: `same market type (SWAP) + different inst universe (universe_B, disjoint from Trial-1/2)`

### 6.2.1 Trial-2 completion anchors (append-only)

- **w0_report**: `docs/v12/artifacts/d0/d0_trial_2/w0_report.json`
- **sweep_summary**: `docs/v12/artifacts/d0/d0_trial_2/trial_2_sweep_summary.json`
  - **sha256**: `f95425801ab5d1c57f73309d22a5b4cb32c1a0099b9a3ba184a7f3cde4d420c9`
- **operator_summary** (archived): `docs/v12/artifacts/d0/D0_TRIAL_2_3_COMPLETE_SUMMARY_from_operator.json`

### 6.3.1 Trial-3 completion anchors (append-only)

- **w0_report**: `docs/v12/artifacts/d0/d0_trial_3/w0_report.json`
- **sweep_summary**: `docs/v12/artifacts/d0/d0_trial_3/trial_3_sweep_summary.json`
  - **sha256**: `c2981d891c97c1c73fe2e9ad682bd838e5e0468bdf2936b312900ee5f7e98e66`
- **operator_summary** (archived): `docs/v12/artifacts/d0/D0_TRIAL_2_3_COMPLETE_SUMMARY_from_operator.json`

### 6.4 Trial-4 (planned; pre-registered knife)

- **trial_id**: `d0_trial_4_temporal_causality_break_block_permute_knife_v0`
- **status**: `COMPLETED`
- **pre_reg_doc**: `docs/v12/pre_reg/D0_TRIAL_4_TEMPORAL_CAUSALITY_BREAK_BLOCK_PERMUTE_KNIFE_V0_20260107.md`
- **purpose**: `structural ablation knife (block-wise time permutation) to attempt to kill the time-structure claim with minimal extra freedom`

### 6.4.1 Trial-4 completion anchors (append-only)

- **runs_root**: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_4_block_knife/`
- **operator_summary** (archived): `docs/v12/artifacts/d0/d0_trial_4/D0_TRIAL_4_BLOCK_PERMUTE_KNIFE_SUMMARY_from_operator.json`
  - **sha256**: `2f47e03f0a937c23e1e23e54d6e5378584ff57a2c33b80f85036c9a2117a6e21`
- **recomputed_summary** (audit): `docs/v12/artifacts/d0/d0_trial_4/trial_4_block_knife_recomputed_summary.json`
  - **sha256**: `5515eb6982eadedb86b39dfb7043e222f05831cb4bf9ce040407812efa8b3471`

### 6.5 Trial-5 (planned; pre-registered knife)

- **trial_id**: `d0_trial_5_visibility_horizon_r_cap_knife_v0`
- **status**: `COMPLETED`
- **pre_reg_doc**: `docs/v12/pre_reg/D0_TRIAL_5_VISIBILITY_HORIZON_R_CAP_KNIFE_V0_20260107.md`
- **purpose**: `visibility horizon ablation (cap run-length memory) to attempt to kill the local-structure explanation without changing the world`

### 6.5.1 Trial-5 completion anchors (append-only)

- **runs_root**: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_d0_trial_5_visibility_knife/`
- **operator_summary** (archived): `docs/v12/artifacts/d0/d0_trial_5/D0_TRIAL_5_VISIBILITY_HORIZON_KNIFE_SUMMARY_from_operator.json`
  - **sha256**: `fed8bd2702d444e8c1508d2db2bd4653cee04069eb6bb6e48017ad42794e946d`
- **recomputed_summary** (audit): `docs/v12/artifacts/d0/d0_trial_5/trial_5_visibility_knife_recomputed_summary.json`
  - **sha256**: `a44f647dd44169836fb8b863d5aabdc177562a4ba871d673287bb2cd1dde3d44`

### 6.6 Trial-6 (planned; pre-registered knife)

- **trial_id**: `d0_trial_6_signal_visibility_window_knife_v0`
- **status**: `PRE_REGISTERED (NOT_RUN_YET)`
- **pre_reg_doc**: `docs/v12/pre_reg/D0_TRIAL_6_SIGNAL_VISIBILITY_WINDOW_KNIFE_V0_20260107.md`
- **purpose**: `front-end blindness: compute signal only from visible window; attempt to kill time-structure claim by removing access to long lookback point (k=500)`
