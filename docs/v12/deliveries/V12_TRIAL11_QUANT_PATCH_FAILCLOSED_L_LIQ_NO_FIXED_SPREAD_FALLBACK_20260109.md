# Delivery — Quant Patch Request — Fail-closed L_liq (no fixed-spread fallback) — 2026-01-09

Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Purpose (hard):
- Enforce SSOT boundary: **E-liquidity (`L_liq`) is NOT_MEASURABLE in replay evidence when bid/ask are missing**.
- **Prohibit** any `last_px`-based fixed spread fallback that fakes bid/ask and yields a constant `L_liq`.

SSOT reference (Research repo):
- `docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md` (§9)

Patch target (Quant):
- `tools/v12/run_survival_space_em_v1.py`

Required code change (minimal):
1) In `_compute_L_liq_from_E(...)`:
   - REMOVE the block that synthesizes bid/ask from `last_px` with fixed spread.
   - If `bid_px_1` or `ask_px_1` is missing/unavailable (None/<=0):
     - return `(None, 0, ["not_measurable:market_missing_bid_ask"])`

2) Ensure the emitted `survival_space.jsonl` respects mask discipline:
   - `L_liq_mask=0` ⇒ `L_liq=null`
   - `L_liq_reason_codes` includes `not_measurable:market_missing_bid_ask`

3) No other behavior changes.

Acceptance (Research-side verifier expectation):
- Runs using last_px-only replay datasets should become **NOT_MEASURABLE** (because `L = min(L_liq,L_imp)` becomes NOT_MEASURABLE under SSOT).
- Any run that still contains `liq:spread_bps_from_last_px_fallback` must be **FAIL** (forbidden).

Return to Research:
- Quant commit hash
- One short smoke run_dir (e.g. 200–1000 steps) demonstrating:
  - `L_liq_mask=0` with reason `not_measurable:market_missing_bid_ask`
  - `verify_survival_space_em_v1.py` returns `NOT_MEASURABLE` (not PASS)

