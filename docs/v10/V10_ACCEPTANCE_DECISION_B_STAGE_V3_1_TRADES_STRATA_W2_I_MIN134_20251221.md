# V10 B阶段 v3.1 裁决：W2 锚定赢家 trades 分层稳定性（修复分箱退化）

日期：2025-12-21  
窗口：W2（start=4380, len=4380）  
配置：I_min_134（I1+I3+I4；I2=0）  
对比：A_real vs B2_shuffle_returns  

---

## 0) 这份 v3.1 在解决什么问题？

在 v3（分层稳定性）里，我们希望按 `total_trades` 把“锚定赢家”分层，检验 **Top 通道是否在不同交易强度层仍稳定**。

但 W2 上出现了一个**工程层面的退化**：  
`total_trades` 在锚定赢家人群中高度离散且集中，导致**分位数分箱无法形成有效边界**（大量样本堆在同一取值上），从而出现“空箱/退化箱”。

这不是“机制不存在”，而是“尺子分段方式失效”。所以 v3.1 的目标是：  
用一个**仍然可审计、仍满足样本下限**的分箱方式，完成同一件 v3 要求的事。

---

## 1) 锚定赢家口径（固定）

- anchor 方法：`q90_A`（以 A 组 `roi_lifetime` 的 90 分位数为阈值，同一阈值应用于 A 与 B2）
- `q90_A = 0.08723749095721656`（≈ +8.72%）
- 锚定赢家样本量（全体 run 聚合）：
  - A：1114
  - B2：381

证据来源（只读）：  
- A：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_112841`  
- B2：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_114331`

---

## 2) 为什么分位数分箱会退化（W2 的 trades “尖峰”）

锚定赢家内，`total_trades` 的分布极端集中：

- A 锚定赢家：50分位/75分位都等于 **2 笔**；90分位才到 4 笔；但尾部又很长（最大到 3290）。
- B2 锚定赢家：50分位等于 **4 笔**；75分位到 16 笔；尾部也很长（最大到 4186）。

因此用“合并后分位数”的三分位切分（即便先 `log1p`）仍然会把切点压成同一个值，产生空箱。

结论：**W2 trades 维度不能用分位数三等分来做 v3 分层**，必须改用固定阈值分箱（或其他稳健分箱）。

---

## 3) v3.1 分箱方案（可行且满足样本下限）

目标约束：每个 trades 分箱内，A 与 B2 都满足 `n >= 30`，才允许纳入结论（符合 Gate 3.5 的精神）。

我们对 W2 锚定赢家做阈值搜索，得到可行的三箱分层：

- **low**：`total_trades <= 4`
- **mid**：`5 <= total_trades <= 50`
- **high**：`total_trades > 50`

分箱样本量（锚定赢家集合内）：

| trades bin | A n | B2 n | 是否有效证据 |
|---|---:|---:|---|
| low (<=4) | 1012 | 198 | ✅ 有效 |
| mid (5..50) | 35 | 116 | ✅ 有效 |
| high (>50) | 67 | 67 | ✅ 有效 |

---

## 4) v3.1 结果（同向性稳定性 + Top 通道摘要）

说明：  
- 我们在每个 trades 分箱内，对 **锚定赢家** 做 A vs B2 的基因差分，取 Top 权重后做 **IN/OUT 同向性**（G3.4 的一致性审计思想）。  
- `consistency_rate` 指：在 Top 权重中能形成 OUT/IN 配对的 `(feature_idx, hidden_idx)` 连接里，`sign(delta_OUT) == sign(delta_IN)` 的比例。  

### 4.1 low（<=4 trades）

- 样本量：A=1012, B2=198
- 同向性：`n_pairs=12`, `consistency_rate=1.00`
- Top 代表通道（按 OUT/IN 配对强度排序的部分示例）：
  - `C4_group_death_rate`（OUT/IN 同向）
  - `I3_state_machine_state`（OUT/IN 同向）
  - `M10_volatility_stress`（OUT/IN 同向）
  - `C5_top_performers_signal`（OUT/IN 同向）
  - `M5_slippage_impedance`（OUT/IN 同向）

### 4.2 mid（5..50 trades）

- 样本量：A=35, B2=116
- 同向性：`n_pairs=13`, `consistency_rate=1.00`
- Top 代表通道（示例）：
  - `E11_24h_high_norm`（OUT/IN 同向）
  - `E12_24h_low_norm`（OUT/IN 同向）
  - `M11_pnl_signal_quality`（OUT/IN 同向）
  - `C4_group_death_rate`（OUT/IN 同向）
  - `M3_size_impedance`（OUT/IN 同向）
  - `I1_has_position`（OUT/IN 同向）

### 4.3 high（>50 trades）

- 样本量：A=67, B2=67
- 同向性：`n_pairs=12`, `consistency_rate=1.00`
- Top 代表通道（示例）：
  - `M12_comfort_signal_strength`（OUT/IN 同向）
  - `M2_time_impedance`（OUT/IN 同向）
  - `M6_impact_impedance`（OUT/IN 同向）
  - `E4_open_price_norm`（OUT/IN 同向）
  - `E1_close_price_norm`（OUT/IN 同向）
  - `I4_last_signal`（OUT/IN 同向）

---

## 5) 裁决（v3.1）

**结论：PASS（在可行分箱下，W2 的 trades 分层稳定性证据成立）**

- 我们用固定阈值分箱修复了 W2 trades 的分位数退化问题，并严格满足每箱 `nA>=30 且 nB2>=30`。
- 在 low/mid/high 三个 trades 层中，IN/OUT 同向性均达到 **1.00**（在可配对连接集合上）。
- Top 通道在不同 trades 层会“换重心”（低频更偏群体死亡率/状态，较高频更偏摩擦与信号舒适度），但**方向一致性不翻盘**。

---

## 6) 备注：这不改变世界规则

v3.1 只是在“研究审计层”把 trades 的分层尺子从“分位数三等分”换成了“满足样本下限的固定阈值分箱”。  
它不修改任何交易机制、阈值、资金规则或特征计算；仅使用已落盘的 `behaviors_run_*.json` 与 `genomes_run_*.npy` 做只读分析。


