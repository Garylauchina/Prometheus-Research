# Delivery — Quant Instructions — Trial-2 Negative Control (probe OFF) — 2026-01-09

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Run one “old world” run with `probe_attempts_per_tick=0`
- Confirm Trial-2 posthoc impedance-proxy generator **fails closed** (expected)

Research references (absolute paths):
- Pre-reg (neg control): `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_PROBE_OFF_NEG_CONTROL_V0_20260109.md`
- Trial-2 posthoc tool (Quant): `tools/v12/posthoc_local_reachability_v2_impedance_proxy.py`

---

## A) Run one Quant modeling-tool run (probe OFF)

```bash
python3 tools/v12/run_survival_space_em_v1.py \
  --dataset_dir "/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m" \
  --runs_root "/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool" \
  --steps 10000 \
  --seed 61001 \
  --ablation_mode full \
  --probe_attempts_per_tick 0
```

Record the produced `<RUN_DIR>` (absolute path).

---

## B) Show impedance is NOT_MEASURABLE exists

```bash
grep -n \"\\\"verdict\\\": \\\"NOT_MEASURABLE\\\"\" \"<RUN_DIR>/interaction_impedance.jsonl\" | head -n 3
```

---

## C) Attempt to generate Trial-2 reachability (must FAIL)

```bash
python3 tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \
  --run_dir \"<RUN_DIR>\" \
  > /tmp/trial2_probe_off_posthoc_stdout.txt \
  2> /tmp/trial2_probe_off_posthoc_stderr.txt

echo \"exit_code=$?\"
```

Expected:
- exit_code != 0
- stderr indicates impedance not PASS / attempts<1

---

## D) Return to Research

Send back:
- `<RUN_DIR>` absolute path
- runner command
- the three grep lines showing NOT_MEASURABLE
- `/tmp/trial2_probe_off_posthoc_stdout.txt`
- `/tmp/trial2_probe_off_posthoc_stderr.txt`
- the printed `exit_code`

