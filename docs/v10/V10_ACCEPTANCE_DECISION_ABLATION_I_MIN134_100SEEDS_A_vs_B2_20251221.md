# V10 验收裁决摘要（I子集消融）：I_min_134（100-seed）下 A vs B2 — 2025-12-21

本文件用于检验 I 子集中的 **I4（last_signal）** 是否更接近“生存必要信息”。  
I_min_134 定义：保留 I1+I3+I4，I2=0。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + I_min_134, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__20251221_051404/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_min_134, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__20251221_053600/multiple_experiments_summary.json`

审计字段（两组均有）：

- `ablation=I_min_134`
- `ablation_detail=keep I1+I3+I4; I2=0`
- B2：`null_hypothesis=shuffle_log_returns_rebuild_price`
- 数值健康：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Primary endpoints（A vs B2，n=100）

### 1.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-5.902%  
- **B2 mean**：-9.349%  
- **A median**：-5.674%  
- **B2 median**：-8.913%  
- **A IQR**：[-7.409%, -3.384%]  
- **B2 IQR**：[-10.698%, -7.748%]

统计检验（双侧）：**Mann–Whitney U**

- U = 8245.0  
- p = 2.235e-15

效应量（Cliff’s delta）：

- δ = 0.6490（A总体优于B2，强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 1.2 Primary #2：extinction_rate

- **A 灭绝率**：56/100 = 56.0%  
- **B2 灭绝率**：51/100 = 51.0%

统计检验（双侧）：**Fisher exact**

- odds = 1.2228  
- p = 0.5708

效应量：

- risk_diff（A-B2）= +5.0pp

**裁决（Primary #2）：FAIL（差异不显著）**

---

## 2) 结论（针对 I4 的启示）

- I4（last_signal）相比 I2（方向）看起来更有帮助：A 的灭绝率更低（56% vs I_min_123 的62%），且净值也更好（-5.90% vs -6.76%）。
- 但“真实市场更易灭绝”在统计上仍未被彻底消除（A仍略高于B2，未显著）。

一句话解释（人话）：

> I4（last_signal）更像“自我刹车记忆”，可能更接近生存必要信息；但要把灭绝率彻底拉平，还需要继续精刻或改用更强的稳定性机制。


