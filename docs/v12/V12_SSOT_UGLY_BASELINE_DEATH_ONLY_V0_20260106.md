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

NOT_MEASURABLE:
- evidence is valid but a higher-level measurement (not part of v0) is disabled/not measurable
- (v0 death-only should usually be PASS if evidence is correct)

FAIL:
- missing required evidence
- non-strict JSONL
- schema violations
- inconsistent extinction semantics

---

## 4) Tools (frozen entry)

- Verifier:
  - `python3 tools/v12/verify_ugly_baseline_death_only_v0.py --run_dir <RUN_DIR> --steps_target 5000`


