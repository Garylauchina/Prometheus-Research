# V12 Pre-reg — Trial-12 Real-time Order-Book Capture E-Contract (books5 + trades) v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Context (frozen facts):
- Trial-11 (historical order-book) is blocked by data availability.
- Trial-11T (trade-derived quotes for 2021–2022 replay) is NOT_MEASURABLE because OKX `history-trades` does not provide 2021–2022 trades.
- The only viable path to restore adjudicable E-liquidity with real bid/ask is: **capture real-time books** and build a new replay dataset from captured evidence.

Hard boundary (frozen):
- This trial changes the **dataset era** (recent live capture) and must not be mixed with 2021–2022 replay conclusions.

---

## 0. Hypothesis (frozen, minimal)

If we capture real-time order-book L1 (bid/ask) and trades with auditable provenance, then:
- E-liquidity becomes measurable (`L_liq_mask=1`) under SSOT §9 (no fallback),
- and Survival Space `full` runs become adjudicable on a real bid/ask E-contract dataset.

---

## 1. Frozen capture contract

Instrument:
- `BTC-USDT-SWAP`

Streams (required):
- Order-book: OKX `books5` (L1 bid/ask must be extractable per tick)
- Trades: OKX `trades` (used to sanity-check and provide auxiliary provenance; not used to synthesize bid/ask)

Capture duration (minimum):
- At least 7 days of continuous capture (do-or-die minimum).

Ticking:
- Build 1m ticks aligned by `ts_utc` (ISO8601) in a new replay dataset.

Hard ban:
- No `last_px`-derived bid/ask synthesis.

---

## 2. Frozen dataset output

Dataset directory (example):
- `datasets_v12/dataset_replay_v2_live_orderbook_SWAP_BTC-USDT-SWAP_<START_UTC>__<END_UTC>_bar1m`

Required files:
- `market_snapshot.jsonl` (must include `bid_px_1`, `ask_px_1`, `last_px` optional)
- `dataset_build_manifest.json` with:
  - `dataset_version` includes `live_orderbook`
  - `orderbook_provenance` (endpoint, sampling rule, reconnect policy, gap policy)
  - `trade_provenance` (endpoint, sampling rule)
  - coverage statistics for bid/ask
  - explicit statement: bid/ask are from books5

---

## 3. Frozen gates (do-or-die)

### Gate G0: Provenance (must PASS)

Run (Research):
- `python3 tools/v12/verify_orderbook_e_contract_provenance_gate_v0.py --expected_source orderbook --dataset_dir <DATASET_DIR> ...`

PASS iff:
- verdict = PASS

### Gate G1: E-liquidity coverage (must PASS)

Run (Research):
- `python3 tools/v12/verify_e_liquidity_measurability_gate_v0.py --dataset_dir <DATASET_DIR> --coverage_threshold 0.95 ...`

PASS iff:
- verdict = PASS

---

## 4. Minimal execution (Quant side; frozen)

1) Deploy a real-time recorder (books5 + trades) and capture >=7 days.
2) Build dataset_dir (1m ticks) from captured evidence.
3) Run Gate G0 + G1 (must both PASS).
4) Run minimal Survival Space runs (full only):
   - steps: 2000
   - seeds: 3 (71201/71202/71203)
   - `probe_attempts_per_tick=1`
5) Verify each run with Research verifier (must PASS; no forbidden fallback code).

---

## 5. Verdict (frozen)

Trial-12 verdict:
- **PASS** if G0 PASS and G1 PASS and all 3 runs verifier PASS.
- **FAIL** otherwise.

---

## 6. Completion anchors (append-only)

- quant_commit:
- dataset_dir_new:
- capture_window_utc:
- g0_provenance_gate_report:
- g1_coverage_gate_report:
- run_dirs:
- verifier_reports:
- verdict:

