# Delivery — Quant Instructions — Trial-3 Cross-Dataset / Cross-Asset Transfer (2026-01-09)

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Run the Trial-2 M-probe reachability protocol on two new datasets
- Produce grouped reports per dataset (Research side)

Research references (absolute paths):
- Trial-3 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL3_CROSS_DATASET_TRANSFER_V0_20260109.md`
- Grouped aggregator (Research): `/Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_grouped_v0.py`

Frozen runner parameters (do not change without explicit note):
- `--probe_attempts_per_tick 1`
- `--steps 10000`
- seeds: `70001 70002 70003`
- modes: `full no_e no_m null`

---

## A) Dataset A (BTC 2021–2022) — same asset, broader regime

Set:
- `DATASET_A="<ABSOLUTE_PATH_REQUIRED>"`

Run:

```bash
for SEED in 70001 70002 70003; do
  for MODE in full no_e no_m null; do
    echo "==> dataset=A seed=$SEED mode=$MODE"
    python3 tools/v12/run_survival_space_em_v1.py \
      --dataset_dir "$DATASET_A" \
      --runs_root "/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool" \
      --steps 10000 \
      --seed "$SEED" \
      --ablation_mode "$MODE" \
      --probe_attempts_per_tick 1 || exit 1
  done
done
```

For each created `<RUN_DIR>`, generate reachability:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \
  --run_dir "<RUN_DIR>" || exit 1
```

Write run list:

```bash
cat > /tmp/local_reachability_trial3_run_dirs_A.txt << 'EOF'
<RUN_DIR_1>
...
EOF
```

---

## B) Dataset B (ETH 2024-Q4) — cross-asset

Set:
- `DATASET_B="<ABSOLUTE_PATH_REQUIRED>"`

Run:

```bash
for SEED in 70001 70002 70003; do
  for MODE in full no_e no_m null; do
    echo "==> dataset=B seed=$SEED mode=$MODE"
    python3 tools/v12/run_survival_space_em_v1.py \
      --dataset_dir "$DATASET_B" \
      --runs_root "/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool" \
      --steps 10000 \
      --seed "$SEED" \
      --ablation_mode "$MODE" \
      --probe_attempts_per_tick 1 || exit 1
  done
done
```

Generate reachability per run_dir (same as dataset A).

Write run list:

```bash
cat > /tmp/local_reachability_trial3_run_dirs_B.txt << 'EOF'
<RUN_DIR_1>
...
EOF
```

---

## C) Return to Research

Send back:
- `/tmp/local_reachability_trial3_run_dirs_A.txt`
- `/tmp/local_reachability_trial3_run_dirs_B.txt`
- the two dataset absolute paths used

Research will run grouped aggregation:
- `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_grouped_v0.py --run_dirs_file /tmp/local_reachability_trial3_run_dirs_A.txt --output_json /tmp/local_reachability_trial3_grouped_A.json`
- `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_grouped_v0.py --run_dirs_file /tmp/local_reachability_trial3_run_dirs_B.txt --output_json /tmp/local_reachability_trial3_grouped_B.json`

