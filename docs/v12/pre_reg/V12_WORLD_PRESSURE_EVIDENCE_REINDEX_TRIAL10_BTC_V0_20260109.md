# V12 Pre-reg — BTC Evidence Re-indexing by Consensus Epochs (world_u boundaries) — Trial-10 v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Hard constraints (frozen):
- **Descriptive audit only** (no prediction models).
- **No mechanism changes** (no code/parameter changes in Quant runner; no feedback loops).
- Single dataset only (BTC 2021–2022), full only, no expansion.

Prerequisite (frozen):
- Trial-9 consensus epoch boundaries (annotation-only, PASS):
  - `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/epoch_candidates.json`

---

## 0. Purpose (frozen)

Use Trial-9 consensus epochs as a new **audit coordinate system** to reorganize existing evidence-chain statistics:

- Within each epoch: world_u distribution, gate stats (suppression/downshift/block), fail-closed event density, residence time.
- Between epochs: distribution differences / effect sizes **only** (no predictive modeling).

This trial answers:

> Do consensus epochs produce stable, cross-seed distinguishable structure in evidence-chain statistics?

---

## 1. Frozen inputs

Consensus boundaries (tick indices, N=10000; frozen):
- `[644, 3837, 5812, 6339, 6676]`

Runs (frozen; same 3 full runs as Trial-8/9):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full`

Evidence files used (frozen; all must exist, else FAIL):
- `interaction_impedance.jsonl` (world_u per tick)
- `decision_trace.jsonl` (gate outcomes per tick)
- `errors.jsonl` (may be empty; must exist; used for fail-closed event density)

Join rule (frozen):
- Use strict implicit ordering **within each file** (line index == tick index).
- Additionally require `ts_utc` line-by-line equality between `interaction_impedance.jsonl` and `decision_trace.jsonl` (fail-closed).

---

## 2. Frozen epoch construction

Epoch boundaries define segments:
- E0: [0, 644)
- E1: [644, 3837)
- E2: [3837, 5812)
- E3: [5812, 6339)
- E4: [6339, 6676)
- E5: [6676, 10000)

Residence time per epoch:
- `len(Ei)` ticks

---

## 3. Frozen per-epoch metrics (descriptive)

### 3.1 world_u distribution (from interaction_impedance)
- mean, std, min, p50, p90, p99, max

### 3.2 gate statistics (from decision_trace)

Define per tick:
- attempted := (interaction_intensity > 0)
- suppression := 0 if not attempted else 1 - post_gate_intensity / interaction_intensity
- block := attempted AND (post_gate_intensity == 0)
- downshift := attempted AND (0 < post_gate_intensity < interaction_intensity)

Per epoch:
- attempted_rate
- block_rate
- downshift_rate
- suppression (mean + distribution stats)

### 3.3 fail-closed event density (from errors.jsonl)
- `errors_per_1k_ticks = 1000 * errors_count_in_epoch / len(epoch)`

---

## 4. Frozen between-epoch difference audit (no prediction)

For each run (seed) and each ordered pair of epochs (Ei, Ej):

Continuous metrics effect size:
- Cohen’s d for:
  - world_u
  - suppression

Rate metrics difference:
- absolute difference for:
  - block_rate
  - downshift_rate
  - attempted_rate

---

## 5. Do-or-die verdict (frozen)

Define “distinguishable epoch pair” (Ei, Ej) if **both** hold:
- `min_seed |d_world_u(Ei,Ej)| >= 0.30`
- and at least one gate metric has stable difference:
  - `min_seed |Δ block_rate(Ei,Ej)| >= 0.05` OR
  - `min_seed |Δ downshift_rate(Ei,Ej)| >= 0.05` OR
  - `min_seed |d_suppression(Ei,Ej)| >= 0.30`

PASS if:
- There exist at least **2** distinguishable epoch pairs, and
- The union of epochs involved covers at least **3 distinct epochs**.

FAIL otherwise.

Meaning:
- PASS ⇒ epoch annotation has evidence-chain meaning (structure is stable and auditable).
- FAIL ⇒ boundaries are only a mathematical cut with no stable audit value (under current evidence).

---

## 6. Completion anchors (append-only)

- analysis_tool:
- artifacts_dir:
- output_files:
- verdict:


---

## 7. Completion record (append-only)

- analysis_tool: `tools/v12/reindex_btc_evidence_by_consensus_epochs_v0.py`
- artifacts_dir: `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/`
- output_files:
  - `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/per_run_epoch_metrics.json`
  - `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/between_epoch_effects.json`
  - `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/between_epoch_effects_top50.json`
  - `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/aggregate_verdict.json`
  - `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/trial10_btc_evidence_reindex_report.md`
- verdict: **FAIL** (distinguishable_pairs=0 under frozen thresholds)
