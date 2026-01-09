# Delivery — Quant Instructions — Local Reachability Trial-2 Seed Sweep (2026-01-09)

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Run a small seed sweep with `probe_attempts_per_tick=1`
- Produce multiple run_dirs and ensure each contains Trial-2 `local_reachability.jsonl`
- Return a run_dirs list file for Research aggregation

Research references (absolute paths):
- Trial-2 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- Trial-2 seed sweep pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V0_20260109.md`
- Trial-2 delivery: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_EXEC_20260109.md`

---

## A) Choose seeds (small sweep)

Use 3–10 seeds. Example (3 seeds):

- 60001 (already done)
- 60002
- 60003

---

## B) Run Quant runner with probe enabled

For each seed:

```bash
python3 tools/v12/run_survival_space_em_v1.py \
  --dataset_dir "/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m" \
  --runs_root "/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool" \
  --steps 10000 \
  --seed <SEED> \
  --ablation_mode full \
  --probe_attempts_per_tick 1
```

---

## C) Generate Trial-2 local_reachability.jsonl

For each produced `<RUN_DIR>`:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \
  --run_dir "<RUN_DIR>"
```

Sanity:
- `interaction_impedance.jsonl` should be `PASS` per tick (and `order_attempts_count>=1`).

---

## D) Return run list to Research

Create:

```bash
cat > /tmp/local_reachability_trial2_run_dirs.txt << 'EOF'
<RUN_DIR_1>
<RUN_DIR_2>
<RUN_DIR_3>
EOF
```

Send back:
- `/tmp/local_reachability_trial2_run_dirs.txt`

Research will run aggregation (no need for you to run):
- `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_v0.py --run_dirs_file /tmp/local_reachability_trial2_run_dirs.txt --output_json /tmp/local_reachability_trial2_seed_sweep_report.json`

