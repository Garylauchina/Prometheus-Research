# Trial-11 Artifacts — Adjudicability Restoration via Order-Book E-Contract — 2026-01-09

This directory is an **immutable archive** of the Quant-side delivery for Trial-11 and Research-side independent re-verification.

## Summary (auditable)

- **Quant commit**: `d5cc98fbf8340f87dd751efd2a01a044bbe13dd2`
- **Delivered dataset_dir**:
  - `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v1_orderbook_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`
- **G1 (E-liquidity coverage gate)**: PASS (coverage=1.0)
- **G0 (order-book provenance gate)**: **FAIL** (synthetic order-book detected)
- **Trial-11 verdict (SSOT / pre-reg)**: **FAIL**

Reason (hard ban violation):
- Trial-11 pre-reg explicitly forbids synthesizing bid/ask from `last_px`.
- Delivered dataset is explicitly `replay_v1_synthetic_orderbook`, using fixed spread from `last_px`.

## Evidence files

- `PROGRAMMER_COMPLETION_REPORT.md`: original delivery report (Quant side)
- `dataset_build_manifest.json`: provenance manifest; contains `synthesis_method` from `last_px`
- `g1_e_liquidity_gate_report.json`: Research gate G1 report (coverage only)
- `g0_orderbook_provenance_gate_report.json`: Research gate G0 report (**FAIL**)
- `verify_run_seed71001.json`: Research verifier output for one representative run_dir (PASS on run evidence, but does not validate order-book provenance)

