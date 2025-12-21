# V10 窗口迁移裁决（W1b 半年窗）：I_min_134 下 A vs B2（n=100）— 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **Gate 2.3（时间窗迁移）**。  
数据只有 8760 小时（1年），因此将窗口拆成两段半年窗（W1b/W2）以实现**严格不重叠**的迁移验证。

---

## 0) 证据路径（来自 Prometheus-Quant，必须填）

- **A组（真实时间结构 + I_min_134 + W1b）**：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W1b_start0_len4380__20251221_091145/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_min_134 + W1b）**：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W1b_start0_len4380__20251221_092819/multiple_experiments_summary.json`

窗口参数（必须在 summary 中可读到且两组一致）：

- `window_id=W1b`
- `start_idx=0`
- `max_ticks=4380`

---

## 1) Gate 0（硬门槛）

- **数值健康**：**PASS**（无 NaN/Inf/爆炸）
- **对照物理合理**：**PASS**（B2 为 shuffle_log_returns_rebuild_price）
- **消融声明一致**：**PASS**（ablation=I_min_134，detail一致）

---

## 2) Primary endpoints（W1b，A vs B2，n=100）

### 2.1 system_roi（基于 current_total）

- A mean = **-5.613%**，B2 mean = **-9.417%**
- Mann–Whitney U：U = **8500.0**，p = **1.224e-17**
- Cliff’s delta：δ = **0.7000**

裁决：**PASS（A显著优于B2）**

### 2.2 extinction_rate

- A extinct = **0/100**，B2 extinct = **7/100**
- Fisher exact：p = **0.0140**，odds = **0.0**，risk_diff(A-B2) = **-7pp**

裁决：**PASS（A显著更低灭绝率）**

---

## 3) W1b 小结（TBD）

- 一句话：在 W1b（上半年窗）中，I_min_134 同时给出 **更好的净值（A>B2）** 与 **显著更低的灭绝率（A<B2）**，属于非常强的迁移证据；下一步看 W2 是否保持方向一致。


