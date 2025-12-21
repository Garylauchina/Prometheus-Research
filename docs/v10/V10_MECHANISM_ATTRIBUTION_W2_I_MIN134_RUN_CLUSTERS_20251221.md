# V10 机制归因（B阶段，最小闭环v1）：W2 + I_min_134 的 run 级行为空间聚类 — 2025-12-21

目的：在不改世界规则的前提下，把“A>B2（system_roi）”从现象推进到**可解释的机制线索**。  
本报告采用 **run 级行为特征聚类**（非基因、非Agent级），属于 B 阶段的最小可复核闭环。

---

## 0) 数据来源（Prometheus-Quant）

- A（真实时间结构）：`prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_094318/`
- B2（打乱log-return重建价格）：`prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_100107/`

共同前提：

- 固定 `I_min_134`（I1+I3+I4；I2=0）
- window：W2（start_idx=4380, max_ticks=4380）
- n_seeds：100

---

## 1) 方法（可复核口径）

### 1.1 为什么用 run 级聚类

当前落盘的 `genes_run_*.npy` 是 TopK 基因矩阵，但缺少“基因 ↔ 具体行为/ROI”的逐个Agent映射；因此先用 run 级行为作为“机制线索”，避免强行过拟合解释。

### 1.2 聚类特征（不含ROI，避免循环解释）

用于聚类的行为特征（对数压缩后标准化）：

- `trades`
- `reproductions`
- `deaths`
- `alive_agents`
- `total_agents_ever`

随后在每个簇内再比较 **结果指标**：

- `system_roi`
- `extinction_rate`

---

## 2) 结果：两个稳定的“run 行为簇”

（最佳K=2，Silhouette≈0.347）

### 簇0：低活动/低繁殖（A占主）

- **规模**：n=94（A=78，B2=16）
- **行为画像均值**：
  - trades≈64,069
  - reproductions≈10.27
  - alive_agents≈6.33
- **结果对比（同簇内）**：
  - A system_roi≈+2.01%
  - B2 system_roi≈-0.85%

### 簇1：高活动/高繁殖（B2占主）

- **规模**：n=106（A=22，B2=84）
- **行为画像均值**：
  - trades≈82,102
  - reproductions≈20.64
  - alive_agents≈16.99
- **结果对比（同簇内）**：
  - A system_roi≈+1.62%
  - B2 system_roi≈-2.28%

---

## 3) 解释（目前能负责任地说到哪里）

### 3.1 “为什么 A>B2” 的最小解释线索

在**两种不同的行为模式簇**里，A 都比 B2 有更高的 `system_roi`。这支持一个相对稳健的解释：

> A>B2 不是因为“某一种行为模式刚好被A跑出来”，而更像是：在不同强度的交易/繁殖行为下，真实时间结构依然提供了可利用的优势。

### 3.2 B2 更“活跃/繁殖更多”但 ROI 更差的含义

这提示：在当前世界规则下，“更活跃/更繁殖”未必对应更高 `system_roi`。这与我们此前发现的“盈利与生存/繁殖并非同一轴”相呼应，但仍需 Agent 级证据落盘才能把因果链讲完整。

---

## 4) 下一步（把 v1 升级到真正的“机制背书”）

要把归因从“线索”升级到“背书”，最小改动是**补齐 Agent 级行为落盘**（不改核心世界规则）：

- 在 runner 层为每个 run 输出 `behaviors_run_<id>.json`，每条记录至少包含：
  - agent_id、final_capital/roi、total_trades、state_switches、is_alive、death_reason（如可得）
  - 以及该 agent 对应的 genome（或 genome_hash 以便关联到 genes矩阵）

这样就能做真正的 B 阶段归因：

- Agent 行为空间聚类 → 找到“贡献A>B2”的簇
- 再回到基因空间看该簇的权重模式（gene expression 的可解释片段）


