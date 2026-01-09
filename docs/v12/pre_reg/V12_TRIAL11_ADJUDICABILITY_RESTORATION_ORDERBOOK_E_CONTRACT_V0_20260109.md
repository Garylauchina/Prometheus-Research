# V12 Pre-reg — Trial-11 Adjudicability Restoration via Order-Book E-Contract (do-or-die) v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Context (frozen facts):
- Under SSOT §9 (fail-closed `L_liq`, no fixed-spread fallback), the current BTC 2021–2022 replay dataset is **NOT_MEASURABLE** for E-liquidity:
  - bid/ask coverage = 0.0
  - Gate report: `docs/v12/artifacts/e_liquidity_gate/eligibility_btc_2021_2022_v0_20260109/README.md`

Goal of Trial-11:
- Restore **adjudicability** by upgrading the replay E-contract to include order-book L1 (bid/ask).

Hard bans (frozen):
- No fixed-spread fallback from `last_px`.
- No mechanism changes to gate logic (only restore measurability of E input truth).
- No prediction models.

References:
- Survival Space SSOT (L_liq fail-closed): `docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md` (§9)
- E-liquidity eligibility gate SSOT: `docs/v12/V12_GATE_E_LIQUIDITY_MEASURABILITY_V0_20260109.md`

---

## 0. Hypothesis (frozen)

If the replay dataset provides auditable order-book L1 (`bid_px_1`, `ask_px_1`) with high coverage, then:
- E-liquidity becomes measurable (`L_liq_mask=1`) under SSOT §9,
- and `full` mode adjudication is no longer forced into a constant cap regime by a synthetic constant `L_liq`.

---

## 1. Frozen inputs

Dataset target (BTC 2021–2022):
- time range: `2021-01-01` .. `2022-12-31`
- bar: 1m ticks (same timeline length as existing replay dataset)

New dataset requirement (order-book enriched):
- `market_snapshot.jsonl` MUST include:
  - `bid_px_1` (string, parseable float > 0)
  - `ask_px_1` (string, parseable float > 0)
  - `bid_sz_1` / `ask_sz_1` (optional but recommended)
  - `last_px` may remain, but MUST NOT be used to synthesize bid/ask

Evidence requirement:
- The dataset builder must archive provenance:
  - source endpoints (e.g., OKX `books5` + candles/ticker)
  - run manifest / build manifest
  - input raw evidence (or references) sufficient to audit that bid/ask were not synthesized

---

## 2. Frozen qualification gates (do-or-die)

### Gate G1: E-liquidity measurability eligibility

Run:
- `python3 tools/v12/verify_e_liquidity_measurability_gate_v0.py --dataset_dir <DATASET_DIR> --min_ticks 1000 --coverage_threshold 0.95`

PASS if:
- verdict = PASS (coverage >= 0.95)

FAIL if:
- verdict != PASS

### Gate G2: Survival Space verifier (no forbidden fallback)

For one minimal `full` run on the new dataset:
- `python3 tools/v12/verify_survival_space_em_v1.py --run_dir <RUN_DIR>`

PASS criteria:
- verdict is **PASS** (or at least not FAIL due to SSOT §9 fallback ban)
- `survival_space.jsonl` contains **no** `liq:spread_bps_from_last_px_fallback`

---

## 3. Frozen minimal execution (Quant side)

1) Build the order-book enriched replay dataset directory (new dataset_dir).
2) Run Gate G1 (must PASS).
3) Run a minimal Survival Space run (full mode):
   - steps: 2000 (minimum)
   - seeds: 3 (71001/71002/71003)
   - `probe_attempts_per_tick=1`
4) Verify each run with Research verifier (must satisfy Gate G2).

---

## 4. Frozen acceptance / rejection

Trial-11 verdict:
- **PASS** if:
  - Gate G1 PASS, and
  - all 3 minimal runs satisfy Gate G2 (no forbidden fallback; adjudication evidence is measurable)
- **FAIL** otherwise.

Stop rule:
- If FAIL ⇒ stop. Do not “tune” by introducing synthetic E fields.

---

## 5. Completion anchors (append-only)

- quant_commit:
- dataset_dir_new:
- g1_gate_report:
- run_dirs:
- verifier_reports:
- verdict:

### Completion record — 2026-01-09 (append-only)

- quant_commit: `d5cc98fbf8340f87dd751efd2a01a044bbe13dd2`
- dataset_dir_new: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v1_orderbook_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`
- g1_gate_report:
  - operator path: `/tmp/trial11_e_liquidity_gate_report.json`
  - archived: `docs/v12/artifacts/trial11_orderbook_e_contract_v0_20260109/g1_e_liquidity_gate_report.json`
- run_dirs (operator):
  - `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T123943Z_seed71001_full`
  - `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T123945Z_seed71002_full`
  - `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T123946Z_seed71003_full`
- verifier_reports (archived):
  - `docs/v12/artifacts/trial11_orderbook_e_contract_v0_20260109/verify_run_seed71001.json`
- provenance evidence (archived):
  - `docs/v12/artifacts/trial11_orderbook_e_contract_v0_20260109/dataset_build_manifest.json`
  - `docs/v12/artifacts/trial11_orderbook_e_contract_v0_20260109/g0_orderbook_provenance_gate_report.json`
- verdict: **FAIL**
  - reason: Delivered dataset uses **synthetic** bid/ask derived from `last_px` (fixed spread), violating Trial-11 hard ban: "No fixed-spread fallback from `last_px`."
  - recomputed verdict: `docs/v12/artifacts/trial11_orderbook_e_contract_v0_20260109/trial11_recomputed_verdict.json`
