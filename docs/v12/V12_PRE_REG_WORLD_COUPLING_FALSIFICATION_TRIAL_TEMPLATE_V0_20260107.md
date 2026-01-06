# V12 Pre-registration template — world-coupling falsification trial v0 — 2026-01-07

Fill this template **before running**. Do not edit after the run (additive-only append is allowed).

---

## 0) Trial identity

- trial_id:
- owner:
- date_utc:
- repo_commit_quant:
- repo_commit_research:

---

## 1) World input (frozen for this trial)

- dataset_dir:
- dataset_id:
- inst_id:
- tick_interval_ms:
- segment/window description:

### 1.1 W0 gate parameters + result

Command:
- `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000 --output <W0_REPORT.json>`

Result:
- W0 verdict:
- W0 report path:

---

## 2) World signal (frozen)

- signal_name:
- formula:
- window(s)/params:
- missing-data rules:

Normalization anchor (must be shared across ON/OFF/SHUFFLE):
- signal_p99_anchor source: (dataset-level / precomputed / constant)
- signal_p99_anchor value:

---

## 3) Pressure mapping (frozen; NO reward)

- energy_update_type: action_cost / impedance_cost
- base_cost distribution:
- coupling_cost distribution:
- mapping formula from signal → g → cost:
- clamps (if any):
- strict ban: positive energy update (confirm):

---

## 4) Projection definition (frozen)

- projection_kind: binary A/B / continuous / other
- strategy (must be simple & auditable, no “learning” in this trial):
- what is being adjudicated:

---

## 5) Controls (must run)

- ON:
- OFF (ablation):
- SHUFFLE (negative control; deterministic permutation):
  - shuffle_seed:
  - shuffle algorithm:

---

## 6) Primary metric + falsification criteria (frozen)

Primary metric name:
- M:

Alignment effect:
- alignment_effect = M(ON) - M(SHUFFLE)
- rule for “ON distinguishable from SHUFFLE”:

Binary projection gap (if applicable):
- G definition:
- rule for “gap reduced under SHUFFLE”:

Failure conditions mapping to D0:
- triggers F1 when:
- triggers F2 when:
- triggers F3 when:

---

## 7) Run plan (frozen)

- seeds:
- steps_target:
- early_stop:
- expected run_dirs naming:

---

## 8) Post-run evidence anchors (fill after completion; do not change above)

- runs_root:
- run_ids (ON):
- run_ids (OFF):
- run_ids (SHUFFLE):
- summary_json_path:


