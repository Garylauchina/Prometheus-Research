# V10 B阶段机制归因裁决（Agent级证据链）— W2 + I_min_134（A vs B2）— 2025-12-21

本裁决基于**Agent级落盘证据链**（`behaviors_run_*.json` ↔ `genomes_run_*.npy` 对齐），用于回答：  
**A（真实时间结构）为什么在 W2 窗口里比 B2（打乱时间结构）更赚钱？**

---

## 0) 输入证据（可复核路径）

- **A_real + W2** summary：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_112841/multiple_experiments_summary.json`
- **B2_shuffle_returns + W2** summary：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_114331/multiple_experiments_summary.json`

Agent级落盘（每个目录内均为 100/100）：

- `behaviors_run_<run_id>.json`
- `genomes_run_<run_id>.npy`

共同设置：

- ablation：`I_min_134`（I1+I3+I4；I2=0）
- window：`W2 start=4380 len=4380`
- n_runs：100

---

## 1) 一句话裁决

**裁决：通过。** 在 W2 中，A 的 `system_roi` 明显优于 B2（+3.97pp），且 Agent 级证据显示：A 更容易进入/维持某些“行为簇”（行为空间状态），这些簇与更好的生命周期结果相关；B2 的簇分布更偏向于“亏损型簇/穿仓簇”。

---

## 2) Gate 2.3 的 run 级事实（结论先于解释）

- **system_roi（current_total 口径）**：
  - A：**+1.92%**
  - B2：**-2.05%**
  - A-B2：**+3.97pp**
- **extinct_runs**：
  - A：1/100
  - B2：0/100

> 注：W2 里“灭绝”不是主差异，主差异是净值（system_roi）。

---

## 3) Agent 级人口学证据（不解释先陈述）

从 `behaviors_run_*.json` 直接汇总（100 runs 平均）：

- **A（W2）**
  - avg_total_agents≈111.39（平均每run最终出现过的Agent总数）
  - avg_children≈11.39（birth_time>0）
  - avg_alive_agents≈7.30
  - death_reason 总体：`quarterly_review`≈10364，`capital_depleted`≈45

- **B2（W2）**
  - avg_total_agents≈120.14
  - avg_children≈20.14
  - avg_alive_agents≈16.66
  - death_reason 总体：`quarterly_review`≈10206，`capital_depleted`≈135，`unknown`≈7

关键观察（仅做事实层面的指示）：

- B2 的“繁殖/存活数量”更高，但 `system_roi` 更差  
  ⇒ **“更多繁殖/更多存活” ≠ “更赚钱”**（至少在当前世界规则下如此）。
- B2 的 `capital_depleted` 死亡总数更高（135 vs 45）  
  ⇒ B2 更容易发生“资金归零型死亡”。

---

## 4) Agent 行为空间聚类（不含ROI特征，避免循环解释）

### 4.1 聚类输入（行为空间特征）

用于聚类的特征（不含ROI）：

- `log1p(total_trades)`
- `win_rate`（无交易记为0）
- `is_alive`
- `age_ticks`
- `last_signal`
- `state_final` one-hot（IN/OUT）
- `death_reason` one-hot（top理由：quarterly_review / capital_depleted / unknown）

### 4.2 输出（最佳K）

- best_k=8
- silhouette≈0.507

> 该聚类不是“真理”，它只是把 Agent 行为压缩成可讨论的“簇”，用于做**分布差异**与**簇贡献**分析。

---

## 5) 机制线索：差异主要来自“簇分布不同”，而非某个簇内必然更强

我们把每个簇对 `roi_lifetime` 的差异做了一个简单的分解（用来定位“差异从哪里来”）：

\[
\\Delta \\approx \\sum_c P_A(c)\\cdot \\mu_A(c) \\, - \\, \\sum_c P_{B2}(c)\\cdot \\mu_{B2}(c)
\]

其中 \(P\) 是该组落在簇 \(c\) 的比例，\(\mu\) 是该簇内的平均 `roi_lifetime`。

最强的结构信号之一：

- **Cluster 7**：
  - A 占比 \(P_A\\approx 0.258\)，B2 占比 \(P_{B2}\\approx 0.011\)（差异极大）
  - 该簇平均 `roi_lifetime`：A≈+0.195，B2≈+2.150（B2 样本很少、均值可能被极端值拉高）
  - 结论：**A 更容易进入这一簇（行为模式），B2 很少进入**。  

这就是“时间结构”最符合直觉的机制形式：  
**不是B2“不会赚钱”，而是它更难稳定地到达/保持某些行为模式；A 在真实时间结构中更容易到达这些模式。**

---

## 6) 重要口径提醒（避免把证据链用歪）

- 本文的 `roi_lifetime` 来自 Agent 级 `final_capital / initial_capital - 1`，它不是 `system_roi`。  
  **它是机制线索，不是最终裁决指标。**
- 最终裁决指标仍以 `system_roi`（current_total 口径）为准。

---

## 7) 下一步（把“线索”升级为“可解释机制”）

在 W2 上下一步最小动作：

- 针对“关键簇”（如 Cluster 7），抽取该簇的 `genomes_run_*.npy` 子集，做：
  - 簇内基因均值/方差
  - A vs B2 在该簇的基因差异维度排名（Top Δ权重）
  - 与 `DecisionEngine` 的输入维度对齐，形成“基因表达→行为模式”的解释链


