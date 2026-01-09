# Trial-4 — World-Conditioned Impedance (E→M coupling) — Result Summary (2026-01-09)

Quant commit:
- `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

Artifacts directory:
- `docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/`

## Evidence-chain status (fail-closed)

- `verify_local_reachability_v0.py`: all 24 runs verified (see `verify_local_reachability_reports.jsonl`).

## Coupling audit (sample-only)

One representative run per dataset shows:
- `interaction_impedance.jsonl.metrics` contains `world_r`, `world_u`, `world_conditioned_impedance=true`.
- `corr(world_u, avg_ack_latency_ms)` is positive (see `world_u_latency_sample_stats.json`).

## Core readout (grouped; per-run mean feasible_ratio)

Dataset A (BTC 2021–2022): `grouped_A.json`
- full: mean=0.626785
- no_e: mean=0.603111
- no_m: mean=0.626685
- null: mean=0.592433

Dataset B (ETH 2024-Q4): `grouped_B.json`
- full: mean=0.626789
- no_e: mean=0.600278
- no_m: mean=0.626163
- null: mean=0.591226

## Interpretation (within Trial-4 scope)

- The E→M coupling is **auditable and active** (world_u present; latency responds).
- The reachability grouped means across datasets are **still extremely close**. This suggests the *current reachability lens* remains dominated by the probe/friction structure, i.e. Trial-4 does **not** materially break the cross-dataset invariance at the `feasible_ratio` level.

Per Trial-4 pre-reg, this supports triggering:
- “Still identical across datasets (near-identical)” ⇒ stop this claim (no further patching inside Trial-4).

