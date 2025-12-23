# INCIDENT-20251223: Preflight + Bootstrap + Agent allocation PASSED — okx_demo_api

## What happened（现象，1–3句）

We fixed the execution-world startup chain so that **Startup Preflight succeeds** and bootstrap is fully auditable:

- equity parsing is unified (preflight reuses reconciliation logic)
- manifest contains complete bootstrap + agent allocation fields
- bootstrap allocates `80%` to agents with fixed `1000 USDT/agent` and floors agent count

Result: the single-run verification is **SUCCESS** and unblocks the 24h local screening launch.

---

## Context（run_id / mode / commit）

- **Mode**: `okx_demo_api` (OKX demo / simulated trading)
- **Verification run**: `run_20251223_083150_32021f4`
- **Prometheus-Quant commits (operator report)**:
  - `fb32019`: unified equity parser (preflight reuses reconciliation logic)  ✅ key
  - `32021f4`: save manifest in `run_okx_demo` after preflight success
  - `98bed2f`: update manifest with preflight results from `run_okx_demo`
  - `d358f35`: save manifest immediately after `run_okx_demo` returns
  - `e92e72e`: define start_time for abort manifest
  - `ce347b3`: correct preflight abort exception handling

---

## Evidence（关键证据：按合同口径）

### Preflight

- `preflight_status = success`
- `bootstrap_capital_field = totalEq`
- `bootstrap_capital_value = 115411.43 USDT`

### Bootstrap allocation (locked rule)

- `allocation_ratio = 0.8`
- `capital_per_agent = 1000`
- `num_agents = 92` (floor)
- `allocated_capital_actual = 92000`
- `system_reserve_initial = 23411.43` (20% base + rounding dust)

---

## Interpretation（解读）

- PASS means the execution-world startup chain is now auditable and consistent with:
  - Startup Preflight contract
  - Bootstrap contract (80/20 + 1000/agent + floor)
  - “exchange equity is source of truth” accounting premise

This removes the previous blocker where demo preflight failed due to inconsistent balance parsing.


