# V12 — Survival Space — Poset Round-2 Incomparability Saturation Test v0 — 2026-01-09

Additive-only. Document type: **Pre-registration (Research Falsification Trial)**.

Scope: Survival Space（post-hoc only; not decision, not optimization, not profitability).

Cross-links:
- Checklist: `docs/v12/V12_SURVIVAL_SPACE_POSET_LATTICE_FALSIFICATION_CHECKLIST_V0_DRAFT_20260109.md` (§2, §7)
- Round‑1 pre-reg + result: `docs/v12/pre_reg/V12_SURVIVAL_SPACE_POSET_ROUND1_INCOMPARABILITY_SATURATION_V0_20260109.md`
- §3 info-gain result (Round‑1 dims failed): `docs/v12/pre_reg/V12_SURVIVAL_SPACE_POSET_SECTION3_INFO_GAIN_FAILURE_TEST_V0_20260109.md`
- Finalized evidence bundle: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/README.md`

---

## §0 Frozen motivation (new hypothesis)

We test a new hypothesis:

> The previous poset failure was due to **low information content** in `block_rate` (too discrete), not because poset is intrinsically unusable.

Therefore we hold the checklist / kill-switch unchanged, but change the Round‑2 dimension set.

---

## §1 Frozen prerequisites (fail-closed)

- Poset is strictly post-hoc; no runtime feedback.
- No reward / PnL / profit proxy enters any judgment.
- No weighting / scoring / representative element selection (Forced Linearization is a kill switch).

If broken ⇒ verdict `NOT_APPLICABLE`.

---

## §2 Universe (frozen)

Same as Round‑1:
- source: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/per_run_metrics.jsonl`
- run list: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/final_440_run_ids.txt`
- included modes: `full` and `no_e`

---

## §3 Frozen dimension set (Round‑2)

Round‑2 poset dimensions (frozen):

- \(x_1 = \texttt{suppression_ratio}\)
- \(x_2 = \texttt{downshift_rate}\)

Direction (frozen):
- higher = harder / more constrained

No other dimensions permitted in Round‑2.

---

## §4 Order definition (frozen)

Componentwise dominance:

\[
a \preceq b \iff x_1(a)\le x_1(b) \land x_2(a)\le x_2(b)
\]

Comparable iff \(a \preceq b\) or \(b \preceq a\).
Incomparable iff neither dominates the other.

---

## §5 Trial target (frozen)

Primary target: checklist §2 **Incomparability Saturation**.

Frozen threshold:
- incomparability_rate ≥ 0.80

Stability requirement (frozen):
- As sample size increases, incomparability_rate must not significantly decrease.

Frozen sampling plan:
- pair samples per curve point: 50,000 (random pairs with replacement)
- curve sample sizes: 200, 400, 800, 1600, 3200
- RNG seed: 20260109 (frozen)

---

## §6 Outputs (frozen)

Tool (frozen):
- `tools/v12/poset_incomparability_test_v0.py`

Invocation (frozen):

```bash
python3 tools/v12/poset_incomparability_test_v0.py \
  --per_run_metrics_jsonl <artifact_per_run_metrics_jsonl> \
  --modes full,no_e \
  --x1_field suppression_ratio \
  --x2_field downshift_rate \
  --seed 20260109 \
  --pair_samples 50000 \
  --curve_sizes 200,400,800,1600,3200 \
  --threshold 0.80 \
  --output_json <.../poset_round2_report.json> \
  --output_md <.../poset_round2_report.md>
```

Outputs (must be archived):
- `poset_round2_report.json`
- `poset_round2_report.md`

---

## §7 Stop rule (frozen)

If incomparability saturation triggers (≥0.80 stable), Round‑2 declares:
- verdict `FAIL` (poset operationally uninformative under this dimension set).

If it does not trigger, verdict `PASS` for this knife only (poset survives §2 under Round‑2 dims).

No transition to lattice unless separately justified under checklist §5.

