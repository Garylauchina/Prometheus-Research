# V10 验收裁决摘要（消融）：E子集（仅OHLCV）下 A vs B2 — 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **G0.6 / G3.3（Prior leakage）**。  
目标：验证此前 A>B2 的 `system_roi` 差异是否依赖 **E维度中“盘口/价差/24h”等可能为近似构造的数据**。因此本轮只保留 OHLCV（E1–E5），移除 E6–E12 与可选 E13–E15。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + E_ob_only）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_30__ablation_E_ob_only__20251221_023035/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + E_ob_only）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_30__ablation_E_ob_only__20251221_023035/multiple_experiments_summary.json`

审计声明关键字段（两组均有）：

- `ablation=E_ob_only`
- `ablation_detail=keep E1-E5; drop E6-E12 and optional E13-E15`
- B2：`null_hypothesis=shuffle_log_returns_rebuild_price`
- 数值健康：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Gate 0：培养皿检查（硬门槛）

- **G0.3 数值健康**：**PASS**（无 NaN/Inf/爆炸）
- **G0.5 对照物理合理**：**PASS**（B2为“打乱log-return后重建价格”，非直接乱序价格）
- **G0.6 Prior leakage audit**：**PASS**（本轮消融明确且落盘：仅保留E1–E5）

---

## 2) Gate 1：非随机性（Primary endpoints，A vs B2）

样本量：A n=30，B2 n=30（按 run 计）

### 2.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-6.726%  
- **B2 mean**：-10.015%  
- **A median**：-5.211%  
- **B2 median**：-9.475%  
- **A IQR**：[-8.471%, -4.246%]  
- **B2 IQR**：[-11.143%, -8.045%]

统计检验（两独立样本，双侧）：**Mann–Whitney U**

- U = 720.0  
- p = 6.765e-05

效应量（Cliff’s delta）：

- δ = 0.6000（A总体优于B2，中等偏强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 2.2 Primary #2：extinction_rate

- **A 灭绝率**：16/30 = 53.33%  
- **B2 灭绝率**：21/30 = 70.00%

统计检验（双侧）：**Fisher exact**

- odds = 0.4898  
- p = 0.2882

效应量：

- risk_diff（A-B2）= -16.67pp  
- risk_ratio（A/B2）≈ 0.762

**裁决（Primary #2）：FAIL（差异未达显著；但方向对A有利）**

---

## 3) Gate 3：Prior leakage 消融裁决（核心结论）

对照基线裁决记录：

- `docs/v10/V10_ACCEPTANCE_DECISION_A_vs_B2_20251221.md`

**结论：通过（对“E维度里盘口/价差/24h近似构造导致假阳性”的担忧显著降低）**

一句话解释（人话）：

- 只给 OHLCV（不喂任何“近似盘口/价差/24h”相关的 E 分量）后，A 依旧显著优于 B2，说明 A>B2 的核心信号**不依赖这些潜在近似数据**。

---

## 4) 下一步建议（最小改动优先）

- **I消融（I={}/置零）**：继续缩小“时间结构优势来自哪里”的证据范围（E/I/M/C里只剩I未排雷）。
- **窗口迁移（Gate 2.3）**：至少换一个不重叠时间窗，验证 A>B2 的方向一致。
- **扩大 seeds**：灭绝率目前方向对A有利但不显著，增加样本量能提升统计功效。


