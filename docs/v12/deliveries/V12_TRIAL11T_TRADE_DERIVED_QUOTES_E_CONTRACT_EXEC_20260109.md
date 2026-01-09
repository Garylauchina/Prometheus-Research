# Delivery — Quant Instructions — Trial-11T Trade-Derived Quotes E-Contract (proxy bid/ask from trades) — 2026-01-09

Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

This instruction file (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_TRIAL11T_TRADE_DERIVED_QUOTES_E_CONTRACT_EXEC_20260109.md`

Goal (do-or-die):
- Build a replay dataset where `bid_px_1/ask_px_1` are **trade-derived proxies** (NOT order-book).
- Prove provenance (non-synthetic; trade-derived) via Research gate.
- Prove coverage eligibility (>=0.95) via Research gate.
- Run minimal `full` runs and verify they pass Research verifier.

Hard bans:
- No fixed-spread or any `last_px`-derived synthetic bid/ask.
- Do NOT describe this as “order-book restoration”. It is explicitly a proxy E-contract.

Research references:
- Trial-11T pre-reg:
  - `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_TRIAL11T_TRADE_DERIVED_QUOTES_E_CONTRACT_V0_20260109.md`
- E-liquidity coverage gate SSOT:
  - `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_GATE_E_LIQUIDITY_MEASURABILITY_V0_20260109.md`
- Survival Space SSOT (L_liq fail-closed; no fallback):
  - `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md` (§9)

---

## A) Build a new dataset_dir with trade-derived bid/ask proxies

Input:
- Source dataset: BTC 2021–2022 candle replay dataset (existing v0 dataset_dir)
- Source trades: OKX `history-trades` endpoint (must be auditable; record pagination and join rule)

Frozen contract (must match pre-reg):
- window: 60 seconds (per tick)
- `bid_px_1` = max buy trade price in window
- `ask_px_1` = min sell trade price in window
- If missing buy or sell in window ⇒ set that side null ⇒ tick NOT_MEASURABLE under coverage gate

Required additional fields in `market_snapshot.jsonl`:
- `quote_source`: `"trade_derived"`
- `trade_window_s`: `60`
- (Recommended) `trades_buy_count_window`, `trades_sell_count_window`

Build manifest:
- Write `dataset_build_manifest.json` in dataset_dir:
  - `dataset_version` MUST include `trade_derived`
  - include `trade_provenance` object
  - explicit disclaimer: not order-book

Output dataset directory (example name, you choose):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v1_trade_derived_quotes_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`

---

## B) Run Gate G0T (Research provenance gate) — must PASS

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_orderbook_e_contract_provenance_gate_v0.py \
  --expected_source trade_derived \
  --dataset_dir "<NEW_DATASET_DIR>" \
  --sample_lines 50 \
  --output_json /tmp/trial11t_trade_derived_provenance_gate_report.json
```

Expected:
- verdict = PASS

---

## C) Run Gate G1T (Research coverage gate) — must PASS

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_e_liquidity_measurability_gate_v0.py \
  --dataset_dir "<NEW_DATASET_DIR>" \
  --min_ticks 1000 \
  --coverage_threshold 0.95 \
  --output_json /tmp/trial11t_e_liquidity_gate_report.json
```

Expected:
- verdict = PASS

---

## D) Run minimal Survival Space runs (full only) — 3 seeds

```bash
DATASET="<NEW_DATASET_DIR>"
RUNS_ROOT="/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool"

for SEED in 71101 71102 71103; do
  python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/run_survival_space_em_v1.py \
    --dataset_dir "$DATASET" \
    --runs_root "$RUNS_ROOT" \
    --steps 2000 \
    --seed "$SEED" \
    --ablation_mode full \
    --probe_attempts_per_tick 1 || exit 1
done
```

---

## E) Verify each run_dir (Research verifier) — must PASS/MEASURABLE

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_survival_space_em_v1.py --run_dir "<RUN_DIR>"
```

Hard checks:
- Must NOT contain forbidden reason code: `liq:spread_bps_from_last_px_fallback`
- If bid/ask coverage gate passed, `L_liq_mask` should be 1 for most ticks

---

## F) Return to Research

Send back:
- Quant commit hash
- New dataset_dir absolute path
- `/tmp/trial11t_trade_derived_provenance_gate_report.json`
- `/tmp/trial11t_e_liquidity_gate_report.json`
- List of the 3 new run_dirs (absolute paths)

