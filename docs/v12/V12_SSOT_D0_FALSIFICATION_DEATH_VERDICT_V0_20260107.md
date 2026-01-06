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


