# V10 消融（Prior leakage）执行规范（A/B 裁决用）

目的：把“隐含预设策略（prior leakage）”从争论变成可复核的实验事实。  
适用：`docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **G0.6 / G3.3**。

---

## 1) 核心原则（强制）

- **只动实验入口，不动世界规则**：仅在 experiment runner 层做“输入置空/置零”，不得改 `DecisionEngine`、`Agent`、`SystemManager` 等核心逻辑。
- **同一对照口径**：A vs B2 必须保持：
  - 相同的 seeds 列表
  - 相同的数据窗口/数据文件
  - 相同的所有阈值与参数（只改变“消融开关”）
- **落盘可审计**：summary JSON 必须写入 `audit_declaration.ablation` 字段（例如 `"M_zeroed"` / `"C_zeroed"` / `"none"`）。

---

## 2) 最小实验矩阵（强制）

每个消融都至少跑一组 **A vs B2**（建议 `n_seeds >= 30`）：

### 2.1 M 消融（优先）

- A：真实时间结构 + **M={}/M置零**
- B2：打乱log-return顺序 + **M={}/M置零**

### 2.2 C 消融（其次）

- A：真实时间结构 + **C={}/C置零**
- B2：打乱log-return顺序 + **C={}/C置零**

> 解释：如果 A>B2 的差异主要依赖 M（或C）通道，消融后应显著退化；否则说明时间结构信号主要来自其它通道或纯价格结构。

---

## 3) 输出物（强制）

每次跑完必须产出：

- `multiple_experiments_summary.json`
  - 必含：`config`、`audit_declaration`、`all_stats`、`summary_stats`
  - 必含：`audit_declaration.ablation`
- Research 侧一页裁决记录（Markdown）
  - 标题命名建议：`V10_ACCEPTANCE_DECISION_ABLATION_<M|C>_A_vs_B2_<YYYYMMDD>.md`
  - 必含：主指标（`system_roi`、`extinction_rate`）的均值/中位数/分位数 + p值 + 效应量
  - 必含：与“未消融”基线的对照解释（是否退化）

---

## 4) 判定口径（简化版）

- **通过（支持“无prior leakage”）**：消融后 A>B2 的差异显著减弱或消失（至少在 `system_roi` 上）。
- **失败（怀疑 prior leakage 或通道依赖过强）**：消融后 A>B2 依旧强且稳定，或出现反直觉增强，需要进一步拆解“究竟哪条硬规则/缩放/阈值在起作用”。


