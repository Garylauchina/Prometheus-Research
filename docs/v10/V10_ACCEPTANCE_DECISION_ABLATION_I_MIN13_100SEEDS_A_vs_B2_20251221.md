# V10 验收裁决摘要（I子集消融）：I_min_13（100-seed）下 A vs B2 — 2025-12-21

本文件用于检验 “I 是生存稳定器，但可能压制探索” 的工程假设：  
通过 **只保留最小自我信息**（I1=是否持仓、I3=状态机状态；I2/I4置零），观察能否在不抹掉时间结构信号（A>B2 的 `system_roi`）的前提下，降低 “真实市场更易灭绝” 的代价。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + I_min_13, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_13__20251221_034435/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_min_13, n=100）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_13__20251221_040806/multiple_experiments_summary.json`

审计字段（两组均有）：

- `ablation=I_min_13`
- `ablation_detail=keep I1_has_position + I3_state_machine_state; I2/I4=0`
- B2：`null_hypothesis=shuffle_log_returns_rebuild_price`
- 数值健康：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Primary endpoints（A vs B2，n=100）

### 1.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-5.552%  
- **B2 mean**：-8.226%  
- **A median**：-5.310%  
- **B2 median**：-8.511%  
- **A IQR**：[-6.957%, -3.614%]  
- **B2 IQR**：[-9.587%, -7.338%]

统计检验（双侧）：**Mann–Whitney U**

- U = 8298.0  
- p = 7.814e-16

效应量（Cliff’s delta）：

- δ = 0.6596（A总体优于B2，强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 1.2 Primary #2：extinction_rate

- **A 灭绝率**：59/100 = 59.0%  
- **B2 灭绝率**：48/100 = 48.0%

统计检验（双侧）：**Fisher exact**

- odds = 1.5589  
- p = 0.1561

效应量：

- risk_diff（A-B2）= +11.0pp（A更高）  
- risk_ratio（A/B2）≈ 1.229

**裁决（Primary #2）：FAIL（差异未达显著；方向对A不利）**

---

## 2) 与 I_zeroed（100-seed）的对比：I_min_13 是否改善“生存代价”？

对照文件：

- `docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_I_100SEEDS_A_vs_B2_20251221.md`

关键对比（只用 A_real 作为参照）：

- **A_real 灭绝率**：I_zeroed 78% → I_min_13 59%（显著改善，减少 19pp）
- **A_real system_roi**：I_zeroed -3.856% → I_min_13 -5.552%（净值更差，代价上升）

一句话解释（人话）：

> I 的“最小自我信息”确实能明显降低灭绝，但也会牺牲一部分净值表现；它像一个真正的稳定器，而不是纯粹的策略偏置。

---

## 3) 结论与下一步

### 3.1 结论（当前证据）

- **时间结构利用能力（system_roi 的 A>B2）**：仍然强且稳定（PASS）
- **真实市场生存代价（A 的灭绝率更高）**：方向仍对A不利，但在 I_min_13 下未达显著（p=0.156）
- **I_min_13 的作用**：对 A_real 的灭绝率有明显改善（78%→59%），但牺牲了部分净值（-3.86%→-5.55%）

### 3.2 下一步建议（最小改动优先）

1) 若目标是“找到最小必要 I”：
   - 继续做 **I_min_123**（加回 I2=方向）与 **I_min_134**（加回 I4=last_signal）两组对比，判断哪个更像“生存必要信息”。
2) 若目标是“稳定地同时优化两条轴”：
   - 把 `system_roi` 与 `extinction_rate` 明确作为双目标，开始做“代价曲线”（不同 I 子集对应一组点）。


