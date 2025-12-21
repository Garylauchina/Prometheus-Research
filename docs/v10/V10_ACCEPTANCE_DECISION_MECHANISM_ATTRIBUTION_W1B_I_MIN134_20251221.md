# V10 B阶段机制归因裁决（Agent级证据链）— W1b + I_min_134（A vs B2）— 2025-12-21

本裁决回答：  
**在 W1b（前半窗口）里，A 为什么同时更“活得下来”（灭绝更少）且 system_roi 更好？**

---

## 0) 输入证据（可复核路径）

- **A_real + W1b** summary：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W1b_start0_len4380__20251221_115821/multiple_experiments_summary.json`
- **B2_shuffle_returns + W1b** summary：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W1b_start0_len4380__20251221_121143/multiple_experiments_summary.json`

Agent级落盘（每个目录内均为 100/100）：

- `behaviors_run_<run_id>.json`
- `genomes_run_<run_id>.npy`

共同设置：

- ablation：`I_min_134`（I1+I3+I4；I2=0）
- window：`W1b start=0 len=4380`
- n_runs：100

---

## 1) 一句话裁决

**裁决：通过。** 在 W1b 中，A 的 `system_roi` 明显优于 B2（+3.81pp），同时 A 的灭绝率更低（0/100 vs 7/100）。Agent级证据显示：A 在该窗口拥有显著更强的“繁殖持续性”（children数量更高、存活子代占比更高），形成了稳定的人口底盘，进而把系统从“偶发灭绝”区间拉回到可持续区间。

---

## 2) run 级事实（结论先于解释）

- **system_roi（current_total 口径）**：
  - A：**-5.61%**
  - B2：**-9.42%**
  - A-B2：**+3.81pp**
- **extinct_runs**：
  - A：0/100
  - B2：7/100
- **avg_alive_agents**（摘要统计）：
  - A：≈22.56
  - B2：≈5.73
- **avg_reproductions**：
  - A：≈17.13
  - B2：≈3.57

> 注：W1b 是“更难活”的窗口，差异体现为：**A 有持续的人口与繁殖，而 B2 缺乏繁殖动能**。

---

## 3) Agent 级人口学证据（繁殖持续性=核心）

从 `behaviors_run_*.json` 汇总（100 runs 平均）：

- **A（W1b）**
  - avg_total_agents≈117.13
  - avg_children≈17.13（birth_time>0）
  - avg_alive_agents≈22.56
  - avg_alive_children≈15.45
  - alive 中 children 占比≈0.677

- **B2（W1b）**
  - avg_total_agents≈103.57
  - avg_children≈3.57
  - avg_alive_agents≈5.73
  - avg_alive_children≈3.32
  - alive 中 children 占比≈0.504

结论（机制层面最短解释）：

> **W1b 的关键不是“谁更能赚”，而是“谁能持续繁殖并维持人口”**。  
> A 在真实时间结构中显著更容易跨过繁殖阈值，从而维持生态系统；B2 在去时间结构后繁殖动能不足，更容易走向灭绝。

---

## 4) Agent 行为空间聚类（用于定位“存活簇”）

使用与 W2 同口径的“非ROI行为特征”做聚类：

- best_k=8
- silhouette≈0.646

观测到的稳定结构之一：

- 存活簇（`alive_rate=1.0`）中，A 的占比显著高于 B2（在多个大簇上 A_share≈0.79~0.80）。  
  ⇒ **A 更容易进入/停留在“低风险的存活行为模式”。**

> 这里的聚类用来定位“存活机制”，不是用来替代 system_roi 裁决。

---

## 5) 重要口径提醒

- B阶段最终裁决仍以 `system_roi` 为准；Agent级聚类/人口学用于解释“差异从哪里来”。
- 本文的核心归因对象是 **extinction_rate 与可持续繁殖能力**，不是“单个Agent是否盈利”。

---

## 6) 下一步（把“繁殖持续性”落到基因表达解释）

最小后续工作：

- 选取 W1b 中“存活簇”的Agent集合，抽取对应 `genomes_run_*.npy` 子集
- 做 A vs B2 的基因差异维度排序（Top Δ权重）
- 将这些维度映射回 `DecisionEngine` 的输入通道（E/M/I/C）与两套网络（IN/OUT），形成可读的“为什么能繁殖/能活”解释链


