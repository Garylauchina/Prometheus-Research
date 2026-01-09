# V12 — Survival Space Poset §3 (Round-2 dims) No-Informational-Gain Failure Test (v0, 2026-01-09)

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

## 0. Purpose (Decision Gate)

We are **not** asking whether a poset can be defined.
We are asking whether, under **two independent dimension projections**, the poset approach has **ever** provided **new information** beyond the **M-only baseline**.

This document executes **§3 No-Informational-Gain** on the **Round-2 dimension set**:

- dims: **(suppression_ratio, downshift_rate)**

Decision rule (hard):

- If **§3 triggers (FAIL)**: **Poset is engineering-rejected for Survival Space v1.x** and **no further §1/§2 tests are permitted**.
- If **§3 does NOT trigger (PASS)**: only then may we evaluate **§1 comparability stability** (to detect temporal illusion vs structural persistence).

## 1. Frozen inputs

We operate on the already archived extended-validation metrics file:

- `per_run_metrics_jsonl`: (to be filled at completion anchor)

We do **not** run new experiments here. This is a **post-hoc verifier/classifier test** only.

## 2. Labels and baseline (frozen)

- **Label** \(y\_full\): `order_attempts_count(full) > 0`
  - Interpreted as “some action was actually attempted in full mode”.
- **Baseline predictor** \(M-only\): `order_attempts_count(no_e) > 0`
  - Interpreted as “actions exist even when E is removed”; M-only gate proxy.

Train/test split (frozen):

- train: `seed % 2 == 0`
- test:  `seed % 2 == 1`

## 3. Poset-side predictor family (Round-2, frozen)

Dims are taken from **full** runs:

- `x1 = suppression_ratio(full)`
- `x2 = downshift_rate(full)`

Direction convention (frozen):

- higher = harder

Model family (frozen, no weights, no scoring):

- **axis_or monotone boundary**:
  - predict \(\hat{y}=0\) if \((x1 \ge t1) \lor (x2 \ge t2)\), else \(\hat{y}=1\)
  - \(t1,t2\) are fit on **train** by brute-force search over observed candidate thresholds

Rationale (audit):

- Round-2 `downshift_rate` is continuous; the Round-1 “per-level thresholds” model is not appropriate.
- This keeps the classifier **monotone** and **threshold-only**, avoiding “forced linearization” via weights/scores.

## 4. §3 falsification criterion (frozen)

Compute test accuracies:

- \(Acc_{baseline}\) on test
- \(Acc_{poset}\) on test

Decision (frozen):

- **PASS** only if \(Acc_{poset,test} > Acc_{baseline,test}\) (strictly better)
- otherwise **FAIL** (No informational gain; §3 triggers)

## 5. Outputs (frozen)

We must produce:

- `poset_round2_section3_report.json`
- `poset_round2_section3_report.md`

and archive them under:

- `docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/`

## 6. Completion anchors (append-only)

### 6.1 Run anchors

- per_run_metrics_jsonl:
- command:
- report_json:
- report_md:

### 6.2 Result anchors

- verdict:
- accuracy_baseline_test:
- accuracy_poset_test:

### 6.3 Completion record (appended, 2026-01-09)

- per_run_metrics_jsonl: `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/per_run_metrics.jsonl`
- command:
  - `python3 tools/v12/poset_info_gain_test_v0.py --per_run_metrics_jsonl docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/per_run_metrics.jsonl --x1_field suppression_ratio --x2_field downshift_rate --model axis_or --output_json docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/poset_round2_section3_report.json --output_md docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/poset_round2_section3_report.md`
- report_json: `docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/poset_round2_section3_report.json`
- report_md: `docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/poset_round2_section3_report.md`
- verdict: **FAIL** (No informational gain; §3 triggers)
- accuracy_baseline_test: 1.0
- accuracy_poset_test: 1.0

