# V12 Pre-reg — Local Reachability — Trial-2 Seed Sweep (Impedance probe; M-measurable) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-2 pre-reg: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

Trial-2 has been completed on one run_dir. This seed sweep tests:

- non-triviality across seeds (i.e., not identical across all seeds)
- stability under the same dataset and frozen probe contract

We still do:
- measurement only
- no rollout / planning / search
- no reward / PnL
- death label disabled

---

## 1. Frozen inputs

We run the Quant runner with:
- `--probe_attempts_per_tick 1` (frozen)

and generate `local_reachability.jsonl` using Trial-2 impedance proxy (posthoc).

Seed sweep run_dirs must satisfy:
- same dataset_dir (frozen)
- same `probe_attempts_per_tick=1`
- same mapping coefficients (a2,b3,c2,d1) and latency_hi_ms=200 (frozen)

---

## 2. Frozen evaluation (descriptive)

For each run_dir:
- feasible_ratio stats (min/p50/p90/p99/max/mean)

Aggregate:
- distribution of per-run `feasible_ratio.mean`

No threshold-based “success” is asserted here; we only record structure.

---

## 3. Falsification conditions (frozen)

Reject Trial-2 as a useful lens across seeds if any triggers:

- **Triviality across seeds**: per-run `feasible_ratio.mean` is identical (or near-identical) across all run_dirs.
- **Probe drift**: evidence indicates probe attempts affect survival/reward/gate semantics (hard failure).
- **Input drift**: run_dirs have mismatched dataset_dir / probe config without explicit declaration.

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

