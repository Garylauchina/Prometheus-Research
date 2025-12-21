# V10 B阶段 v2 审计补充（统一赢家口径 + IN/OUT同向性）— W1b + I_min_134（A vs B2）— 2025-12-21

本文件对 W1b 做 v2 增强审计：  
解决“锚定阈值退化”问题，并验证关键差异通道是否在 OUT/IN 两套网络里同向（更像真实机制）。

---

## 0) 输入证据（可复核）

- A：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W1b_start0_len4380__20251221_115821`
- B2：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W1b_start0_len4380__20251221_121143`

协议参考：`docs/v10/V10_B_STAGE_V2_PROTOCOL_WINNER_DEFINITION_AND_SIGN_CONSISTENCY.md`

---

## 1) 赢家口径（两套阈值并行 + 退化处理）

基础指标：`roi_lifetime = final_capital/initial_capital - 1`

### 1.1 绝对赢家（abs_5p）

- 阈值：`roi_lifetime >= +5%`
- winner_rate：
  - A：**1.14%**（133/11713）
  - B2：**1.80%**（186/10357）

说明：W1b 是困难窗口，“大赢家”本来就稀少，因此 abs_5p 在这里更多是“极端赢家率”，不是主要机制指标。

### 1.2 锚定赢家（anchor：退化处理生效）

观测到：A 的 `q90_A = 0.0`，若直接用 `roi>=q90_A` 会退化成“几乎等同 roi>=0”，口径过松。  
因此按协议启用退化处理：

- 采用：`q95_A`（method=`q95_A`，value≈**+0.65%**）
- winner_rate（同一阈值应用于 A 与 B2）：
  - A：**5.00%**（586/11713）
  - B2：**3.83%**（397/10357）

结论（结构层面）：  
在 W1b 中，用合理的锚定阈值（不退化）时，A 的赢家比例仍高于 B2。

---

## 2) IN/OUT 同向性审计（Sign Consistency）

结果（W1b）：

- alive：n_pairs=33，同向性=**1.00**
- alive_child：n_pairs=34，同向性=**1.00**
- winner_abs_5p：n_pairs=38，同向性=**1.00**
- winner_anchor：n_pairs=35，同向性=**1.00**

含义：  
W1b 的关键差异通道也表现为 **OUT/IN 两套网络高度同向**，这让“生存/繁殖机制”更像真实的可重复结构，而不是一次性噪声。

---

## 3) W1b 的 v2 机制结论（与W2互补）

- W1b 的“系统差异”首先体现为 **人口/繁殖持续性**（run级：A 0/100 灭绝 vs B2 7/100；繁殖动能差显著）。
- v2 的补强点是：当我们用不退化的“锚定赢家口径”衡量时，A 的优势仍成立，且差异通道在 IN/OUT 中同向，支撑“可重复机制”的主张。


