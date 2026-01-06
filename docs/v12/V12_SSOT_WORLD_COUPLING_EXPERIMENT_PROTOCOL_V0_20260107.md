# V12 SSOT — World-coupling experiment protocol v0 — 2026-01-07

Goal: make “world → pressure → survival” experiments **auditable and falsifiable**.

Additive-only.

---

## 0) Definitions (frozen)

- **world-coupling experiment**: any experiment that claims “world time dynamics” influences survival via `action_cost` / `impedance_cost` rules.
- **pressure mapping**: a frozen rule mapping world signals into cost deltas.
- **negative control**: a run that preserves marginal distributions but breaks time alignment (e.g. shuffle world signal).
- **ablation**: coupling ON vs coupling OFF on the same world input.

---

## 1) Hard prerequisites (fail-closed)

### 1.1 W0 gate MUST pass (world structure measurability)

Before any world-coupling seed sweep, run W0 on the world input:

- `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000`

If W0 verdict is `NOT_MEASURABLE`:
- the experiment MUST be labeled `NOT_MEASURABLE`
- and MUST NOT proceed to large seed sweeps (avoid manufacturing pseudo-signal).

---

## 2) Pre-registration checklist (must be frozen before running)

The experiment MUST record the following *before* execution (in manifest or a dedicated config file):

- **world input**
  - dataset_id / dataset_dir
  - inst_id
  - tick_interval_ms (if defined)
- **world signal**
  - signal definition (exact formula)
  - window(s) / parameters
  - missing-data rules (`NOT_MEASURABLE` discipline)
- **pressure mapping**
  - exact mapping from world signal → `action_cost`/`impedance_cost`
  - parameter values, clamps (if any), and rationale
  - explicit ban: no positive energy injection
- **life contract**
  - E0 distribution
  - base delta_per_tick
  - any additional costs (and their reason_codes)
- **acceptance / falsification criteria**
  - metrics to report (see §3)
  - explicit PASS/FAIL/NOT_MEASURABLE rules

Rule: if any item is missing or changed post-run ⇒ `FAIL (contract_drift)`.

---

## 3) Required metrics (per-run + campaign aggregate)

Per-run (in `life_run_summary.json`, additive-only fields):
- `reject_rate_run` (or equivalent event rate)
- `tick_pressure_volatility` (e.g. std of per-tick reject_ratio or per-tick cost intensity)
- `alive_ratio_at_tick_N` for at least one N (e.g. 5000 or 10000)
- `world_signal_stats` (min/mean/p99/max on executed ticks)
- `W0_verdict` + W0 report reference

Campaign aggregate (summary JSON):
- `extinction_ticks.values` + mean/std/range
- per-run `reject_rate_run.values` + mean/std/range
- per-run `tick_pressure_volatility.values` + mean/std
- `alive_ratio_at_tick_N` distribution

All outputs must be strict JSON / strict JSONL.

---

## 4) Mandatory controls (falsification-focused)

### 4.1 Ablation: coupling OFF vs ON

Same dataset, same seeds:
- ON: pressure mapping enabled
- OFF: pressure mapping disabled (baseline costs only)

Pass condition for “world-coupling exists” requires ON and OFF to be measurably different under the pre-registered criteria.

### 4.2 Negative control: time-alignment break (shuffle)

Shuffle the world signal across ticks (preserve marginal distribution, break time coupling).

Hard requirements (frozen; prevents “fake coupling” by inconsistent normalization):
- **Shared normalization anchor**: any normalization such as `g = signal / signal_p99` MUST use the **same** `signal_p99_anchor` across ON/OFF/SHUFFLE:
  - either a precomputed dataset-level anchor (recommended), or
  - a pre-registered constant.
  - It MUST NOT be recomputed per-mode or per-run in a way that changes the mapping scale.
- **Shuffle definition**: SHUFFLE MUST permute the per-tick signal values with a deterministic permutation (seeded), preserving the marginal distribution and length; only the **time alignment** is broken.
- **OFF definition**: OFF MUST not read the world signal at all (baseline-only).

Expectation:
- If ON ≈ SHUFFLE, then “world time structure” is NOT driving outcomes ⇒ FAIL (coupling_not_detected).
- If OFF is not ≈ SHUFFLE, then the negative control is invalid ⇒ FAIL (control_invalid:off_not_equivalent_to_shuffle).

---

## 5) Verdict semantics (frozen)

- **PASS**: W0 PASS + controls behaved as expected + pre-registered criteria satisfied.
- **FAIL**: contract drift, evidence missing, or controls falsify the claimed coupling.
- **NOT_MEASURABLE**: W0 NOT_MEASURABLE (no-structure world) or world signal not measurable under frozen rules.


