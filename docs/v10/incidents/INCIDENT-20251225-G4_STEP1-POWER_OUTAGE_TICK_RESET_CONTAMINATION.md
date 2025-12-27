# INCIDENT-20251225: Gate4 Step1 interrupted (power outage) + tick reset contamination

## Summary

- **Run dir (external evidence location)**: `/Users/liugang/Cursor_Store/Prometheus-Quant/volumes/runs/run_20251224_032650_gate4mac_step1_okx_demo_15m_96ticks_final/`
- **Event**: Mac power outage caused container interruption; Docker auto-restarted and continued writing evidence into the same `run_id`.
- **Impact**: tick indices restarted from 1 under the same `run_id`, creating **tick collisions** across multiple restart segments.
- **Verdict**: this evidence directory is **Invalid / Not Measurable** for “single 96-tick judgment window” claims. It is still useful as **debug evidence** for decision-chain liveness and live market input sanity.

## Evidence highlights (read-only)

- `decision_trace.jsonl` shows multiple segments (tick reset):
  - Segment A: tick 1..55, `2025-12-24T03:27Z` → `2025-12-24T16:57Z`
  - Segment B: tick 1..2, `2025-12-25T00:56Z` → `2025-12-25T01:11Z`
  - Segment C: tick 1..4, `2025-12-25T01:25Z` → `2025-12-25T02:10Z`
- `capital_reconciliation_events.jsonl` has matching tick collisions (e.g., tick 1 appears multiple times with different timestamps).

## Live market input sanity check (partial but strong)

At `2025-12-25T01:25:42Z`:

- `decision_trace.jsonl` tick summary has `mark_price=87664.4`
- `okx_rest_raw_samples.json` ticker sample has `last=87664.4` for `BTC-USDT-SWAP`
- The nearest-timestamp delta is sub-second; price diff is 0.0.

This supports the claim that `mark_price` is sourced from OKX REST ticker (at least at this checkpoint).

## Required fix (next iteration, contract-level)

The execution wrapper must enforce one of:

- **A) New run_id on restart** (preferred for Gate4 Step1), or
- **B) Monotonic `restart_index` + monotonic tick timeline** with explicit segment boundaries and frozen evidence contract.

Any run that continues under the same `run_id` with tick reset must be labeled **Invalid / Not Measurable** for Gate4 Step1 window claims.


