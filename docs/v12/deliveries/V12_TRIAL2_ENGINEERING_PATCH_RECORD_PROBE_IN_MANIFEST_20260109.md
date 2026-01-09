# Delivery — Quant Engineering Patch — Record probe_attempts_per_tick in run_manifest (2026-01-09)

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Improve auditability: record `probe_attempts_per_tick` into `run_manifest.params`
- Do **not** change semantics of the runner

Background:
- Probe attempts are already tagged in `order_attempts.jsonl` with `attempt_kind=\"probe\"`.
- Research aggregation currently reads `run_manifest.params.probe_attempts_per_tick`, but this field is missing (null) in existing runs.

---

## Target file

- `tools/v12/run_survival_space_em_v1.py`

---

## Required changes

### 1) Add CLI arg

In `parse_args()` add:

- `--probe_attempts_per_tick` (int, default 0)

### 2) Record into run_manifest.params

When building `manifest[\"params\"]`, add:

- `\"probe_attempts_per_tick\": int(args.probe_attempts_per_tick)`

### 3) Include it in the printed “Rerun” command

Append:

- `--probe_attempts_per_tick {args.probe_attempts_per_tick}`

---

## Acceptance check (local)

Run one short job and confirm `run_manifest.json` contains:

- `.params.probe_attempts_per_tick` equal to the CLI value

