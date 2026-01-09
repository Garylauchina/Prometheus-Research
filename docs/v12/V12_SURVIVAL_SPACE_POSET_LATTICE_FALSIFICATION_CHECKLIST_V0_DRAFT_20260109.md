# V12 — Survival Space — Poset / Lattice Falsification Checklist v0 (Draft) — 2026-01-09

Additive-only. Document type: **Research Falsification Checklist**.

Scope: Survival Space（非决策、非优化、非盈利指标）  
Purpose: 明确“偏序 / 格”在本系统中**不成立或不应继续使用**的可观测条件（post-hoc only）。

Cross-links:
- Survival Space SSOT: `docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md`
- v1.0.1 Extended Validation Milestone: `docs/v12/V12_SURVIVAL_SPACE_EM_V1_0_1_FIX_M_EXTENDED_VALIDATION_MILESTONE_20260109.md`

---

## 0) 使用前提（冻结条件）

在进入任何偏序 / 格讨论之前，以下前提必须成立：

- Survival Space 已被确认是**连续调制（suppression / downshift 主导）**，而非二值 gate。
  - 证据入口：见 v1.0.1 extended validation milestone 与 artifacts bundle。
- 盈利 / 亏损 / reward 不参与任何判断。
- 筛选 ≠ 决策。
- 偏序仅用于 post-hoc 生存空间刻画（不得回灌 runtime）。

Fail-closed:
- 若任一前提被破坏，本清单自动失效（NOT_APPLICABLE）。

---

## 1) 可比性失效（Comparability Collapse）

### 1.1 定义

尝试在行为轨迹集合 \(A\) 上定义关系：

\[
a \preceq b \;\;\Leftrightarrow\;\; a \text{ 在所有生存约束维度上不比 } b \text{ 更“困难”}
\]

### 1.2 证伪条件

偏序判定失效，若出现以下任一情况（同一 world contract + 同一 epoch 尺度下）：

- \(a \preceq b\) 在不同时间窗口**系统性反转**。
- 可比性依赖于：
  - 采样顺序
  - seed 对齐
  - 事后窗口裁剪

### 1.3 判定结论

若可比关系无法在同一世界条件下稳定复现，则：
- Survival Space 不具备偏序基础结构。

---

## 2) 不可比性饱和（Incomparability Saturation）

### 2.1 定义

对随机采样的行为对 \((a,b)\)，统计：

- 可比：\(a \preceq b\) 或 \(b \preceq a\)
- 不可比：两者在不同约束维度互有优势

### 2.2 证伪条件

若在合理样本规模下：

- 不可比比例 ≥ 80%（阈值可调，但需冻结）
- 且该比例随样本数增加不显著下降

### 2.3 判定结论

偏序在形式上成立，但在操作上不携带信息量，等价于全集过滤。

---

## 3) 信息增益失败（No Informational Gain）

### 3.1 对照基线

Baseline 定义为：

- 仅使用硬约束（M）
- 不引入任何偏序结构
- 输出 allowed / not-allowed 判定

### 3.2 证伪条件

若引入偏序后，对“是否还能继续行动”的判定在：

- 误判率 / 不确定性 / 稳定性

上不优于 baseline。

### 3.3 判定结论

偏序未能提供超出“硬约束过滤”的额外结构信息，属于装饰性建模。

---

## 4) 结构退化诱因（Forced Linearization）

### 4.1 观察信号（危险区）

若在实现或分析过程中出现以下行为压力：

- 需要给约束维度加权
- 需要定义“更生存 / 更优生存”
- 需要选取极大元 / 代表元
- 需要排序以“便于使用”

### 4.2 证伪条件

只要出现任一情况，并被认为是“系统继续运作所必需”：

- 偏序 / 格假设立即判定为失败（FAIL）。

### 4.3 说明

这是原则性失败，不是工程不足。

---

## 5) 格结构不可闭合（Lattice Non-Closure）

### 5.1 理论期望（若尝试格）

若尝试提升为格结构，应满足：

- 任意两元素存在：
  - meet（共同约束下界）
  - join（最小放松上界）

### 5.2 证伪条件

若满足任一：

- meet / join 不存在
- 或仅在引入人为规则后才能存在
- 或不同 epoch 下 closure 条件不一致

### 5.3 判定结论

Survival Space 不具备格结构；偏序已是上限，不应继续提升。

---

## 6) 时间尺度崩塌（Epoch Sensitivity Failure）

### 6.1 定义

偏序关系应在冻结的 epoch 定义下成立。

### 6.2 证伪条件

若：

- 更换 epoch 粒度（但不更换 world contract）
- 偏序结构整体消失或完全重排

### 6.3 判定结论

当前 Survival Space 不可被稳定结构化，偏序只是在局部时间窗口的幻象。

---

## 7) 总体失败判定（Global Kill Switch）

满足以下任一条，即触发 GLOBAL FAIL：

- 2 个以上核心证伪条件成立（1/2/3/5/6 视作核心）
- 或任一 Forced Linearization 条件成立（§4）
- 或团队在使用偏序时出现“这不这样做就跑不下去”的共识

---

## 8) 失败后的合法结论（必须明确）

若偏序 / 格被证伪，唯一允许的结论是：

Survival Space 在当前世界与测量方式下，不具备可被序结构表达的稳定几何；不存在排序，不存在可比性，也不存在结构压缩。

这不是失败，是测量结果。

---

## 9) 明确禁止的后续行为

在偏序 / 格被证伪后，严禁：

- 回退到评分 / 排序模型
- 引入 reward proxy
- 用盈利或稳定性“补救结构”
- 用“暂时有效”作为正向证据

---

## 10) 文档地位声明（SSOT 用）

本清单用于判定偏序 / 格是否不应继续使用；
不构成其成立的任何正向证明。

若无明确证伪结果，偏序 / 格仅处于“尚未被否定”状态。

---

Frozen closing sentence (non-narrative):

> 一个能被清楚否定的工具，才配得上被认真尝试。

