# Delivery — Quant Instructions — Trial-11 Adjudicability Restoration via Order-Book E-Contract — 2026-01-09

This instruction file (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_TRIAL11_ORDERBOOK_E_CONTRACT_EXEC_20260109.md`

Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal (do-or-die):
- Build a new replay dataset with **order-book L1 bid/ask** so E-liquidity is eligible under fail-closed contract.
- Prove eligibility via Research gate (coverage>=0.95).
- Run minimal `full` runs and verify they are measurable (no forbidden fallback).

Research references:
- Trial-11 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_TRIAL11_ADJUDICABILITY_RESTORATION_ORDERBOOK_E_CONTRACT_V0_20260109.md`
- E-liquidity gate SSOT: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_GATE_E_LIQUIDITY_MEASURABILITY_V0_20260109.md`
- Survival Space SSOT (L_liq fail-closed): `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md` (§9)

---

## A) Build a new dataset_dir with bid/ask (no synthesis)

Requirement:
- `market_snapshot.jsonl` must include valid `bid_px_1` and `ask_px_1` (float>0) for >=95% ticks.
- `bid/ask` must come from order-book endpoint (e.g., OKX `books5`), not from `last_px`.

Suggested evidence approach:
- For each tick timestamp:
  - candle/last_px from history candles
  - bid/ask from `books5` sampled at that tick (or nearest within a tight window you freeze and record)

Output dataset directory (example name, you choose):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v1_orderbook_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`

Also write a build manifest inside dataset_dir:
- `dataset_build_manifest.json`
  - source endpoints used
  - sampling/join rule for books↔candle (frozen)
  - counts and coverage numbers
  - quant_commit hash

---

## B) Run Gate G1 (Research tool) — must PASS

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_e_liquidity_measurability_gate_v0.py \
  --dataset_dir "<NEW_DATASET_DIR>" \
  --min_ticks 1000 \
  --coverage_threshold 0.95 \
  --output_json /tmp/trial11_e_liquidity_gate_report.json
```

Expected:
- verdict = PASS

---

## C) Run minimal Survival Space runs (full only) — 3 seeds

```bash
DATASET="<NEW_DATASET_DIR>"
RUNS_ROOT="/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool"

for SEED in 71001 71002 71003; do
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

## D) Verify each run_dir (Research verifier) — must be PASS/MEASURABLE

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/verify_survival_space_em_v1.py --run_dir "<RUN_DIR>"
```

Hard checks:
- Must NOT contain forbidden reason code: `liq:spread_bps_from_last_px_fallback`
- `L_liq_mask` should be 1 for most ticks (given coverage gate passed)

---

## E) Return to Research

Send back:
- Quant commit hash
- New dataset_dir absolute path
- `/tmp/trial11_e_liquidity_gate_report.json`
- List of the 3 new run_dirs (absolute paths)

