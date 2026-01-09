# V12 Pre-reg — Local Reachability — Trial-2 Seed Sweep v1 (grouped by ablation_mode; M-probe) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-2 pre-reg: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- Trial-2 seed sweep v0: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

We extend Trial-2 seed sweep to a grouped design:

- For each seed, run 4 modes: `full`, `no_e`, `no_m`, `null`
- Probe contract is frozen: `probe_attempts_per_tick=1`

Goal:
- measure whether the M-only reachability compression has **non-trivial variability across seeds**
- measure whether the distribution differs **across ablation modes** (descriptive only)

We still do:
- measurement only
- no rollout / planning / search
- no reward / PnL
- death label disabled

---

## 1. Frozen inputs

For each seed:
- Quant runner: `tools/v12/run_survival_space_em_v1.py`
- `--probe_attempts_per_tick 1` (frozen)
- steps: 10000 (recommended; may be frozen by operator)

Required artifacts per run_dir:
- `run_manifest.json`
- `interaction_impedance.jsonl` (PASS per tick)
- `decision_trace.jsonl`
- `local_reachability.jsonl` (Trial-2 impedance proxy reason codes)

---

## 2. Frozen evaluation (descriptive only)

Per run_dir:
- feasible_ratio stats (min/p50/p90/p99/max/mean)

Grouped aggregation:
- for each `ablation_mode`, aggregate the distribution of per-run `feasible_ratio.mean`

No threshold-based “success” is asserted here.

---

## 3. Falsification conditions (frozen)

Reject Trial-2 as a useful lens across seeds if any triggers:

- **Triviality within group**: within any mode group, per-run `feasible_ratio.mean` is identical (or near-identical) across seeds.
- **Probe drift (hard failure)**: evidence indicates probe attempts affect survival/reward/gate semantics.
- **Input drift**: mismatch of dataset_dir / probe config across run_dirs without explicit declaration.

Stop rule:
- if triggered ⇒ stop (no patching within this claim).

---

## 4. Completion anchors (append-only)

### 4.1 Run anchors

- run_dirs_file:
- grouped_aggregate_report_json:

### 4.2 Observed summary (descriptive)

- grouped_per_run_mean_feasible_ratio:
- notes:

