# V10 Post-run Ledger Audit Contract / 事后账簿审计契约（“一分钱不差”）

Date: 2025-12-26  
Scope: okx_demo observation (truth_profile=degraded_truth) first; okx_live later  
Goal: Real-time deltas may be absorbed, but **post-run must be balanced and traceable** (or explicitly NOT_MEASURABLE).

---

## 0) Core principle

- **Realtime**: temporary equity/ledger deltas may exist; system may absorb via `system_reserve_adjusted`, but must record **delta + reason_code + evidence refs**.
- **Post-run**: final books must be **balanced and traceable**. Finance systems do not tolerate “one cent” errors.

---

## 1) What “balanced” means

At post-run conclusion, we require (in a single currency, e.g., USDT):

1) Accounting identity closure:

\[
\sum agent\_energy + system\_reserve \approx exchange\_equity
\]

2) Reconciliation deltas closure:
- The sum of all unexplained deltas must be **0 within tolerance** if `truth_profile=full_truth_pnl`.
- If `truth_profile=degraded_truth`, missing evidence forces a downgrade to **NOT_MEASURABLE** (no fabrication).

---

## 2) Required realtime evidence (append-only)

### 2.1 `capital_reconciliation_events.jsonl`

Every time reserve is adjusted, the event MUST include:
- `delta`, `tolerance`, `action_taken="system_reserve_adjusted"`
- `reason_code` (mandatory)
- `evidence_refs[]` (paths/hashes to bills/fills/order_status samples used, if any)

### 2.2 `ledger_ticks.jsonl`

Ledger snapshots per tick (Tier-1), including:
- `exchange_equity`, `exchange_equity_source`
- truth-quality markers for positions/fills

---

## 3) Post-run audit output (required)

### 3.1 `post_run_ledger_audit.json`

One file per run, written at shutdown.

Minimum fields:
- `ts_utc`, `run_id`, `mode`, `truth_profile`, `impedance_fidelity`
- `tolerance_usdt`
- `exchange_equity_final`
- `sum_agent_energy_final`
- `system_reserve_final`
- `identity_delta_final = exchange_equity_final - (sum_agent_energy_final + system_reserve_final)`
- `reconciliation_events_count`
- `explained_deltas_total_usdt`
- `unexplained_deltas_total_usdt`
- `unexplained_events[]` (each includes `tick`, `delta`, `reason_code`, `missing_evidence[]`)
- `audit_status = PASS | NOT_MEASURABLE | FAIL`
- `audit_reason` (short string)

---

## 4) Audit status rules

### 4.1 PASS

- `truth_profile=full_truth_pnl`
- `abs(identity_delta_final) <= tolerance_usdt`
- `unexplained_deltas_total_usdt == 0 within tolerance`
- every delta is traceable to evidence (`bills/fills/order_status`) or explicitly explained by a contracted category.

### 4.2 NOT_MEASURABLE (demo-allowed downgrade)

- `truth_profile=degraded_truth`
- any required evidence category is unavailable in demo (e.g., fills/bills missing fields)
- **no fabrication**: unknowns remain unknown, and unresolved deltas are explicitly listed.

### 4.3 FAIL

- evidence chain missing (e.g., deltas adjusted without reason_code)
- silent fabrication detected (unknowns treated as zeros without mask/quality)
- `abs(identity_delta_final) > tolerance_usdt` and no allowed downgrade condition applies

---

## 5) Liqudiation / forced-close evidence requirement (when detected)

If liquidation/ADL/forced-close is detected or suspected, post-run audit MUST attempt to attach:
- bills (preferred) OR fills/trades OR order_status markers
- if unavailable in demo: must be listed under `missing_evidence[]` and cause NOT_MEASURABLE for that claim category.


