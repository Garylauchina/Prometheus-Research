# Trial-6 — World Pressure via EDoF-CR — BTC Do-or-Die Calibration — Result Summary (2026-01-09)

Quant commit (locked):
- `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

Tool:
- `tools/v12/calibrate_world_pressure_edof_cr_v0.py`

## What we tested (frozen)

- World pressure proxy: `u_t = interaction_impedance.metrics.world_u`
- Action vector (per tick): `a_t = [interaction_intensity, post_gate_intensity, action_allowed]`
- Rolling window: W=200
- Readout: `EDoF-CR(t) = -(EDoF(t) - EDoF(t-1))`
- Do-or-die acceptance: require positive sign + minimum `rho` threshold and epoch robustness across 3 seeds.

## Evidence-chain status

- Strict implicit join enforced with line-by-line `ts_utc` equality between `decision_trace.jsonl` and `interaction_impedance.jsonl`.
- All 3 runs processed (no missing files / no join mismatches).

## Core results (representative run: seed 71001)

- `spearman_rho(u, EDoF-CR) ≈ -0.0118` (negative; fails sign + threshold)
- Quantile delta (top10% u minus bottom10% u) for EDoF-CR:
  - `delta ≈ -1.28e-4` (negative; fails sign)
- Segment medians (1000/5000/10000) are also negative / near zero.

## Verdict (do-or-die)

**FAIL** (3/3 runs).

Engineering meaning (within Trial-6 scope):
- Under the frozen action embedding and W=200, EDoF-CR does not behave as a continuous world-pressure gauge in the BTC single-world calibration.
- Per stop rule: tool exits; no patching inside Trial-6.

