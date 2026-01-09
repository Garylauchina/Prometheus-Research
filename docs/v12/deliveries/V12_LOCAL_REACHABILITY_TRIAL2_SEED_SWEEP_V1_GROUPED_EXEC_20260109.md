# Delivery — Quant Instructions — Local Reachability Trial-2 Seed Sweep v1 (grouped by mode) — 2026-01-09

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- For each seed, run 4 ablation modes: `full`, `no_e`, `no_m`, `null`
- Keep probe contract frozen: `--probe_attempts_per_tick 1`
- Generate Trial-2 impedance-proxy `local_reachability.jsonl` for each run_dir
- Return a single run_dirs file for Research grouped aggregation

Research references (absolute paths):
- Trial-2 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_IMPEDANCE_PROBE_V0_20260109.md`
- Seed sweep v1 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL2_SEED_SWEEP_V1_GROUPED_V0_20260109.md`

---

## A) Choose seeds

Recommended: 10 seeds (example):

`60001 60002 60003 60004 60005 60006 60007 60008 60009 60010`

---

## B) Run Quant runner (4 modes × seeds)

Dataset (frozen for this sweep):
- `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m`

For each seed and mode:

```bash
for SEED in 60001 60002 60003 60004 60005 60006 60007 60008 60009 60010; do
  for MODE in full no_e no_m null; do
    echo "==> seed=$SEED mode=$MODE"
    python3 tools/v12/run_survival_space_em_v1.py \
      --dataset_dir "/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2022-10-01__2022-12-31_bar1m" \
      --runs_root "/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool" \
      --steps 10000 \
      --seed "$SEED" \
      --ablation_mode "$MODE" \
      --probe_attempts_per_tick 1 || exit 1
  done
done
```

---

## C) Generate Trial-2 local_reachability.jsonl (for each run_dir)

After each run, locate the newly created `<RUN_DIR>` and run:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \
  --run_dir "<RUN_DIR>" || exit 1
```

---

## D) Return run list for Research grouped aggregation

Create:

```bash
cat > /tmp/local_reachability_trial2_v1_grouped_run_dirs.txt << 'EOF'
<RUN_DIR_1>
<RUN_DIR_2>
...
EOF
```

Send back:
- `/tmp/local_reachability_trial2_v1_grouped_run_dirs.txt`

Research will run aggregation:
- `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_grouped_v0.py --run_dirs_file /tmp/local_reachability_trial2_v1_grouped_run_dirs.txt --output_json /tmp/local_reachability_trial2_v1_grouped_report.json`

