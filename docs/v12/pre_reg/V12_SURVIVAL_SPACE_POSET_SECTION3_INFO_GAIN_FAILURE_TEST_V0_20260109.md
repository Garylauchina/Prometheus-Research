# V12 — Survival Space — Poset §3 No-Informational-Gain Falsification Test v0 — 2026-01-09

Additive-only. Document type: **Pre-registration (Research Falsification Trial)**.

Scope: Survival Space（post-hoc only; not decision, not optimization, not profitability).

Cross-links:
- Checklist: `docs/v12/V12_SURVIVAL_SPACE_POSET_LATTICE_FALSIFICATION_CHECKLIST_V0_DRAFT_20260109.md` (§3)
- Round‑1 pre-reg: `docs/v12/pre_reg/V12_SURVIVAL_SPACE_POSET_ROUND1_INCOMPARABILITY_SATURATION_V0_20260109.md`
- Finalized evidence bundle: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/README.md`

---

## §0 Frozen prerequisites (fail-closed)

- Poset is strictly post-hoc; no runtime feedback.
- No reward / PnL / profit proxy enters any judgment.
- We do **not** introduce new dimensions beyond Round‑1.
- We do **not** introduce weights/scoring in the final classifier (monotone poset boundary only).

If any prerequisite is broken ⇒ verdict `NOT_APPLICABLE`.

---

## §1 Data universe (frozen)

Data source:
- `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/per_run_metrics.jsonl`

Universe selection (frozen):
- seeds: those where both modes exist: `full` and `no_e` (same seed)
- baseline mode: `no_e` (treated as M-only baseline for this test)

---

## §2 Frozen label (“can continue action”)

We freeze a minimal, auditable label for `full` run:

- `y_full = 1` iff `order_attempts_count > 0`
- `y_full = 0` iff `order_attempts_count == 0`

Rationale (frozen):
- This is a fail-closed, non-optimizing definition of “any action occurred at all”.
- It avoids introducing thresholds on “how much action is enough”.

---

## §3 Baseline (M-only) predictor (frozen)

Baseline predictor uses only the paired `no_e` run of the same seed:

- `ŷ_baseline = 1` iff `order_attempts_count(no_e) > 0`
- `ŷ_baseline = 0` iff `order_attempts_count(no_e) == 0`

This matches checklist §3.1: “only hard constraint (M) → allowed/not-allowed”.

---

## §4 Poset predictor family (frozen)

Allowed inputs (Round‑1 dims, frozen):
- `(suppression_ratio, block_rate)` from the `full` run only

Constraint (frozen):
- Predictor must be **monotone** under dominance:
  - higher suppression_ratio ⇒ never predicts “more actionability”
  - higher block_rate ⇒ never predicts “more actionability”

Operationalization (frozen v0):
- A threshold surface over discrete `block_rate` levels:
  - choose per-level suppression thresholds that are non-increasing as block_rate increases
  - no weights; no scoring; no regression

Tool:
- `tools/v12/poset_info_gain_test_v0.py`

---

## §5 Train/test split (frozen)

To avoid overfitting, thresholds are selected on a fixed split:

- Split by seed parity:
  - train: `seed % 2 == 0`
  - test: `seed % 2 == 1`

---

## §6 Decision rule (frozen)

We compare test-set accuracy (or equivalently error rate) of:
- baseline predictor vs poset predictor

Falsification target (checklist §3 No Informational Gain):

- If `accuracy_poset_test <= accuracy_baseline_test` ⇒ **FAIL** (poset provides no informational gain over M-only baseline)
- If `accuracy_poset_test > accuracy_baseline_test` ⇒ **PASS** for this knife only (poset not killed by §3)

No other “soft” interpretations allowed in v0.

---

## Completion anchor (append-only; reserved)

When executed, append:
- artifact output paths
- verdict + key metrics

---

## Completion anchor (append-only; 2026-01-09)

Artifact outputs:
- `docs/v12/artifacts/survival_space_em/poset_section3_info_gain_v0_20260109/poset_section3_report.json`
- `docs/v12/artifacts/survival_space_em/poset_section3_info_gain_v0_20260109/poset_section3_report.md`

Observed outcome (frozen readout from report):
- pairs_count=200 (train=100, test=100)
- baseline_test_accuracy=1.0
- poset_test_accuracy=1.0
- verdict=`FAIL` (no informational gain over M-only baseline)

Kill statement (frozen):
- Under the Round‑1 dimension set, poset did not improve the fail-closed “can continue action” judgment over the M-only baseline; therefore poset is considered failed under checklist §3 for this system state.

