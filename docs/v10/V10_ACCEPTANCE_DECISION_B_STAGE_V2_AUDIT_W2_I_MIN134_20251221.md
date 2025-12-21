# V10 B阶段 v2 审计补充（统一赢家口径 + IN/OUT同向性）— W2 + I_min_134（A vs B2）— 2025-12-21

本文件是对 W2 的 v2 增强审计：  
把“赢家口径”固定化，并对关键通道做 **IN/OUT 同向性** 检查，目的是让 Research 结果更像“研究项目”而不是“运行日志”。

---

## 0) 输入证据（可复核）

- A：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_112841`
- B2：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_114331`

协议参考：`docs/v10/V10_B_STAGE_V2_PROTOCOL_WINNER_DEFINITION_AND_SIGN_CONSISTENCY.md`

---

## 1) 赢家口径（两套阈值并行）

基础指标：`roi_lifetime = final_capital/initial_capital - 1`

### 1.1 绝对赢家（abs_5p）

- 阈值：`roi_lifetime >= +5%`
- winner_rate：
  - A：**15.40%**（1715/11139）
  - B2：**3.89%**（467/12014）

### 1.2 锚定赢家（anchor：用A组阈值同一把尺子打两组）

- 采用：`q90_A`（method=`q90_A`，value≈**+8.72%**）
- winner_rate：
  - A：**10.00%**（1114/11139）
  - B2：**3.17%**（381/12014）

结论（只陈述结构）：  
**不管用绝对阈值还是锚定阈值，A 的赢家比例都显著高于 B2。**

---

## 2) IN/OUT 同向性审计（Sign Consistency）

我们在每个关键人群上取 Top-N（N≈80）的差异通道（按 |Cohen’s d| 排序），把同一 `(feature_idx, hidden_idx)` 的 OUT 与 IN 两套网络配对，检查符号是否一致。

结果（W2）：

- alive：n_pairs=32，同向性=**1.00**
- alive_child：n_pairs=37，同向性=**1.00**
- winner_abs_5p：n_pairs=33，同向性=**1.00**
- winner_anchor：n_pairs=34，同向性=**1.00**

解释（仅到“证据强度”）：  
**W2 的关键差异通道在 OUT/IN 两套网络里呈现高度一致的方向性**，这比“单点Top权重”更像可重复机制，而不是噪声。

---

## 3) W2 的 v2 机制结论（可用于下一步v3）

在赢家与存活相关人群中，差异通道持续指向：

- **M维度（交易摩擦/风险阻抗）**：例如 M1（成交阻抗）、M2（时间阻抗）、M9（强平阻抗）
- **I维度（内部状态）**：例如 I1（是否持仓）
- 以及少量 **E/C 通道**（订单簿量、群体信号）作为辅助

这为后续 v3（更强机制链）提供了明确靶点：  
**先在赢家人群上，固定赢家阈值，做通道级“符号一致性 + 稳定性分层”**，再决定是否进入“产品/虚拟盘背书”阶段。


