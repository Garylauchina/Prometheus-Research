# V12 Local Reachability Trial-4 — World-Conditioned Impedance — Completion Report

**Date**: 2026-01-09 17:24 UTC+8
**Status**: ✅ COMPLETE (24/24 runs successful)

---

## 📋 OBJECTIVE

**Goal**: Fix Trial-3 "cross-dataset perfect consistency" issue by making mock/probe impedance depend monotonically on world volatility

**Key Innovation**: E→M coupling via world volatility proxy

---

## 🔧 ENGINEERING CHANGES

### Quant Commit
**Hash**: `e0e177fa6dc4cba12c82175ffda5d044c7c5c23c`

**Modified File**: `tools/v12/run_survival_space_em_v1.py`

### Implementation Details

#### 1. CLI Parameters (with frozen defaults)
```python
--world_conditioned_impedance 1  # Enable world coupling
--world_r_cap 0.01               # Volatility normalization cap
--world_a_http 0.02              # HTTP error coupling coefficient
--world_a_rl 0.10                # Rate-limiting coupling coefficient  
--world_a_rej 0.05               # Rejection coupling coefficient
--world_a_lat_ms 200.0           # Latency add-on coefficient
```

#### 2. World Volatility Proxy
```python
# Per tick:
r_t = abs(log(px_t / px_{t-1}))  # Volatility (unclamped)
u_t = min(r_t, r_cap) / r_cap    # Normalized [0, 1]
```

#### 3. Conditioned Probabilities
```python
# Applied to BOTH probe and agent attempts:
p_http_t = clamp(p_http_base + a_http * u_t, 0, 0.20)
p_rl_t   = clamp(p_rl_base + a_rl * u_t, 0, 0.80)
p_rej_t  = clamp(p_rej_base + a_rej * u_t, 0, 0.80)
latency += a_lat_ms * u_t
```

#### 4. Evidence Fields
Added to `interaction_impedance.jsonl.metrics`:
- `world_r`: Unclamped volatility proxy
- `world_u`: Normalized volatility [0, 1]
- `world_conditioned_impedance`: Boolean flag

#### 5. Manifest Recording
All world parameters recorded in `run_manifest.params` for auditability

---

## 📊 EXECUTION SUMMARY

### Dataset A: BTC 2021-2022
**Path**:
```
/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_BTC-USDT-SWAP_2021-01-01__2022-12-31_bar1m
```

**Runs**: 12 (3 seeds × 4 modes)
**Seeds**: 71001, 71002, 71003
**Status**: ✅ 12/12 successful

---

### Dataset B: ETH 2024-Q4
**Path**:
```
/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_SWAP_ETH-USDT-SWAP_2024-10-01__2024-12-31_bar1m
```

**Runs**: 12 (3 seeds × 4 modes)
**Seeds**: 71001, 71002, 71003
**Status**: ✅ 12/12 successful

---

## 📦 DELIVERABLES

### For Research

**Dataset A Run List**:
```
/tmp/local_reachability_trial4_run_dirs_A.txt
```

**Dataset B Run List**:
```
/tmp/local_reachability_trial4_run_dirs_B.txt
```

**Quant Commit Hash**:
```
e0e177fa6dc4cba12c82175ffda5d044c7c5c23c
```

### Generated Files (per run_dir)
Each of 24 run_dirs contains:
- `interaction_impedance.jsonl` (10,000 lines, with world evidence)
- `local_reachability.jsonl` (10,000 lines, Trial-2 impedance proxy)

**Total Output**: 240,000 local_reachability records (24 runs × 10,000 lines)

---

## 🔬 KEY DIFFERENCE FROM TRIAL-3

### Trial-3 (No World Coupling)
- Impedance was deterministic per seed
- BTC and ETH had identical impedance patterns
- Problem: Unrealistic "perfect consistency" across datasets

### Trial-4 (World-Conditioned)
- Impedance now depends on market volatility (r_t)
- BTC 2021-2022 (high volatility) → higher impedance
- ETH 2024-Q4 (different volatility) → different impedance pattern
- Expected: Reachability patterns now vary realistically across datasets

---

## ✅ COMPLETION STATUS

### Engineering
- ✅ World volatility proxy implemented
- ✅ E→M coupling working
- ✅ Probe and agent attempts both conditioned
- ✅ Evidence fields added
- ✅ Manifest recording complete
- ✅ Backward compatible (default: off)

### Execution
- ✅ Dataset A: 12/12 runs successful
- ✅ Dataset B: 12/12 runs successful
- ✅ Total: 24/24 (100%)

### Posthoc Processing
- ✅ All 24 local_reachability.jsonl generated
- ✅ All runs verified

---

## 🎯 EXPECTED RESEARCH FINDINGS

### Hypothesis
World-conditioned impedance should:
1. Break the "perfect consistency" artifact from Trial-3
2. Show impedance variation correlated with market volatility
3. Maintain interpretability (still based on observable M metrics)

### Next Steps (Research Side)
1. Compare Trial-3 vs Trial-4 reachability distributions
2. Verify impedance correlates with volatility (world_r in evidence)
3. Check if BTC vs ETH now show realistic differences

---

**Status**: COMPLETE & READY FOR RESEARCH COMPARISON

---

**Generated**: 2026-01-09 17:24 UTC+8
**Programmer**: AI (Quant)
**Commit**: e0e177fa6dc4cba12c82175ffda5d044c7c5c23c

