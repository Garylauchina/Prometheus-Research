# V12 Pre-reg — Local Reachability — Trial-2 Negative Control (probe_attempts_per_tick=0) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-2 pre-reg (probe on): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- Trial-2 seed sweep v1 grouped: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V1_GROUPED_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

This is a **negative control** to validate the fail-closed boundary:

> Without probe attempts, M becomes NOT_MEASURABLE (no attempts ⇒ no impedance), therefore Trial-2 (M-only reachability) must not silently “work”.

We test the “old world” setting:

- `probe_attempts_per_tick = 0`

Hard boundaries (frozen):
- no rollout / planning / search
- no reward / PnL
- probe is OFF (by design)
- no patching within this claim

---

## 1. Frozen expectation (must be satisfied)

Given probe is OFF:

- Many ticks will have `interaction_impedance.verdict == NOT_MEASURABLE` (no attempts).

Therefore the Trial-2 posthoc builder (impedance proxy) MUST:

- **FAIL** (non-zero exit), refusing to generate `local_reachability.jsonl`, because impedance is not PASS / attempts<1.

If the tool instead produces an output “successfully”, this negative control **fails** (drift: it is no longer an M-only measurable contract).

---

## 2. Frozen inputs

A Quant run_dir produced by `run_survival_space_em_v1.py` with:

- same dataset_dir as Trial-2 runs
- `--ablation_mode full` (frozen)
- `--probe_attempts_per_tick 0` (frozen)

---

## 3. Frozen outputs (what must be returned)

We must archive:

- the absolute `quant_run_dir`
- the runner command
- the posthoc command and its captured stderr/stdout
- sampled lines from `interaction_impedance.jsonl` showing `NOT_MEASURABLE` exists

No `local_reachability.jsonl` should be produced. If it exists, treat as suspicious and capture it for audit.

---

## 4. Completion anchors (append-only)

### 4.1 Run anchors

- quant_run_dir:
- runner_command:
- posthoc_command:
- posthoc_exit_code:
- posthoc_output_path:

### 4.2 Evidence sanity

- interaction_impedance_not_measurable_observed: true|false
- local_reachability_exists: true|false
- notes:


## 5. Completion record (appended, 2026-01-09)

### 5.1 Run anchors

- quant_run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T071127Z_seed61001_full`
- runner_command:
  - `python3 tools/v12/run_survival_space_em_v1.py --dataset_dir /Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m --runs_root /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool --steps 10000 --seed 61001 --ablation_mode full --probe_attempts_per_tick 0`
- posthoc_command:
  - `python3 tools/v12/posthoc_local_reachability_v2_impedance_proxy.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T071127Z_seed61001_full`
- posthoc_exit_code: non-zero (FAIL as expected)
- posthoc_output_path:
  - stdout: `/tmp/trial2_probe_off_posthoc_stdout.txt` (empty)
  - stderr: `/tmp/trial2_probe_off_posthoc_stderr.txt` (ValueError attempts<1)
  - recheck stderr: `/tmp/trial2_probe_off_posthoc_stderr_recheck2.txt`

### 5.2 Evidence sanity

- interaction_impedance_not_measurable_observed: false
- local_reachability_exists: false
- notes:
  - Runner semantics: even with attempts=0 at t=0, `interaction_impedance.verdict` is `PASS` due to bootstrap assumption; hence NOT_MEASURABLE verdict did not appear.
  - However, `interaction_impedance.metrics.order_attempts_count=0` at `ts_utc=2022-10-01T00:00:00Z` is observed, and the Trial-2 posthoc tool fails closed on `attempts<1`, satisfying the negative-control intent.
