# V12 Pre-reg — Trial-11T Trade-Derived Quotes E-Contract (proxy bid/ask from trades) v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Context (frozen facts):
- OKX public APIs do not provide **historical order-book** snapshots for long horizons via the same interface as candles.
- Trial-11 (order-book E-contract) remains the “true restoration” path and has a hard ban against any `last_px`-derived synthetic bid/ask.
- This Trial-11T defines a **separate E-contract**: *trade-derived bid/ask proxies*, explicitly **NOT** order-book.

Hard boundary (frozen):
- This Trial-11T MUST NOT be misreported as “order-book restoration”.
- Any downstream SSOT that requires order-book must treat trade-derived as **NOT_ELIGIBLE** unless explicitly allowed.

---

## 0. Hypothesis (frozen, minimal)

If we derive per-tick bid/ask proxies from **historical trades** with auditable provenance, then:
- we can restore a non-trivial E-liquidity readout path (`L_liq_mask=1`) without forbidden synthetic spread from `last_px`,
- while preserving fail-closed semantics for sparse periods (no buy or no sell trades ⇒ NOT_MEASURABLE for that tick).

This is a **mechanism validation / measurability bridge**, not a claim about true order-book microstructure.

---

## 1. Frozen E-contract definition (trade-derived quotes)

Per tick \(t\) (1m bar), define a time window:
- window = \([t - W, t]\)
- default \(W = 60s\) (frozen for this trial)

Let `trades_in_window` be all trades in the window, with fields:
- `ts_utc` (ISO8601)
- `px` (float>0)
- `side` in {`buy`,`sell`} (as provided by OKX history-trades)

Define proxies:
- `bid_px_1_proxy = max(px) over side=buy trades in window`
- `ask_px_1_proxy = min(px) over side=sell trades in window`

Fail-closed:
- If no buy trades in window ⇒ `bid_px_1_proxy = null`
- If no sell trades in window ⇒ `ask_px_1_proxy = null`
- If either missing ⇒ E-liquidity is NOT_MEASURABLE for that tick.

Required fields in `market_snapshot.jsonl` for this contract:
- `bid_px_1` = `bid_px_1_proxy`
- `ask_px_1` = `ask_px_1_proxy`
- `quote_source` (string) MUST be `trade_derived`
- `trade_window_s` (int) MUST be 60

---

## 2. Frozen provenance requirements

Dataset directory MUST contain `dataset_build_manifest.json` including:
- `dataset_version` includes `trade_derived` (e.g., `replay_v1_trade_derived_quotes`)
- `trade_provenance` object with:
  - source endpoint: OKX `history-trades`
  - pagination / time slicing rule (frozen)
  - any rate limit handling (frozen)
  - summary counts (total trades, buy/sell counts)
  - join rule (trade→tick window)
- Explicit statement: “Not order-book; trade-derived quotes only.”

Hard ban:
- `synthesis_method` (any `last_px` spread-based synthesis) is forbidden.

---

## 3. Frozen gates (do-or-die)

### Gate G0T: Provenance (must PASS)

Run (Research):
- `python3 tools/v12/verify_orderbook_e_contract_provenance_gate_v0.py --expected_source trade_derived --dataset_dir <DATASET_DIR> ...`

PASS if:
- verdict = PASS

FAIL if:
- verdict = FAIL

NOT_MEASURABLE if:
- verdict = NOT_MEASURABLE (insufficient provenance evidence)

### Gate G1T: Coverage (must PASS or mark NOT_MEASURABLE)

Run (Research coverage gate; bid/ask presence only):
- `python3 tools/v12/verify_e_liquidity_measurability_gate_v0.py --dataset_dir <DATASET_DIR> --coverage_threshold 0.95 ...`

Interpretation (frozen):
- PASS ⇒ trade density is sufficient for this trial
- NOT_MEASURABLE ⇒ this dataset cannot support E-liquidity under trade-derived contract (stop)

---

## 4. Minimal execution (Quant side; frozen)

1) Build dataset_dir with trade-derived bid/ask proxies for BTC 2021–2022.
2) Run Gate G0T (must PASS).
3) Run Gate G1T (must PASS; else mark NOT_MEASURABLE and stop).
4) Run minimal Survival Space runs (full only):
   - steps: 2000
   - seeds: 3 (71101/71102/71103)
   - `probe_attempts_per_tick=1`
5) Verify each run with Research verifier (must PASS, and must not contain forbidden fallback code).

---

## 5. Verdict (frozen)

Trial-11T verdict:
- **PASS** if:
  - G0T PASS, and
  - G1T PASS, and
  - all 3 runs are verifiable (Research verifier PASS)
- **NOT_MEASURABLE** if:
  - G0T PASS but G1T NOT_MEASURABLE (coverage too low; sparse)
- **FAIL** otherwise.

---

## 6. Completion anchors (append-only)

- quant_commit:
- dataset_dir_new:
- g0t_provenance_gate_report:
- g1t_coverage_gate_report:
- run_dirs:
- verifier_reports:
- verdict:

