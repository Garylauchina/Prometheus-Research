# Delivery — Quant Instructions — Trial-4 World-Conditioned Impedance (E→M coupling) — 2026-01-09

Audience: Programmer AI (Quant repo).  
Repo: `/Users/liugang/Cursor_Store/Prometheus-Quant`

Goal:
- Make mock/probe impedance depend monotonically on world volatility proxy from `last_px`
- Rerun the grouped protocol on Dataset A/B (3 seeds × 4 modes) with `probe_attempts_per_tick=1`
- Generate Trial-2 impedance-proxy reachability outputs as usual and return run lists for Research aggregation

Research references (absolute paths):
- Trial-4 pre-reg: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL4_WORLD_CONDITIONED_IMPEDANCE_V0_20260109.md`
- Trial-3 (previous transfer): `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL3_CROSS_DATASET_TRANSFER_V0_20260109.md`

Datasets (absolute paths; confirmed by user):
- Dataset A (BTC 2021–2022): `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m`
- Dataset B (ETH 2024-Q4): `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m`

Frozen sweep settings:
- seeds: `71001 71002 71003`
- modes: `full no_e no_m null`
- steps: `10000`
- probe: `--probe_attempts_per_tick 1`

---

## A) Engineering change (Quant): world-conditioned friction

Target file:
- `tools/v12/run_survival_space_em_v1.py`

Add CLI args (with defaults frozen as Trial-4 v0):
- `--world_conditioned_impedance` (0/1, default 0)
- `--world_r_cap` (float, default 0.01)
- `--world_a_http` (float, default 0.02)
- `--world_a_rl` (float, default 0.10)
- `--world_a_rej` (float, default 0.05)
- `--world_a_lat_ms` (float, default 200.0)

Implementation (frozen):
1) Parse `last_px` from each `market_snapshot` tick.
2) Compute `u_t`:
   - `r_t = abs(log(px_t/px_{t-1}))` (t>0), else r_0=0
   - `u_t = min(r_t, r_cap) / r_cap`
3) If `--world_conditioned_impedance 1`, replace the base probabilities used by BOTH:
   - probe attempt outcome generator (PHASE 0)
   - agent attempt outcome generator (PHASE 6)
   with:
   - `p_http_t = clamp(p_http_base + a_http*u_t, 0, 0.20)`
   - `p_rl_t   = clamp(p_rl_base   + a_rl*u_t,   0, 0.80)`
   - `p_rej_t  = clamp(p_rej_base  + a_rej*u_t,  0, 0.80)`
   - and latency add-on: `latency_ms += a_lat_ms*u_t`

Evidence requirement:
- In `interaction_impedance.jsonl`, add (inside `metrics`) fields:
  - `world_r` (the unclamped r_t)
  - `world_u` (u_t)
  - `world_conditioned_impedance` (bool)

Manifest requirement:
- Record these new args into `run_manifest.params` (auditability).

Hard constraints:
- No reward / no learning / no parameter adaptation.
- Probe attempts remain measurement only.

---

## B) Run Trial-4 grouped sweeps (A and B)

### B.1 Dataset A

```bash
DATASET_A=\"/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m\"\n+\n+for SEED in 71001 71002 71003; do\n+  for MODE in full no_e no_m null; do\n+    echo \"==> A seed=$SEED mode=$MODE\"\n+    python3 tools/v12/run_survival_space_em_v1.py \\\n+      --dataset_dir \"$DATASET_A\" \\\n+      --runs_root \"/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool\" \\\n+      --steps 10000 \\\n+      --seed \"$SEED\" \\\n+      --ablation_mode \"$MODE\" \\\n+      --probe_attempts_per_tick 1 \\\n+      --world_conditioned_impedance 1 \\\n+      --world_r_cap 0.01 \\\n+      --world_a_http 0.02 \\\n+      --world_a_rl 0.10 \\\n+      --world_a_rej 0.05 \\\n+      --world_a_lat_ms 200.0 || exit 1\n+\n+    # After each run: generate reachability (Trial-2 lens unchanged)\n+    python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \\\n+      --run_dir \"<NEW_RUN_DIR>\" || exit 1\n+  done\n+done\n+```\n+\n+Write run list:\n+\n+```bash\n+cat > /tmp/local_reachability_trial4_run_dirs_A.txt << 'EOF'\n+<RUN_DIR_1>\n+...\n+EOF\n+```\n+\n+### B.2 Dataset B\n+\n+```bash\n+DATASET_B=\"/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m\"\n+\n+for SEED in 71001 71002 71003; do\n+  for MODE in full no_e no_m null; do\n+    echo \"==> B seed=$SEED mode=$MODE\"\n+    python3 tools/v12/run_survival_space_em_v1.py \\\n+      --dataset_dir \"$DATASET_B\" \\\n+      --runs_root \"/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool\" \\\n+      --steps 10000 \\\n+      --seed \"$SEED\" \\\n+      --ablation_mode \"$MODE\" \\\n+      --probe_attempts_per_tick 1 \\\n+      --world_conditioned_impedance 1 \\\n+      --world_r_cap 0.01 \\\n+      --world_a_http 0.02 \\\n+      --world_a_rl 0.10 \\\n+      --world_a_rej 0.05 \\\n+      --world_a_lat_ms 200.0 || exit 1\n+\n+    python3 /Users/liugang/Cursor_Store/Prometheus-Quant/tools/v12/posthoc_local_reachability_v2_impedance_proxy.py \\\n+      --run_dir \"<NEW_RUN_DIR>\" || exit 1\n+  done\n+done\n+```\n+\n+Write run list:\n+\n+```bash\n+cat > /tmp/local_reachability_trial4_run_dirs_B.txt << 'EOF'\n+<RUN_DIR_1>\n+...\n+EOF\n+```\n+\n+---\n+\n+## C) Return to Research\n+\n+Send back:\n+- Quant commit hash\n+- `/tmp/local_reachability_trial4_run_dirs_A.txt`\n+- `/tmp/local_reachability_trial4_run_dirs_B.txt`\n+\n*** End Patch"} }
