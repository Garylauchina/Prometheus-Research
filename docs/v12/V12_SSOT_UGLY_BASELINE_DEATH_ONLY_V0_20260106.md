# V12 SSOT — Ugly Baseline (death-only, replay_truth) v0 — 2026-01-06

Goal: freeze a **brutal, minimal baseline** to calibrate expectations and expose fake structures.

This baseline is deliberately “ugly”:
- no reproduction
- no profit/equity-based survival
- no hidden shaping

Additive-only.

---

## 0) Dependencies (frozen)

- Replay dataset v0 (exchange snapshot → offline replay): `docs/v12/V12_SSOT_REPLAY_DATASET_V0_20260106.md`
- Life red-line (death is NOT reward): `docs/v12/V12_SSOT_LIFE_ENERGY_AND_DEATH_V0_20260106.md`

---

## 1) Baseline contract (frozen)

### 1.1 World contract

- `truth_profile`: `replay_truth`
- `tick_interval_ms`: `1000`
- `steps_target`: `5000`
- `inst_id`: must match the replay dataset (`BTC-USDT-SWAP` recommended)

### 1.2 Population

- `agent_count`: recommended range `50..200` (v0)

### 1.3 Life (death-only)

- `energy_init_E0`: constant for all agents (v0 recommended `E0=100`)
- `delta_per_tick`: constant `-1` for all agents
- `death_verdict`: `energy_after_tick <= 0` => dead
- Reproduction: disabled

Allowed baseline outcome:
- mass simultaneous death (all agents dead on the same tick)

Hard red-line:
- death/survival MUST NOT depend on profit/ROI/equity/fitness ranking (see Life SSOT).

---

## 2) Evidence (run_dir) requirements (frozen)

### 2.1 Required files (missing any => FAIL)

- `run_manifest.json`
- `errors.jsonl` (strict JSONL; may be empty)
- `life_tick_summary.jsonl` (strict JSONL; non-empty)
- `life_run_summary.json` (JSON object; single file)

### 2.2 `life_tick_summary.jsonl` minimal schema (v0)

One JSON object per tick (strict JSONL), minimally:

- `tick_id` (int, starting at 1)
- `ts_utc` (string ISO8601 with `Z`, optional but recommended for audit)
- `alive_count` (int)
- `dead_count_cum` (int)
- `extinct` (bool)

Notes:
- After extinction, `alive_count` must remain 0 and `extinct` must remain true.

### 2.3 `life_run_summary.json` minimal schema (v0)

Required keys:

- `agent_count` (int)
- `energy_init_E0` (int)
- `delta_per_tick` (int, must be `-1` in v0)
- `steps_target` (int, must be `5000` in v0)
- `steps_actual` (int)
- `extinction_tick` (int|null)
- `verdict` (`PASS|NOT_MEASURABLE|FAIL`)
- `reason_codes` (array[string])

Hard rule:
- `life_run_summary.json` must explicitly record the life contract parameters (`E0`, `delta_per_tick`, `steps_target`), to prevent silent drift.

---

## 3) Acceptance semantics (frozen)

PASS requires:
- required files exist
- strict JSONL for `errors.jsonl` + `life_tick_summary.jsonl`
- `life_tick_summary.jsonl` has `steps_actual >= steps_target`
- `tick_id` monotonic increasing by 1
- `alive_count` is non-increasing over ticks
- If `extinction_tick` is non-null, it matches the first tick where `alive_count == 0`
- No violation of the Life red-line is detected

Acceptance anchor (read-only, factual record):
- Quant tick run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_tick_loop_v0_20260106T083725Z`
- Dataset dir (local artifact): `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_BTC-USDT-SWAP_20260106T083725.364788Z_20260106T105939.297603Z_1000ms`
- Dataset verifier verdict: `NOT_MEASURABLE` (tick interval unstable: violations=2225/4999, ratio=0.445; delta_ms_min=941, delta_ms_max=13211)
- Baseline run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_ugly_baseline_v0_20260106T115105Z`
- Baseline verifier verdict: `PASS`
- Extinction tick (observed): `100` (agent_count=100, E0=100, delta=-1)

Experimental extension (non-acceptance; read-only factual record):
- v0_dirty_random_cost (random action_cost; still no reward→energy)
  - Quant summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_dirty_random_cost_50seeds_CLEAN_summary_20260106T121350Z.json`
  - Acceptance report: `/tmp/V12_UGLY_BASELINE_V0_DIRTY_ACCEPTANCE_20260106.md`
  - Result (50 seeds, survival_cost_uniform_max=2.0): extinction_tick mean=55.56, std=1.00, range=[54,59]
  - Quant commits: `5f9134e` (feat v0_dirty), `f555f67` (fix run_id collision)

- v0.1 decision-cost (decision record exists; deterministic negative control)
  - Quant summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_1_decision_cost_50seeds_summary_20260106T123740Z.json`
  - Result (50 seeds): extinction_tick mean=67, std=0.0, range=[67,67]; invalid_ratio_mean=0.0
  - Note: This demonstrates that “reading world input” does not imply world affects survival unless mapped into action_cost/impedance_cost.

- v0.1 reject-stress (action_cost invalid penalty; 20000 steps + dataset wrap)
  - Quant artifacts (reported):
    - runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (101 run_dirs: 100-seed sweep + 1 smoke)
    - raw summary: `runs_v12/v0_1_reject_stress_100seeds_raw_summary.json`
    - raw bundle: `docs/v12/V12_V0_1_REJECT_STRESS_100SEED_RAW_OUTPUT_20260106.txt`
  - Result (reported, 100 values list):
    - extinction_tick mean=27.40, std=2.92, range=[22,35]
    - reject_rate mean=30.20%, std=1.31%
  - Friend gate semantics (factual): reject_rate >= 20% ⇒ chain intact (PASS); extinction std > 10~20 not met (std=2.92)
  - Note (scale reality): with `E0=100` and invalid penalty `10..30`, early extinction is expected; long-run “tails” require time-scale alignment (raise E0 or reduce penalty) while keeping the life red-line (no reward→energy).

- v0.3 reject-stress (dynamic threshold + harsher penalties; 30000 steps + dataset wrap)
  - Quant artifacts (reported):
    - Quant commit: `8172caa` (branch: `v12-broker-uplink-v0`)
    - runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (154 run_dirs reported)
    - raw summary: `runs_v12/v0_3_reject_stress_150seeds_raw_summary_20260106T152605Z.json`
    - raw bundle: `/tmp/V0_3_REJECT_STRESS_FINAL_RAW_OUTPUT_20260106.txt`
  - Result (reported, 150 values list):
    - extinction_tick mean=13.95, std=1.42, range=[12,18]
    - reject_rate mean=78.58%, std=6.53%
  - Friend gate semantics (factual): reject_rate mean >= 30% ⇒ PASS (reject-stress achieved)
  - Note (scale reality): extinction at ~14 ticks implies the long-run (30000 steps) is still dominated by “post-extinction ticks”; observing “tails” requires time-scale alignment (raise E0 and/or reduce penalties) while keeping the life red-line.

- v0.4 tail_reject_stress (tail-friendly scale; 50000 steps; 200 seeds)
  - Quant artifacts (reported):
    - Quant commits: `678e4a0`, `047629c`, `d81ba6d` (branch: `v12-broker-uplink-v0`)
    - runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (200 run_dirs: `seed[1..200]`)
    - raw summary: `runs_v12/v0_4_tail_reject_stress_200seeds_raw_summary_20260106T154931Z.json`
    - summarizer: `tools/v12/summarize_v0_4_tail_reject_stress_200seeds_raw.py` (includes admit rule)
  - Result (reported):
    - extinction_tick mean=183, std=15.04, range=134
    - reject_rate mean=50.06% (slightly above suggested 50% upper bound)
  - Admit rule (reported): NOT triggered (std>=10 or range>=50 satisfied)
  - Note (friend “hope” target): if requiring `std>50` and `range>200`, this run set does not meet it yet; it is still a meaningful tail-widening compared to v0.3.

- v0.5 dirty_tail (early stop; 100000 steps target; 300 seeds)
  - Quant artifacts (reported):
    - Quant commits: `d1f9a87`, `1195fa9` (branch: `v12-broker-uplink-v0`)
    - runs_root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (305 run_dirs reported; seeds `1..300`)
    - raw summary: `runs_v12/v0_5_dirty_tail_300seeds_raw_summary_*.json`
    - summarizer: `tools/v12/summarize_v0_5_dirty_tail_300seeds_raw.py` (4 gate checks)
  - Result (reported; early stop enabled):
    - extinction_tick mean=168, std=11.99, range=67 (142..209)
    - reject_rate mean=59.97%, std=0.45%
    - alive@5000: 0% (all extinct before tick 5000)
  - Gate checks (reported): 0/4 passed (FAIL)
  - Note (factual): early stop reduced effective ticks to ~300×168 ≈ 50,400 (≈99.5% saved vs 300×100,000).

- v0.2 impedance-cost (world measurability affects energy via impedance_cost)
  - Quant summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_2_impedance_cost_50seeds_summary_20260106T124935Z.json`
  - Result (50 seeds): extinction_tick mean=53.04, std=0.445, range=[52,54]; impedance_triggered_ratio mean=0.0586, std=0.0
  - Note: impedance_triggered_ratio constant across seeds (dataset-driven quality sequence); extinction variation comes from conditional cost sampling.

- v0.2_extreme (gauss init stress; death-only)
  - Quant summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_2_extreme_summary_20260106T133241Z.json`
  - Result (factual): run_dirs=101 (unique_seeds=100; `rng_seed=1` duplicated); extinction_tick mean=88.7921, std=5.7381, range=[77,100]; impedance_triggered_ratio mean=0.0, std=0.0
  - Note (fail-closed semantics): impedance_triggered_ratio=0.0 means this run set did not exercise the “NOT_MEASURABLE snapshot → impedance_cost” branch; it is valid evidence for **energy-init distribution effects**, not for **impedance-cost effects**.

NOT_MEASURABLE:
- evidence is valid but a higher-level measurement (not part of v0) is disabled/not measurable
- (v0 death-only should usually be PASS if evidence is correct)

FAIL:
- missing required evidence
- non-strict JSONL
- schema violations
- inconsistent extinction semantics

---

## 3.1) W0 — World structure measurability gate (frozen; for world-coupling experiments)

This SSOT is “death-only”; however, many experimental extensions attempted to add “world-coupling”.
To prevent **manufacturing** pseudo-signal in no-structure worlds, we freeze a gate:

- If a run’s intent is “world-coupling” (world → cost/pressure), it MUST run W0 on `market_snapshot.jsonl` first.
- If W0 verdict is `NOT_MEASURABLE`, the run MUST stop (or self-label `NOT_MEASURABLE`) and MUST NOT proceed to large seed sweeps.

Tool:
- `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000`

---

## 4) Tools (frozen entry)

- Verifier:
  - `python3 tools/v12/verify_ugly_baseline_death_only_v0.py --run_dir <RUN_DIR> --steps_target 5000`


