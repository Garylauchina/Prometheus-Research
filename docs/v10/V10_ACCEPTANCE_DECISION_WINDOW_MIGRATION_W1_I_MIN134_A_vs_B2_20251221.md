# V10 窗口迁移裁决（W1）：I_min_134 下 A vs B2（n=100）— 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **Gate 2.3（时间窗迁移）**：  
在固定世界规则与固定 I_min_134（最小生存感官候选）条件下，检验 **W1 窗口**内 A vs B2 的结论是否保持。

---

## 0) 证据路径（来自 Prometheus-Quant）

- **A组（真实时间结构 + I_min_134 + W1）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W1_start0_len8760__20251221_082540/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + I_min_134 + W1）**：  
  `/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W1_start0_len8760__20251221_084753/multiple_experiments_summary.json`

窗口参数（两组一致，已落盘）：

- `window_id=W1`
- `start_idx=0`
- `max_ticks=8760`

数值健康（两组均有）：`has_nan=false, has_inf=false, has_explosion=false`

---

## 1) Primary endpoints（W1，A vs B2，n=100）

### 1.1 Primary #1：system_roi（基于 current_total）

- **A mean**：-5.902%  
- **B2 mean**：-9.349%

统计检验（双侧）：**Mann–Whitney U**

- U = 8245.0  
- p = 2.235e-15

效应量（Cliff’s delta）：

- δ = 0.6490（A总体优于B2，强效应）

**裁决（Primary #1）：PASS（W1 内 A 显著优于 B2）**

### 1.2 Primary #2：extinction_rate

- **A 灭绝率**：56/100 = 56.0%  
- **B2 灭绝率**：51/100 = 51.0%

统计检验（双侧）：**Fisher exact**

- p = 0.5708  
- odds = 1.2228  
- risk_diff（A-B2）= +5.0pp

**裁决（Primary #2）：FAIL（差异不显著）**

---

## 2) W1 小结

- 在 W1 窗口中，`system_roi` 依旧稳定体现 A>B2（强显著 + 强效应量）。
- 灭绝率方向仍略对 A 不利，但在该样本量下不显著。

下一步：等待 W2，再做 Gate 2.3 的“跨窗口一致性裁决”。


