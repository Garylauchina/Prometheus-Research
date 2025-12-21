# V10 窗口迁移裁决（W2 下半年窗）：I_min_134 下 A vs B2（n=100）— 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **Gate 2.3（时间窗迁移）**：  
W2 为下半年窗，与 W1b 不重叠且等长。

---

## 0) 证据路径（来自 Prometheus-Quant，必须填）

- **A组（真实时间结构 + I_min_134 + W2）**：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_094318/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_min_134 + W2）**：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_100107/multiple_experiments_summary.json`

窗口参数（必须在 summary 中可读到且两组一致）：

- `window_id=W2`
- `start_idx=4380`
- `max_ticks=4380`

---

## 1) Gate 0（硬门槛）

- **数值健康**：**PASS**（无 NaN/Inf/爆炸）
- **对照物理合理**：**PASS**（B2 为 shuffle_log_returns_rebuild_price）
- **消融声明一致**：**PASS**（ablation=I_min_134，detail一致）

---

## 2) Primary endpoints（W2，A vs B2，n=100）

### 2.1 system_roi（基于 current_total）

- A mean = **+1.925%**，B2 mean = **-2.047%**
- Mann–Whitney U：U = **7525.0**，p = **6.901e-10**
- Cliff’s delta：δ = **0.5050**

裁决：**PASS（A显著优于B2）**

### 2.2 extinction_rate

- A extinct = **1/100**，B2 extinct = **0/100**
- Fisher exact：p = **1.0**，odds = **∞**，risk_diff(A-B2) = **+1pp**

裁决：**FAIL（差异不显著；且方向对A略不利但极小）**

---

## 3) W2 小结（TBD）

- 一句话：在 W2（下半年窗）中，I_min_134 仍稳定体现 **净值 A>B2**，且 A 出现少量灭绝（1%）但与 B2 的差异不显著；整体上结论方向与 W1/W1b 一致。


