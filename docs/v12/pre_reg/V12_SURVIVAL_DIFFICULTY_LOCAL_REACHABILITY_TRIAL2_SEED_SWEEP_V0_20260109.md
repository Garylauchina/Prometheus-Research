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


## 5. Completion record (appended, 2026-01-09)

### 5.1 Run anchors

- run_dirs_file: `/tmp/local_reachability_trial2_run_dirs.txt`
- command_batch:
  - `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_v0.py --run_dirs_file /tmp/local_reachability_trial2_run_dirs.txt --output_json /tmp/local_reachability_trial2_seed_sweep_report.json`
- aggregate_report_json: `/tmp/local_reachability_trial2_seed_sweep_report.json`

### 5.2 Observed summary (descriptive)

- per_run_mean_feasible_ratio_stats:
  - count: 3
  - min: 0.6777555555555556
  - p50: 0.6788444444444445
  - max: 0.6793666666666667
  - mean: 0.6786555555555557
- notes:
  - All run_dirs verified PASS under `verify_local_reachability_v0`.
  - Reason codes indicate Trial-2 impedance proxy outputs (`reachability_proxy:impedance_exp`).
  - This record is descriptive only; it does not assert acceptance beyond evidence integrity.
