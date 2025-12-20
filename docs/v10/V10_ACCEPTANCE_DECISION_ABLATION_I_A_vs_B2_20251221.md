# V10 验收裁决摘要（消融）：I 消融（I={}/置零）下 A vs B2 — 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **G0.6 / G3.3（Prior leakage）**。  
目标：验证此前 A>B2 的 `system_roi` 差异是否依赖 **I 通道**（Agent自我状态/内部资源信息）——若依赖，应在 I 消融后显著退化或消失。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + I_zeroed）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_30__ablation_I_zeroed__20251221_024802/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_zeroed）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_30__ablation_I_zeroed__20251221_024802/multiple_experiments_summary.json`

审计声明关键字段（两组均有）：

- `ablation=I_zeroed`
- `ablation_detail=I={}`
- B2：`null_hypothesis=shuffle_log_returns_rebuild_price`
- 数值健康：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Gate 0：培养皿检查（硬门槛）

- **G0.3 数值健康**：**PASS**（无 NaN/Inf/爆炸）
- **G0.5 对照物理合理**：**PASS**（B2为“打乱log-return后重建价格”，非直接乱序价格）
- **G0.6 Prior leakage audit**：**PASS**（本轮消融明确且落盘：I={})

---

## 2) Gate 1：非随机性（Primary endpoints，A vs B2）

样本量：A n=30，B2 n=30（按 run 计）

### 2.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-3.877%  
- **B2 mean**：-5.954%  
- **A median**：-3.947%  
- **B2 median**：-5.817%  
- **A IQR**：[-4.676%, -2.815%]  
- **B2 IQR**：[-6.759%, -5.168%]

统计检验（两独立样本，双侧）：**Mann–Whitney U**

- U = 796.0  
- p = 3.256e-07

效应量（Cliff’s delta）：

- δ = 0.7689（A总体优于B2，强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 2.2 Primary #2：extinction_rate

- **A 灭绝率**：24/30 = 80.00%  
- **B2 灭绝率**：18/30 = 60.00%

统计检验（双侧）：**Fisher exact**

- odds = 2.6667  
- p = 0.1581

效应量：

- risk_diff（A-B2）= +20.00pp（A更高）  
- risk_ratio（A/B2）≈ 1.333

**裁决（Primary #2）：FAIL（差异未达显著；但方向对A不利）**

---

## 3) Gate 3：Prior leakage 消融裁决（核心结论）

对照基线裁决记录：

- `docs/v10/V10_ACCEPTANCE_DECISION_A_vs_B2_20251221.md`

**结论：通过（对“时间结构优势主要靠 I 通道先验”的担忧降低；但出现“生存性反向信号”）**

一句话解释（人话）：

- 把 I 拿掉后，`system_roi` 上 A 仍显著优于 B2，说明 A>B2 的净值优势**不依赖 I 通道**；但灭绝率在本轮出现 A 更高（虽然未达显著），提示 I 可能更像“生存/风险控制感官”，拿掉后系统更容易灭绝。

---

## 4) 下一步建议（最小改动优先）

1) **补统计功效（针对灭绝率）**：把 seeds 提升到 100（或至少 60），专门检验“灭绝率反向”是否稳定。  
2) **窗口迁移（Gate 2.3）**：换一个不重叠时间窗，验证 `system_roi` 的 A>B2 是否仍成立。  
3) **解释路径**：如果“净值优势存在，但生存性变差”反复出现，可以把它视为方法论的一个真实特征：时间结构可被利用，但需要 I 感官来控制探索成本。


