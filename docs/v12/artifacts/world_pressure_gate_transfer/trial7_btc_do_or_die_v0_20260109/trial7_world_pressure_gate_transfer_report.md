# Trial-7 — World Pressure via Gate Transfer Function (Suppression) — BTC Do-or-Die Calibration — Result Summary (2026-01-09)

Quant commit (locked):
- `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

Tool:
- `tools/v12/calibrate_world_pressure_gate_transfer_v0.py`

## What we tested (frozen)

- World proxy: `u_t = interaction_impedance.metrics.world_u`
- Readout:
  - if `interaction_intensity==0` skip tick
  - else `suppression(t) = 1 - post_gate_intensity / interaction_intensity`
- Do-or-die thresholds: require `rho(u, suppression) >= 0.15` and `delta(top10%-bottom10%) >= 0.02`, plus epoch robustness.

## Evidence-chain status

- Strict implicit join enforced with line-by-line `ts_utc` equality between `decision_trace.jsonl` and `interaction_impedance.jsonl`.
- All 3 runs processed (no missing files / no join mismatches).

## Core results (representative run: seed 71001)

- `rho(u, suppression) ≈ 0.0157` (positive but far below 0.15)
- `delta(top10%-bottom10%) ≈ 0.02083` (barely above 0.02)

Interpretation (within Trial-7 scope):
- The compression readout shows **weak continuous association** with the world proxy.
- Quantile delta can be positive, but that is insufficient for a continuous pressure gauge under frozen thresholds.

## Verdict (do-or-die)

**FAIL** (3/3 runs; primary gate `rho_min` not met).

Stop rule applies:
- Tool exits; no patching inside Trial-7.

