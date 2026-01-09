# Trial-2 Engineering Patch — Record probe_attempts_per_tick in run_manifest (2026-01-09)

Purpose: close the audit gap where `probe_attempts_per_tick` was missing (null) in `run_manifest.params` for grouped aggregation.

## Quant implementation anchor

- Quant commit hash: `3eab4bb7709ea62ce9f5f73294c2e07b1b16b9a4`

## Example run_dir anchor (absolute)

- `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260109T072231Z_seed99001_full`

Verified facts (read from run_manifest.json):
- `params.probe_attempts_per_tick = 1`
- `steps = 100`
- `ablation.survival_space.mode = full`

Verified facts (read from order_attempts.jsonl):
- Probe attempts are tagged: `attempt_kind="probe"`

## Delivery doc (Research)

- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_TRIAL2_ENGINEERING_PATCH_RECORD_PROBE_IN_MANIFEST_20260109.md`

