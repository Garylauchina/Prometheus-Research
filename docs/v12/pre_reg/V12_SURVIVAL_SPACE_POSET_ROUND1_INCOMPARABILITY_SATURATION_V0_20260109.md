# V12 — Survival Space — Poset Round-1 Incomparability Saturation Test v0 — 2026-01-09

Additive-only. Document type: **Pre-registration (Research Falsification Trial)**.

Scope: Survival Space（post-hoc only; not decision, not optimization, not profitability).

Cross-links:
- Checklist: `docs/v12/V12_SURVIVAL_SPACE_POSET_LATTICE_FALSIFICATION_CHECKLIST_V0_DRAFT_20260109.md`
- Extended validation milestone: `docs/v12/V12_SURVIVAL_SPACE_EM_V1_0_1_FIX_M_EXTENDED_VALIDATION_MILESTONE_20260109.md`
- Finalized evidence bundle: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/README.md`

---

## §0 Frozen prerequisites (fail-closed)

This trial is valid only if all hold:

- Survival Space gate is **continuous modulation** (suppression/downshift-dominated), not binary-only.
- No reward / PnL / profit proxy enters any judgment.
- Screening ≠ decision; poset is **post-hoc only**.

If any prerequisite is broken ⇒ verdict must be `NOT_APPLICABLE`.

---

## §1 Object of comparison (frozen)

Element = one run (one behavior trace summarized post-hoc) under the same world contract and epoch scale.

Run universe (frozen for v0):
- source: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/per_run_metrics.jsonl`
- run list: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/final_440_run_ids.txt`
- included modes: `full` and `no_e`
- excluded modes (controls): `no_m`, `null` (kept for sanity only; not part of Round‑1 poset inference)

Rationale (frozen):
- Round‑1 poset should be tested on the mechanisms where E+M interplay exists (`full/no_e`), not on controls.

---

## §2 Frozen dimension set (Round‑1)

Round‑1 poset dimensions (frozen):

- \(x_1 = \texttt{suppression_ratio}\)
- \(x_2 = \texttt{block_rate}\)

Direction (frozen):
- higher = harder / more constrained

No other dimensions permitted in Round‑1.

---

## §3 Order definition (frozen)

Componentwise dominance:

\[
a \preceq b \iff x_1(a)\le x_1(b) \land x_2(a)\le x_2(b)
\]

Comparable iff \(a \preceq b\) or \(b \preceq a\).

Incomparable iff neither dominates the other.

---

## §4 Trial target (frozen)

Primary target: trigger checklist §2 **Incomparability Saturation**.

Frozen threshold:
- incomparability_rate ≥ 0.80

Stability requirement (frozen):
- As sample size increases, incomparability_rate must **not** significantly decrease.
  - operationalization: evaluate multiple pair-sample sizes; the curve must remain ≥0.80 beyond \(N_\text{min}\).

Frozen minimums:
- \(N_\text{min}\) runs included per mode: 100
- pair samples per point: 50,000 (random pairs with replacement)

---

## §5 Negative controls / sanity checks (frozen)

- Confirm controls behave as expected (not used for poset conclusion):
  - `null`: suppression_ratio≈0, block_rate≈0 (should cluster)
  - `no_m`: suppression_ratio≈baseline cap, block_rate≈0 (should cluster)

If controls are wildly inconsistent, flag `NOT_MEASURABLE` for pipeline issues (not poset).

---

## §6 Outputs (frozen)

Tool (frozen):
- `tools/v12/poset_incomparability_test_v0.py`

Outputs (must be produced and archived):
- `poset_round1_report.json`
- `poset_round1_report.md`

Both must include:
- data source pointers (paths)
- frozen dimension definition + direction
- incomparability_rate curve over multiple sample sizes
- verdict: `PASS` (poset survives this knife) or `FAIL` (poset killed by saturation) or `NOT_APPLICABLE/NOT_MEASURABLE`

---

## §7 Stop rule (frozen)

If incomparability saturation triggers (≥0.80 stable), Round‑1 declares:
- `FAIL` for poset usefulness (operationally uninformative), and **do not** expand dimensions.

If it does not trigger, only then may Round‑2 add a 3rd dimension (candidate: `downshift_rate`).

---

## Completion anchor (append-only; 2026-01-09)

Artifact outputs:
- `docs/v12/artifacts/survival_space_em/poset_round1_incomparability_v0_20260109/poset_round1_report.json`
- `docs/v12/artifacts/survival_space_em/poset_round1_incomparability_v0_20260109/poset_round1_report.md`

Observed outcome (frozen readout from report):
- verdict: `PASS` (incomparability saturation NOT triggered)
- incomparability_rate: 0.0 across tested curve points (200→3200 sample sizes)

Important constraint (audit note; frozen):
- In the current dataset, `block_rate` takes only **two distinct values**, causing a chain-like dominance structure under \((suppression_ratio, block_rate)\).
  - This is not a proof that poset is “useful”; it only means §2 saturation did not trigger under Round‑1 dims.

