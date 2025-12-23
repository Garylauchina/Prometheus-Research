# INCIDENT-20251223: Capital reconciliation PASSED (exchange equity is source of truth) — okx_demo_api

## What happened（现象，1–3句）

We implemented and verified the **capital reconciliation mechanism** in execution world:

- `capital_reconciliation_events.jsonl` is generated
- exchange equity is successfully read from OKX demo
- `system_reserve` is adjusted to keep `exchange_equity ≈ allocated_capital + system_reserve`

All acceptance checks for this reconciliation verification were reported as **PASSED**.

---

## Context（run_id / commits / mode）

- **Mode**: `okx_demo_api`
- **Verification run**: `run_20251223_060042_b494fec`
- **Commits (Prometheus-Quant, operator report)**:
  - `bd615a3`: reconciliation module core
  - `43591c4`: main loop integration
  - `87a2640`: allocation_ratio fix
  - `ed4f873`: OKX API parsing fix
  - `b494fec`: remove duplicate old code block

---

## Evidence（关键证据）

### Artifact presence / 产物存在

- `capital_reconciliation_events.jsonl`: **exists**
- number of reconciliation events: **3** (3 ticks)

Each event includes required fields:

- `exchange_equity`
- `allocated_capital`
- `system_reserve`
- `delta`
- `action_taken`

### Equity trace / 交易所权益序列（USDT）

From operator report:

- `112702.84 → 112679.87 → 112745.75`

### Allocation stability / 已分配资金稳定性

From operator report:

- `allocated_capital` remains stable: `8000 USDT`
- `system_reserve` dynamically adjusts to match exchange equity

---

## Fixes applied（关键修复点）

1) OKX API response format mismatch:
   - observed: balance API returned a list `[{...}]` instead of `{code,data}`
   - fix: access `balance_data[0]` directly

2) allocation_ratio parameter read bug:
   - fix: use `args.allocation_ratio` (not `args.reconciliation_tolerance`)

3) duplicated legacy code block used:
   - fix: remove duplicate old code block to avoid accidentally running outdated logic

---

## IEB（证据包）

- IEB archive: `IEB_run_20251223_034500_038be16_RECONCILE_STOP_20251223_115544.tar.gz`

---

## Interpretation（解读）

- PASS means we now have an auditable mechanism that treats **exchange equity as source of truth** and keeps the system wallet consistent.
- This closes a critical audit gap: without reconciliation, `system_reserve` can drift into a fictional number and invalidate ROI/collapse claims.

---

## Next step（下一步）

- Restart the local screening campaign with:
  - Startup preflight (clean slate)
  - Bootstrap (80/20 + 1000 USDT per agent + floor)
  - Reconciliation enabled at a fixed cadence (per tick or per review)
- During the first 24h, monitor:
  - reconciliation event counts & delta distribution
  - disk growth & shard/index integrity


