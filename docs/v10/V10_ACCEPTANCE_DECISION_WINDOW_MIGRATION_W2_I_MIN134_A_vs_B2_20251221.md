# V10 窗口迁移裁决（W2 下半年窗）：I_min_134 下 A vs B2（n=100）— 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **Gate 2.3（时间窗迁移）**：  
W2 为下半年窗，与 W1b 不重叠且等长。

---

## 0) 证据路径（来自 Prometheus-Quant，必须填）

- **A组（真实时间结构 + I_min_134 + W2）**：`<PASTE_A_SUMMARY_PATH>`
- **B2组（打乱log-return重建价格 + I_min_134 + W2）**：`<PASTE_B2_SUMMARY_PATH>`

窗口参数（必须在 summary 中可读到且两组一致）：

- `window_id=W2`
- `start_idx=4380`
- `max_ticks=4380`

---

## 1) Gate 0（硬门槛）

- **数值健康**：PASS/FAIL（NaN/Inf/爆炸即Fail）
- **对照物理合理**：PASS/FAIL（B2必须是 shuffle_log_returns_rebuild_price）
- **消融声明一致**：PASS/FAIL（ablation=I_min_134，detail正确）

---

## 2) Primary endpoints（W2，A vs B2，n=100）

### 2.1 system_roi（基于 current_total）

- A mean=<TBD>，B2 mean=<TBD>
- Mann–Whitney U：U=<TBD>，p=<TBD>
- Cliff’s delta：δ=<TBD>

裁决：PASS/FAIL

### 2.2 extinction_rate

- A extinct=<TBD>/100，B2 extinct=<TBD>/100
- Fisher exact：p=<TBD>，odds=<TBD>，risk_diff(A-B2)=<TBD>

裁决：PASS/FAIL

---

## 3) W2 小结（TBD）

- 一句话：<TBD>


