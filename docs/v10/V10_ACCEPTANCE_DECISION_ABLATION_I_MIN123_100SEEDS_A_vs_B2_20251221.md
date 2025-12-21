# V10 验收裁决摘要（I子集消融）：I_min_123（100-seed）下 A vs B2 — 2025-12-21

本文件用于检验 I 子集中的 **I2（持仓方向）** 是否更接近“生存必要信息”。  
I_min_123 定义：保留 I1+I2+I3，I4=0。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + I_min_123, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_123__20251221_043216/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_min_123, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_123__20251221_045439/multiple_experiments_summary.json`

审计字段（两组均有）：

- `ablation=I_min_123`
- `ablation_detail=keep I1+I2+I3; I4=0`
- B2：`null_hypothesis=shuffle_log_returns_rebuild_price`
- 数值健康：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Primary endpoints（A vs B2，n=100）

### 1.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-6.760%  
- **B2 mean**：-9.541%  
- **A median**：-6.185%  
- **B2 median**：-9.501%  
- **A IQR**：[-8.346%, -5.005%]  
- **B2 IQR**：[-10.780%, -8.168%]

统计检验（双侧）：**Mann–Whitney U**

- U = 7928.0  
- p = 8.489e-13

效应量（Cliff’s delta）：

- δ = 0.5856（A总体优于B2，中等偏强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 1.2 Primary #2：extinction_rate

- **A 灭绝率**：62/100 = 62.0%  
- **B2 灭绝率**：61/100 = 61.0%

统计检验（双侧）：**Fisher exact**

- odds = 1.0431  
- p = 1.0

效应量：

- risk_diff（A-B2）= +1.0pp

**裁决（Primary #2）：FAIL（差异不显著）**

---

## 2) 结论（针对 I2 的启示）

- 加回 I2（方向）并没有让“真实市场更易灭绝”这个代价消失：A 仍略高于 B2（但不显著）。
- 同时 `system_roi` 的 A>B2 依旧稳定成立。

一句话解释（人话）：

> I2（方向）不像是“关键生存必要项”，至少在当前配置下，它没有明显改善 A 的灭绝率。


