# V12 — Survival Space (E+M) v1.0.1 (Fix-M Proportional) — Extended Validation Milestone — 2026-01-09

Additive-only. This document is a milestone record (no narrative).
It freezes the extended validation outcome and pointers to the finalized evidence bundle.

---

## §0 Scope / contract alignment (frozen)

- This milestone is about **Survival Space shaping actionability** via **gate only**.
- Non-goals (still enforced): rollout / planning / reward / learning / runtime adaptation.
- **Primary gate effect metric** for this milestone is **suppression (cap/downshift)**, not only hard blocks:
  - `suppression_ratio = (Σ proposed_intensity − Σ post_gate_intensity) / Σ proposed_intensity`
  - `downshift_rate = P(post_gate_intensity < interaction_intensity)`
  - `block_rate = P(action_allowed == false)` (secondary)

Reason:
- In this mechanism family, the gate may express itself mostly as **intensity caps** while keeping `action_allowed=true`.

---

## §1 Evidence bundle (finalized; frozen pointers)

Finalized artifact bundle (append-only):
- `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/README.md`

Contained files (frozen names):
- `summary.json`
- `per_run_metrics.jsonl`
- `final_440_run_ids.txt`

Fail-closed verifier requirement (frozen for milestone):
- Every run in `final_440_run_ids.txt` must be **PASS** under:
  - `tools/v12/verify_survival_space_em_v1.py`

---

## §2 Dataset / run set (frozen)

Final run set:
- total: 440 runs
- modes:
  - `full`: 200
  - `no_e`: 200
  - `no_m`: 20
  - `null`: 20

Quant runs root (read-only; external):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/`

Final run list source (frozen pointer):
- `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/final_440_run_ids.txt`

---

## §3 Tooling (frozen)

Summarizer tool (Research, stdlib-only):
- `tools/v12/summarize_survival_space_em_extended_summary_v0.py`

Recorded command (frozen entry):

```bash
python3 tools/v12/summarize_survival_space_em_extended_summary_v0.py \
  --runs_root "/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool" \
  --run_list_file /tmp/v12_survival_space_em_v1_fixm_extended_final_440_runs.txt \
  --output_dir /tmp/survival_space_em_v1_fixm_extended_summary_final_440_20260109
```

---

## §4 Aggregated results (frozen snapshot)

Source of truth for these numbers:
- `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/summary.json`

All values below are copied from `summary.json` (frozen snapshot).

### §4.1 `full` (n=200)

- suppression_ratio:
  - mean=0.3791462862, std=0.3632300289
  - p50=0.1670802110, p75=0.9999699944
- downshift_rate:
  - mean=0.3773939000, std=0.2181187825
  - p50=0.2509000000, p75=0.7452650000
- block_rate:
  - mean=0.2499950000, std=0.4330040416
  - p50=0.0000000000, p75=0.2499950000, p90=0.9999800000
- order_attempts_count:
  - mean=46532.0650, std=27224.0359
  - p10=0.0000, p25=2.25, p50=62359.0, p75=62553.75

### §4.2 `no_e` (n=200)

- suppression_ratio:
  - mean=0.2988675898, std=0.4101987444
  - p50=0.0598709177, p75=0.9999699948
- downshift_rate:
  - mean=0.2570709000, std=0.2885147326
  - p50=0.0897900000, p75=0.7452650000
- block_rate:
  - mean=0.2549949000, std=0.4358524992
  - p50=0.0000000000, p75=0.9999800000
- order_attempts_count:
  - mean=52560.3700, std=30751.3262
  - p10=0.0000, p25=2.25, p50=70403.0, p75=70695.5

### §4.3 Controls

`no_m` (n=20):
- suppression_ratio mean=0.1664283994 (std=0.0011695722)
- downshift_rate mean=0.2495490000 (std=0.0025581280)
- block_rate mean=0.0000000000

`null` (n=20):
- suppression_ratio mean=0.0000000000
- downshift_rate mean=0.0000000000
- block_rate mean=0.0000000000

---

## §5 Do-not-misread constraints (frozen)

- Do not interpret `block_rate` alone as “gate absent”.
  - Gate may act primarily via `intensity_cap` and `post_gate_intensity`.
- “0 attempts” is a valid outcome **only if**:
  - `order_attempts.jsonl` and `okx_api_calls.jsonl` exist (may be empty),
  - and verifier PASS holds for the run.

