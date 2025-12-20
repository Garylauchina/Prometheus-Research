# V10 验收裁决摘要（消融补强）：I消融（I_zeroed）100-seed 下 A vs B2 — 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **G2.1（seed规模/统计功效）**，并补强上一轮 `I_zeroed` 的“灭绝率反向信号”裁决。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + I_zeroed, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_zeroed__20251221_030052/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_zeroed, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_zeroed__20251221_032109/multiple_experiments_summary.json`

数值健康（两组均有）：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Primary endpoints（A vs B2，n=100）

### 1.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-3.856%  
- **B2 mean**：-6.242%  
- **A median**：-3.700%  
- **B2 median**：-5.947%  
- **A IQR**：[-4.884%, -2.890%]  
- **B2 IQR**：[-7.179%, -5.155%]

统计检验（两独立样本，双侧）：**Mann–Whitney U**

- U = 8517.0  
- p = 8.534e-18

效应量（Cliff’s delta）：

- δ = 0.7034（A总体优于B2，强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 1.2 Primary #2：extinction_rate

- **A 灭绝率**：78/100 = 78.0%  
- **B2 灭绝率**：63/100 = 63.0%

统计检验（双侧）：**Fisher exact**

- odds = 2.0823  
- p = 0.02949

效应量：

- risk_diff（A-B2）= +15.0pp（A更高）  
- risk_ratio（A/B2）≈ 1.238

**裁决（Primary #2）：FAIL（A显著更易灭绝）**

---

## 2) 结论（这条结论很“硬”）

在 **I消融（I_zeroed）** 条件下：

- 系统仍能在 `system_roi` 上稳定体现 A>B2（时间结构可被利用）
- 但 **A 的灭绝率显著高于 B2**（p≈0.029，+15pp）

一句话解释（人话）：

> I 更像“生存/风险控制感官”。拿掉 I 后，系统仍能利用时间结构改善净值，但在真实时间结构的世界里会更容易“探索过度 → 付出死亡代价”，因此灭绝率反而更高。

---

## 3) 下一步（最小改动优先）

建议分两条线并行讨论（不等于立刻改代码）：

1) **方法论层面**：接受“收益结构”与“生存结构”可能是两条不同的主维度——I 通道可能主要服务生存而非直接提升ROI。
2) **工程验证层面（下一轮实验）**：
   - 做 **I 子集消融**（只保留最小自我状态，例如 capital/position_count，而不是全置空），看是否能降低灭绝率而不抹掉 A>B2 的净值信号。
   - 或做 **窗口迁移**（不同市场阶段）验证“灭绝率反向”是否普适。


