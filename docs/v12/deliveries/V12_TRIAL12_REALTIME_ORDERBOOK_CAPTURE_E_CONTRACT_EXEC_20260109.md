# Delivery — Quant Instructions — Trial-12 Real-time Order-Book Capture E-Contract (books5 + trades) — 2026-01-09

Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

This instruction file (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_TRIAL12_REALTIME_ORDERBOOK_CAPTURE_E_CONTRACT_EXEC_20260109.md`

Goal (do-or-die):
- Capture **real** order-book bid/ask (books5) + trades in real-time for >=7 days.
- Build a new replay dataset (1m ticks) with `bid_px_1/ask_px_1` from books5 (no synthesis).
- Prove provenance + coverage via Research gates.
- Run minimal Survival Space runs (full) and verify.

Hard bans:
- No fixed-spread or any `last_px`-derived synthetic bid/ask.
- Trades are auxiliary evidence only; do not use trades to fabricate bid/ask.

Research references:
- Trial-12 pre-reg:
  - `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_TRIAL12_REALTIME_ORDERBOOK_CAPTURE_E_CONTRACT_V0_20260109.md`
- Provenance gate (G0):
  - `/Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_orderbook_e_contract_provenance_gate_v0.py`
- Coverage gate (G1):
  - `/Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_e_liquidity_measurability_gate_v0.py`
- Survival Space verifier:
  - `/Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_survival_space_em_v1.py`

---

## A) Deploy a real-time recorder (books5 + trades)

Requirement:
- Continuous capture for >=7 days (do not backfill).

Evidence discipline:
- Write raw captured JSONL (append-only) with timestamps and reconnect events.
- Record gaps explicitly (do not silently skip).

Output root example:
- `/Users/liugang/Cursor_Store/Prometheus-Quant/live_capture_v12/okx_btc_books5_trades_<START_UTC>/`

---

## B) Build dataset_dir (1m ticks) from captured evidence

Output dataset dir example:
- `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v2_live_orderbook_SWAP_BTC-USDT-SWAP_<START_UTC>__<END_UTC>_bar1m`

Must include:
- `market_snapshot.jsonl` with `bid_px_1`, `ask_px_1` from books5 (float>0)
- `dataset_build_manifest.json` with:
  - `dataset_version`: includes `live_orderbook`
  - `orderbook_provenance`: endpoint/books depth, sampling rule, gap policy
  - `trade_provenance`
  - coverage stats

---

## C) Run gates (Research) — must PASS

### Gate G0 (provenance)

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_orderbook_e_contract_provenance_gate_v0.py \
  --expected_source orderbook \
  --dataset_dir "<NEW_DATASET_DIR>" \
  --sample_lines 50 \
  --output_json /tmp/trial12_orderbook_provenance_gate_report.json
```

### Gate G1 (coverage)

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_e_liquidity_measurability_gate_v0.py \
  --dataset_dir "<NEW_DATASET_DIR>" \
  --min_ticks 1000 \
  --coverage_threshold 0.95 \
  --output_json /tmp/trial12_e_liquidity_gate_report.json
```

---

## D) Run minimal Survival Space runs (full only) — 3 seeds

```bash
DATASET="<NEW_DATASET_DIR>"
RUNS_ROOT="/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool"

for SEED in 71201 71202 71203; do
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

## E) Verify each run_dir (Research verifier)

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_survival_space_em_v1.py --run_dir "<RUN_DIR>"
```

Hard checks:
- Must NOT contain forbidden reason code: `liq:spread_bps_from_last_px_fallback`

---

## F) Return to Research

Send back:
- Quant commit hash
- capture root absolute path
- new dataset_dir absolute path
- `/tmp/trial12_orderbook_provenance_gate_report.json`
- `/tmp/trial12_e_liquidity_gate_report.json`
- list of 3 run_dirs (absolute paths)

