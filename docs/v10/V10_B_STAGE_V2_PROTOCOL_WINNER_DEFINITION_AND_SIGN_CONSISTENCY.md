# V10 B阶段 v2 协议：统一“赢家口径” + IN/OUT 同向性审计（可复核）

目的：把 B阶段从“线索级解释”推进到“更硬的机制证据”。  
本协议定义 **统一赢家口径** 与 **IN/OUT 表达同向性** 的审计方法，使任何结论都能被第三方复核。

---

## 1) 输入证据要求（硬约束）

每个实验目录必须具备（100 runs）：

- `multiple_experiments_summary.json`
- `behaviors_run_<run_id>.json`
- `genomes_run_<run_id>.npy`

其中：

- `genomes_run_<run_id>.npy[i]` 必须与 `behaviors_run_<run_id>.json` 中 `genome_index==i` 的 Agent 记录严格对齐。

---

## 2) 赢家口径（Winner Definition）

### 2.1 基础收益指标（必须）

统一使用 **`roi_lifetime`**：

\[
roi\\_lifetime = \\frac{final\\_capital}{initial\\_capital} - 1
\]

理由：它不受繁殖“ROI重置”影响，更适合做“赢家定义”。

### 2.2 两套赢家阈值（都要做）

为了避免“各组各自 q90”导致口径不一致，强制两套阈值并行：

- **绝对阈值**：`roi_lifetime >= +5%`（可换成 +2%、+10%，但必须提前声明并固定）
- **锚定阈值（A锚定）**：用 A组的 `q90_A` 作为阈值，**同一个阈值**应用于 A 与 B2：
  - `winner_anchor = (roi_lifetime >= q90_A)`

#### 2.2.1 退化处理（必须）

如果 `q90_A <= 0`（常见于困难窗口，收益分布被压到0附近），则 `roi>=q90_A` 会退化成“几乎等同 roi>=0”，口径过松。  
此时强制改用以下优先级（直到阈值>0）：

- 优先：`q95_A`
- 次选：`q90_A_pos`（仅在 `roi_lifetime>0` 的子集中取 0.9 分位数；要求样本数≥50）
- 兜底：绝对阈值 `+5%`

文档中必须记录最终采用的锚定方法与数值（例如：`method=q95_A value=0.0065`）。

输出必须包含：

- `winner_rate_abs`（A/B2）
- `winner_rate_anchor`（A/B2）
- `q90_A` 数值（以及退化时的替代阈值）

---

## 3) 基因表达映射（342 → 33维输入通道）

### 3.1 输入特征顺序（33维）

`FeatureCalculator.features_to_vector()` 固定顺序（enable_optional_e_features=False, enable_i4_last_signal=True）：

- E1..E12
- I1..I4
- M1..M12
- C1..C5

共 33 维。

### 3.2 权重结构

- OUT 网络：170维（W1=165 + W2=5）
- IN 网络：170维（W1=165 + W2=5）
- 另有阈值 2 维（entry/exit，Route2下可能为死基因）

### 3.3 W1 的可解释坐标

对任意基因索引映射为：

- `state ∈ {OUT, IN}`
- 若属于 W1：`feature_idx ∈ [0..32]`，`hidden_idx ∈ [0..4]`
- 若属于 W2：`hidden_idx ∈ [0..4]`

输出必须至少包含 Top-N（建议N=50）的：

- `gene_idx, cohen_d, delta_mean, (state, feature_name, hidden_idx)`

---

## 4) v2关键审计：IN/OUT 同向性（Sign Consistency）

### 4.1 为什么要做

如果同一个输入通道（例如 `M9_liquidation_impedance`）在 OUT 与 IN 两套网络里呈现**稳定的同向偏移**，这比“单点Top权重”更像真实机制，而不是噪声。

### 4.2 定义

对同一个 `(feature_idx, hidden_idx)`，比较 OUT 与 IN 的 Δ（A-B2）符号是否一致：

- `sign(delta_OUT) == sign(delta_IN)` 计为一致

输出：

- `sign_consistency_rate`：在选定集合（例如 Top-N 通道）上的一致比例
- 列出最稳定的若干通道（例如 Top 10）：
  - feature_name, hidden_idx, delta_OUT, delta_IN

---

## 5) 输出格式（Research仓库要求）

每个窗口（W1b/W2）至少产出两份文档：

- **机制归因 v2 补充裁决**（面向结论）
- **附录：审计表格与口径**（面向复核）

每份文档必须包含：

- 输入路径（绝对路径或相对路径，必须可定位）
- 赢家阈值两套结果（abs + anchor）
- Top通道列表（至少Top20）与 IN/OUT 同向性统计


