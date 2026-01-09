# V12 Pre-reg — World Pressure Epoch Annotation (from changepoints) — Trial-9 BTC v0 — 2026-01-09

Status: **PRE-REGISTERED**

Append-only after pre-registration. Completion anchors must be appended.

Operator constraints (frozen):
- **Annotation only**: produce epoch candidates as labels; do not change any downstream mechanism, parameters, or evaluation semantics.
- Single dataset only (BTC 2021–2022)
- Full only
- No expansion / no new experiments

Upstream prerequisite (frozen):
- Trial-8 boundary detector PASS (changepoints on `world_u`):
  - SSOT: `docs/v12/V12_SSOT_WORLD_PRESSURE_BOUNDARY_SIGNAL_V0_20260109.md`
  - Artifacts: `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/`

---

## 0. Purpose (frozen)

Institutionalize the Trial-8 boundary signal as a **pure epoch-annotation layer**:

- Input: changepoints \(\{t_k\}\) from Trial-8 per-run reports (3 seeds, full only).
- Output: epoch candidate boundaries and per-epoch descriptive stats, plus a cross-seed consistency audit.

This trial does **not** claim causality, and does **not** modify any system.

---

## 1. Frozen inputs

Runs (frozen; same as Trial-8):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092219Z_seed71001_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092251Z_seed71002_full`
- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T092326Z_seed71003_full`

Evidence source (frozen):
- Trial-8 per-run JSON reports:
  - `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/per_run_*.json`

Observable (frozen):
- `u_t = interaction_impedance.metrics.world_u` (used only for descriptive per-epoch stats)

---

## 2. Frozen construction: per-run epochs and consensus epochs

Per-run epoch candidates:
- For each run r, take its ordered changepoints `CP_r = [t1, t2, ...]`
- Define epochs as segments: `[0,t1), [t1,t2), ..., [t_last, N)`

Consensus epoch candidates (frozen):
- Let `K = min(|CP_r|)` across runs (K>=1 required).
- For k=1..K:
  - Normalize each run’s k-th changepoint: `p_{r,k} = t_{r,k}/N`.
  - Define consensus position `p*_k = median_r(p_{r,k})`.
  - Define consensus boundary `t*_k = round(p*_k * N)`.
- Consensus epochs are segments `[0,t*_1), [t*_1,t*_2), ..., [t*_K,N)`.

No further optimization of boundaries is allowed.

---

## 3. Frozen outputs

Artifacts must include:
- Per-run epoch boundaries + per-epoch stats (mean/std/min/max of u, duration).
- Consensus epoch boundaries + same stats computed on each run (using consensus boundaries).
- Cross-seed consistency audit:
  - For each k<=K: std(p_{r,k}) and pass/fail threshold (reusing Trial-8 rule: std<=0.05).
  - Per-run deviations `t_{r,k} - t*_k`.

All outputs are descriptive-only; no threshold-based “world quality” claims.

---

## 4. Do-or-die acceptance (frozen)

PASS if all:
- K>=1
- Cross-seed consistency holds for k<=K: `std(p_{r,k}) <= 0.05`
- No epoch shorter than `min_epoch_len=200` for consensus boundaries (fail-closed)

FAIL otherwise.

Stop rule:
- If FAIL: do not adjust boundaries; tool exits.

---

## 5. Completion anchors (append-only)

- artifacts_dir:
- analysis_tool:
- inputs_trial8_artifacts_dir:
- output_files:
- verdict:


---

## 6. Completion record (append-only)

- inputs_trial8_artifacts_dir: `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/`
- analysis_tool: `tools/v12/build_epoch_candidates_from_changepoints_v0.py`
- artifacts_dir: `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/`
- output_files:
  - `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/epoch_candidates.json`
  - `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/per_run_epoch_stats.json`
  - `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/consensus_epoch_stats_by_run.json`
  - `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/trial9_epoch_annotation_report.md`
- verdict: **PASS**
