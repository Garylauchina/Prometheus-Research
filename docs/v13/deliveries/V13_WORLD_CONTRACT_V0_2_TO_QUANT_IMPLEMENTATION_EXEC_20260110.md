# Delivery — Quant Implementation Instructions — V13 World Contract v0.2 (evidence closure) — 2026-01-10

Repo (Quant): `/Users/liugang/Cursor_Store/Prometheus-Quant`

This instruction file (Research, absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_WORLD_CONTRACT_V0_2_TO_QUANT_IMPLEMENTATION_EXEC_20260110.md`

## 0) Goal (do-or-die)

Implement **Contract Layer** evidence closure for each observation run:
- generate `evidence.json` (machine-verifiable)
- ensure `world_events` never enters contract reasons
- allow fork-on-world-event without rewriting historical runs

Reference (must read):
- V13 SSOT World Contract v0.2:  
  `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/V13_SSOT_WORLD_CONTRACT_V0_2_20260110.md`
- Spec JSON (machine-readable):  
  `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/spec/world_contract_v0_2_spec.json`
- Research verifier tool (read-only):  
  `/Users/liugang/Cursor_Store/Prometheus-Research/tools/v13/verify_world_contract_v0_2.py`

---

## 1) What to implement (Quant side)

### 1.1 Produce `evidence.json` per run_dir

In each run directory, write:
- `<RUN_DIR>/evidence.json`

Format (frozen for v0.2 verifier):
- JSON array of objects
- Each object MUST contain fields:
  - `timestamp` (str)
  - `strategy_id` (str, non-empty)  ← join key
  - `life_verdict` (str)            ← alive/dead/etc (life layer readout only)
  - `contract_reason_codes` (list)  ← MUST be [] in normal runs
  - `ablation_flags` (list)         ← [] or list of strings
  - `channels` (list)               ← must include `market_api` and `observation_window`

Important:
- `contract_reason_codes` MUST NOT contain narrative reasons.  
  The verifier will FAIL if non-empty even when gates pass.

### 1.2 Keep `world_events` separate (critical boundary)

If you log world events, they MUST:
- never enter `contract_reason_codes`
- never change a past run verdict
- only trigger a **fork** (new run_id) with copied spec + new metadata

### 1.3 Fork mechanism (institutional non-stationarity)

When any of these happens:
- contract rules change
- instrument renamed/offlined
- channel semantics change

Do:
- create a new run_id / run_dir
- copy contract spec reference (do not mutate old)
- continue capture under new run_id

Do NOT:
- retroactively rewrite old run evidence

### 1.4 Shadow / Exploration isolation

Shadow outputs:
- must be written under a separate namespace/dir
- must not produce `evidence.json` that is used for Contract PASS
- if promoted, rerun as a formal run under full Contract closure

---

## 2) Verification (Research-run, you can run locally too)

After generating one run_dir with `evidence.json`, run:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v13/verify_world_contract_v0_2.py \
  --run_dir "<RUN_DIR>" \
  --output_json /tmp/v13_world_contract_v0_2_verdict.json
```

Expected:
- `verdict` = `PASS`

Negative controls (must trigger fail-closed):
- delete `evidence.json` ⇒ `FAIL` + `fail:evidence_file_missing`
- corrupt JSON ⇒ `FAIL` + `fail:evidence_parse_error`
- remove required field ⇒ `FAIL` + `fail:schema_field_missing`
- omit required channel ⇒ `NOT_MEASURABLE` + `not_measurable:channel_missing:*`

---

## 3) Return to Research

Send back:
- Quant commit hash
- One representative run_dir absolute path
- `/tmp/v13_world_contract_v0_2_verdict.json`
- a short note: where you store `world_events` and how fork is triggered (facts only)

