# V12 Pre-reg — Local Reachability — Trial-3 Cross-Dataset / Cross-Asset Transfer (v0, 2026-01-09)

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- Trial-2 grouped sweep (baseline within BTC 2022-Q4): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V1_GROUPED_V0_20260109.md`
- Trial-2 pre-reg (impedance probe): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`

---

## 0. Purpose (frozen)

We test whether the Trial-2 M-probe local reachability lens **transfers** beyond the current dataset.

We run the same protocol (probe-on, same mapping) on:

1) **BTC 2021–2022 (same asset, broader regime)**
2) **ETH 2024-Q4 (cross-asset, same length as BTC-Q4)**

We do NOT claim “agent is better”. We only measure the reachability readout distribution and its stability.

Hard boundaries (frozen):
- measurement only
- no rollout / planning / search
- no reward / PnL
- death label disabled
- probe attempts are measurement only (must not affect survival/reward/gate)

---

## 1. Frozen inputs

We will run the Quant runner (`run_survival_space_em_v1.py`) with:

- `probe_attempts_per_tick = 1` (frozen)
- steps = 10000 (recommended; operator may increase but must record)
- seeds = 3 (minimum) for each dataset (frozen in the execution doc)
- modes = `full`, `no_e`, `no_m`, `null` (frozen; 4-way grouped)

Datasets (absolute paths; to be filled at completion anchors):

- dataset_A (BTC 2021–2022): `<ABSOLUTE_PATH_REQUIRED>`
- dataset_B (ETH 2024-Q4): `<ABSOLUTE_PATH_REQUIRED>`

---

## 2. Frozen outputs

For each run_dir:
- Quant produces evidence (standard):
  - `run_manifest.json`
  - `interaction_impedance.jsonl` (must be PASS per tick due to probe)
  - `decision_trace.jsonl`
- Posthoc generates:
  - `local_reachability.jsonl` (Trial-2 impedance proxy; reason_codes must include `reachability_proxy:impedance_exp`)

Research aggregation (grouped, descriptive only):
- Use tool: `python3 tools/v12/summarize_local_reachability_multi_run_grouped_v0.py`
- Output JSON per dataset bundle.

---

## 3. Frozen evaluation (descriptive)

For each dataset bundle, compute grouped distributions:

- per-run mean feasible_ratio per mode (full/no_e/no_m/null)

We compare:
- whether grouped structure exists and is non-trivial
- whether the ordering/spacing between mode groups is preserved

No threshold-based “success” is asserted; we are collecting transferable structure evidence.

---

## 4. Falsification / stop conditions (frozen)

We reject “transfer” for this lens if any triggers on a dataset bundle:

- **Input drift**: dataset path / probe contract / mapping differs from frozen settings without explicit declaration.
- **Probe drift**: evidence indicates probe attempts affect survival/reward/gate semantics (hard failure).
- **Group collapse**: all 4 mode groups collapse to near-identical per-run mean feasible_ratio (loss of structure).

Stop rule:
- If any hard failure triggers ⇒ stop (no patching within this claim).

---

## 5. Completion anchors (append-only)

### 5.1 Dataset anchors

- dataset_A_path:
- dataset_B_path:

### 5.2 Run anchors

- run_dirs_file_A:
- grouped_report_json_A:
- run_dirs_file_B:
- grouped_report_json_B:

### 5.3 Notes

- notes:


## 6. Completion record (appended, 2026-01-09)

### 6.1 Dataset anchors

- dataset_A_path: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`
- dataset_B_path: `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`

### 6.2 Run anchors (archived)

- artifact_root: `docs/v12/artifacts/local_reachability/trial3_cross_dataset_transfer_v0_20260109/`
- run_dirs_file_A: `docs/v12/artifacts/local_reachability/trial3_cross_dataset_transfer_v0_20260109/run_dirs_A.txt`
- grouped_report_json_A: `docs/v12/artifacts/local_reachability/trial3_cross_dataset_transfer_v0_20260109/grouped_A.json`
- run_dirs_file_B: `docs/v12/artifacts/local_reachability/trial3_cross_dataset_transfer_v0_20260109/run_dirs_B.txt`
- grouped_report_json_B: `docs/v12/artifacts/local_reachability/trial3_cross_dataset_transfer_v0_20260109/grouped_B.json`

### 6.3 Observed summary (descriptive)

Dataset A (BTC 2021–2022), per-run mean feasible_ratio:
- full (n=3): mean=0.678737037037037
- no_m (n=3): mean=0.678737037037037
- no_e (n=3): mean=0.6502
- null (n=3): mean=0.647662962962963

Dataset B (ETH 2024-Q4), per-run mean feasible_ratio:
- full (n=3): mean=0.678737037037037
- no_m (n=3): mean=0.678737037037037
- no_e (n=3): mean=0.6502
- null (n=3): mean=0.647662962962963

Notes:
- Both dataset bundles have `failures=[]` in grouped reports.
- The grouped summaries for dataset A and dataset B are numerically identical under this protocol.
