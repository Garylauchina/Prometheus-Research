# V12 Gate — E-liquidity Measurability Qualification (bid/ask coverage) v0 — 2026-01-09

Additive-only. This gate freezes a **qualification verdict**:

> Under the fail-closed E-liquidity contract (no fixed-spread fallback), is a replay dataset eligible to support `L_liq`?

This gate is executed **before** any trial that depends on `L_liq` (directly or via `L=min(L_liq,L_imp)` in `full` mode).

---

## §0 Scope (frozen)

Applies to:
- replay datasets that provide `market_snapshot.jsonl`
- any Survival Space / gate adjudication trial that requires E-liquidity measurability

Does not apply to:
- M-only tools (impedance-only), or experiments explicitly pre-registered as `no_e`

---

## §1 Contract (frozen)

Required fields per tick (for `L_liq` eligibility):
- `bid_px_1` (non-null, parseable number > 0)
- `ask_px_1` (non-null, parseable number > 0)

Hard ban:
- No synthetic bid/ask derived from `last_px` with any fixed spread.

---

## §2 Gate metric (frozen)

For a dataset with N ticks:
- `eligible_tick` iff (bid_px_1 and ask_px_1 are both present and valid)
- `coverage = eligible_tick_count / N`

---

## §3 Verdict (frozen)

- **PASS** if:
  - `N >= 1000` and `coverage >= 0.95`
- **NOT_MEASURABLE** if:
  - `N >= 1000` but `coverage < 0.95` (E-liquidity cannot be used; any L_liq-dependent trial must be pre-registered as NOT_MEASURABLE)
- **FAIL** if:
  - missing `market_snapshot.jsonl` or invalid JSONL (evidence broken)
  - `N < 1000` (insufficient evidence)

---

## §4 Output / archival (frozen)

Gate output must include:
- dataset_dir
- N
- eligible_tick_count
- coverage
- sample invalid reasons (counts)
- verdict

