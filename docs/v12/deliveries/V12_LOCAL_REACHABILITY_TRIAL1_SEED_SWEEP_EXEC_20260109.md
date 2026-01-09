# Delivery — Quant Instructions — Local Reachability Trial-1 Seed Sweep (2026-01-09)

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Run Trial-1 tool on multiple run_dirs (seed sweep)
- Return a file listing run_dirs (absolute paths) so Research can batch-summarize

Research references (absolute paths):
- Trial-1 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL1_VOLATILITY_PROXY_V0_20260109.md`
- Seed sweep pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL1_SEED_SWEEP_V0_20260109.md`
- Trial-1 delivery: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_LOCAL_REACHABILITY_TRIAL1_VOLATILITY_PROXY_EXEC_20260109.md`

---

## A) Prepare run list (edit if needed)

Create a text file of run_dirs (absolute paths):

```bash
cat > /tmp/local_reachability_trial1_run_dirs.txt << 'EOF'
/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T185657Z_seed50099_no_e
/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T153332Z_seed10001_full
/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_tool_model_survival_space_em_v1_20260108T153336Z_seed10002_full
EOF
```

Note:
- If some run_dir does not exist locally, remove it (do not fabricate).

---

## B) Run Trial-1 tool for each run_dir

```bash
while IFS= read -r RUN_DIR; do
  echo \"==> $RUN_DIR\"
  python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v1_volatility_proxy.py \\
    --run_dir \"$RUN_DIR\" || exit 1
done < /tmp/local_reachability_trial1_run_dirs.txt
```

---

## C) Return to Research side

Send back:
- `/tmp/local_reachability_trial1_run_dirs.txt`

Then Research will run (no need for you to run):
- `python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v12/summarize_local_reachability_multi_run_v0.py --run_dirs_file /tmp/local_reachability_trial1_run_dirs.txt --output_json /tmp/local_reachability_trial1_seed_sweep_report.json`

