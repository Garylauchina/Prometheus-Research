# Trial-5 — BTC World-Pressure Calibration (single-dataset, do-or-die) — Result Summary (2026-01-09)

Quant commit (locked):
- `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

Dataset (single):
- BTC 2021–2022 replay

Runs (full mode only):
- seed 71001: `run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full`
- seed 71002: `run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full`
- seed 71003: `run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full`

Pre-reg thresholds (do-or-die):
- full-series: `rho >= 0.15` and `delta >= 0.02`
- epoch robustness: p50 over windows {1000,5000,10000} satisfies `rho_p50>=0.10` and `delta_p50>=0.015`
- sign must be positive and not flip across runs

## Evidence-chain status

- Tool runs without crashes; strict ordering join is enforced.
- All three runs produce per-run JSON reports.

## Core results

Aggregate (3 runs):
- `rho` mean ≈ 0.111 (min ≈ 0.094, max ≈ 0.121)
- `delta` mean ≈ 0.063 (min ≈ 0.059, max ≈ 0.066)

Interpretation (within Trial-5 scope):
- Quantile separation is strong and consistently positive (`delta` passes).
- But the **continuous association** (`rho`) is below the frozen minimum (`0.15`) on all 3 runs.

## Verdict (do-or-die)

**FAIL** (triggered by `rho_min` threshold under frozen contract).

Per Trial-5 stop rule:
- The **current Local Reachability lens** (Trial-2 impedance-proxy) is engineering-rejected for “measuring world pressure” under this single-world calibration contract.
- No patching inside Trial-5.

