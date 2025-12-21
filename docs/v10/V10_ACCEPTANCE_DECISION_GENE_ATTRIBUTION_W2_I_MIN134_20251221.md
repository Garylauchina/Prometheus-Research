# V10 B阶段机制归因（基因表达回溯 v1）— W2 + I_min_134（A vs B2）— 2025-12-21

目的：把 **W2 的赚钱优势（A>B2）** 从“Agent级行为/簇分布线索”推进到“可指向的基因表达差异”：  
342维权重 → IN/OUT 两套网络 → 33维输入通道（E/I/M/C）与隐藏神经元位置。

---

## 0) 输入证据（可复核）

- A（真实时间结构）目录：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_112841`
- B2（打乱时间结构）目录：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_114331`

Agent级落盘（每组 100 runs，均齐全）：

- `behaviors_run_<run_id>.json`
- `genomes_run_<run_id>.npy`（全体Agent，shape=(N,342)，与 behaviors 严格对齐）

---

## 1) 关键口径（必须写清楚）

### 1.1 输入向量维度与顺序（33维）

`FeatureCalculator.features_to_vector()` 固定顺序（enable_optional_e_features=False，enable_i4_last_signal=True）：

- E1..E12（12维）
- I1..I4（4维）
- M1..M12（12维）
- C1..C5（5维）

合计：12+4+12+5=**33维**。

### 1.2 基因向量结构（342维）

- 0..169：OUT 状态网络权重（170）
- 170..339：IN 状态网络权重（170）
- 340：entry_threshold（Route2 下基本不作为硬门槛，可能是“死基因”）
- 341：exit_threshold（Route2 下改用 signal<=0 离场，可能是“死基因”）

每个状态网络 170维内部结构（ShallowNetwork）：

- W1：33×5=165（输入特征 → 5个隐藏神经元）
- W2：5（隐藏 → 输出）

---

## 2) W2 的“赚钱结构”先验：收益分布出现硬差异

对所有Agent的 `roi_lifetime`（final_capital / initial_capital - 1）做分位数对比：

- A 的 top10% 门槛（q90）：**≈ +8.72%**
- B2 的 top10% 门槛（q90）：**≈ +0.76%**

这意味着：  
**A 在 W2 的“赢家尾部”明显更肥（更容易产生高收益个体），而 B2 的尾部被压扁。**  
这与 run 级 `system_roi`（A +1.92% vs B2 -2.05%）是同一方向的结构证据。

---

## 3) 用于回溯的对比人群（W2）

从 behaviors 汇总得到：

- 全体（all）：
  - A：11139
  - B2：12014
- 存活（alive）：
  - A：730
  - B2：1666
- 存活子代（alive_child）：
  - A：379
  - B2：1025
- Top10 收益人群（top10_roi_lifetime，按各自组内 q90 切分）：
  - A：1114
  - B2：1202

注意：

- `top10_alive` 在 A 中只有 1 个样本（B2=228），因此**不做**该对比，避免伪结论。

---

## 4) 结果（v1）：W2 的关键差异更集中在 M/I/E 的通道上

我们按每个基因维度的 Cohen’s d（效应量）做 Top 排名。这里不强行解释因果，只把“差异指向哪里”钉死。

### 4.1 存活人群（alive_A vs alive_B2）：M维度占主导（执行/强平阻抗）

Top差异通道（同时在 OUT/IN 两套网络出现）：

- OUT.W1：`M1_fill_impedance → hidden#4`（强）
- OUT.W1：`M9_liquidation_impedance → hidden#1/#3`（强）
- IN.W1：`M1_fill_impedance → hidden#4`（强）
- IN.W1：`M9_liquidation_impedance → hidden#1`（强）

直观含义（只到“机制线索”级别）：

> 在 W2 中，“活着的那部分人”首先体现为对 **成交难度（M1）** 与 **强平压力（M9）** 的表达差异。  
> A 与 B2 在这些通道上的表达偏好明显不同，且跨 OUT/IN 同时出现，说明不是偶发。

### 4.2 存活子代（alive_child_A vs alive_child_B2）：M9 更突出（强平阻抗是核心筛选面）

最强项几乎直接锁死在 M9 上：

- OUT.W1：`M9_liquidation_impedance → hidden#3`（最强）
- IN.W1：`M9_liquidation_impedance → hidden#3`（最强）
- OUT/IN：`M9_liquidation_impedance → hidden#1`（也很强）

这与“W2 里 B2 的 capital_depleted 更高”相呼应：  
**子代要活下来，首先得通过“强平压力”这一筛选面。**

### 4.3 Top10 收益人群（top10_roi_lifetime_A vs top10_roi_lifetime_B2）：I1 + 微观摩擦通道进入核心

Top差异项的结构非常一致：

- OUT/IN.W1：`I1_has_position → hidden#4`（Top1/Top2）
- OUT/IN.W1：`M6_impact_impedance → hidden#3`（显著）
- OUT/IN.W1：`M4_urgency_penalty → hidden#3`（显著）
- IN.W1：`M2_time_impedance → hidden#1`（显著）
- OUT/IN.W1：`E9_ask_volume_norm → hidden#3`（显著）

直观含义（仍只到线索级别）：

> W2 的“赢家人群”差异，不是靠某个神秘指标，而更像是：  
> **内部状态（是否持仓，I1） + 执行摩擦/冲击/紧迫（M2/M4/M6） + 订单簿量（E9）** 的表达组合发生了系统性偏移。

---

## 5) 为什么“全体人群 all”差异很弱反而是好事

在 all_A vs all_B2 上，Top效应量非常小（d≈0.01级）。这并不奇怪，甚至是我们想看到的：

- **赚钱差异来自少数人群/关键簇的结构性出现**（尾部/赢家），而不是“所有基因整体漂移很远”。
- 这与我们在 Agent 级聚类里看到的“簇分布差异导致总体优势”是同一种解释框架。

---

## 6) 下一步（v2：把线索升级为更硬的“表达链条”）

最小增强路径（仍不改 core）：

1) 固定一个“赢家定义”（例如统一用 A 的 q90 或者用绝对阈值，如 roi_lifetime>5%）  
   避免 A/B2 各自 q90 造成“赢家口径不同”的弱点。
2) 在赢家人群上，把 Top 通道（I1/M2/M4/M6/M9/E9）做：
   - OUT/IN 同向性检查（符号/隐藏单元一致性）
   - 与 `DecisionEngine` 的状态转移围栏（M7/M9/C4）做交叉解释


