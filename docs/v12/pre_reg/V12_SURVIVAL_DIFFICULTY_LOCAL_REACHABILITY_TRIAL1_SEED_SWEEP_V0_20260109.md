# V12 Pre-reg — Local Reachability — Trial-1 Seed Sweep (v0, 2026-01-09)

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-1 (Volatility proxy; E-only): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL1_VOLATILITY_PROXY_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

Trial-1 has been completed on one run_dir. This sweep checks **stability / non-triviality** across multiple seeds under the same dataset.

We still do:
- measurement only
- no rollout
- no planning/search
- no “better/worse agent”

---

## 1. Frozen inputs

We run Trial-1 tool (Quant):
- `tools/v12/posthoc_local_reachability_v1_volatility_proxy.py`

On a fixed list of existing run_dirs (same dataset family):

- (to be filled at completion anchor; must be absolute paths)

---

## 2. Frozen evaluation (descriptive)

For each run_dir, we compute:
- feasible_ratio stats (min/p50/p90/p99/max/mean)

We aggregate:
- distribution of per-run `feasible_ratio.mean`

No threshold-based acceptance is used here; this is a stability readout.

---

## 3. Falsification conditions (frozen)

We reject Trial-1 as a useful measurement lens if any of:

- **Triviality across seeds**: per-run `feasible_ratio.mean` is identical (or near-identical) across all run_dirs (indicating no usable variability).
- **Input drift**: run_dirs are found to be from different datasets/epochs without explicit declaration.

Stop rule:
- if triggered ⇒ stop (no patching within this claim).

---

## 4. Completion anchors (append-only)

### 4.1 Run anchors

- run_dirs_file:
- command_batch:
- aggregate_report_json:

### 4.2 Observed summary (descriptive)

- per_run_mean_feasible_ratio_stats:
- notes:

