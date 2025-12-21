# V10 里程碑记录：Gate 2.3（窗口迁移一致性）通过 — 2025-12-21

## 这意味着什么（里程碑一句话）

在固定世界规则与 `I_min_134`（I1+I3+I4）配置下，主指标 **`system_roi`** 在多个时间窗口中均稳定呈现 **A（真实时间结构）显著优于 B2（打乱时间结构）**，因此“系统确实在利用市场时间结构”的证据完成了 **跨窗口一致性验证（Gate 2.3 通过）**。

> 注：这不是“保证盈利”，而是“方法论有效性获得可复核的工程证据（在system_roi上）”。

---

## 证据链（可复核路径）

- **Gate 2.3 一致性裁决（总裁决）**：  
  `docs/v10/V10_ACCEPTANCE_DECISION_WINDOW_MIGRATION_CONSISTENCY_I_MIN134_20251221.md`

支撑窗口裁决：

- **W1（全年窗）**：  
  `docs/v10/V10_ACCEPTANCE_DECISION_WINDOW_MIGRATION_W1_I_MIN134_A_vs_B2_20251221.md`
- **W1b（上半年窗，4380）**：  
  `docs/v10/V10_ACCEPTANCE_DECISION_WINDOW_MIGRATION_W1b_I_MIN134_A_vs_B2_20251221.md`
- **W2（下半年窗，4380）**：  
  `docs/v10/V10_ACCEPTANCE_DECISION_WINDOW_MIGRATION_W2_I_MIN134_A_vs_B2_20251221.md`

（背景：I_min_134 的精刻与对照裁决）

- `docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_I_MIN134_100SEEDS_A_vs_B2_20251221.md`
- `docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_I_MIN13_100SEEDS_A_vs_B2_20251221.md`
- `docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_I_100SEEDS_A_vs_B2_20251221.md`

---

## 我们目前“知道了什么”

- **已确认**：`system_roi` 是可迁移的结构信号（A>B2 跨窗口成立）。
- **已初步确认**：I 通道更像“生存/风险控制感官”，`I_min_134` 是当前最优的“最小生存感官候选”之一。
- **仍未锁定**：`extinction_rate` 在不同窗口的显著性不稳定；它应继续作为稳定性代价指标跟踪，而非“一票否决”。

---

## 下一步（进入 B 阶段：科研归因）

目标：回答“为什么 A>B2”，把现象变成可复核机制，而不是故事。

建议最小闭环：

- 固定 `I_min_134` + 选定一个窗口（建议先 W1b 或 W2）
- 基于每个 run 的 TopK genes 做聚类
- 输出每个簇的行为画像（交易数、存活率、ROI分布、死亡路径占比等）
- 形成一页“机制归因裁决记录”


