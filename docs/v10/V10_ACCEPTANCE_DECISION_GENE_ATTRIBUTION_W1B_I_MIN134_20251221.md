# V10 B阶段机制归因（基因表达回溯 v1）— W1b + I_min_134（A vs B2）— 2025-12-21

目的：把“W1b 的生存/繁殖优势”从**人口学现象**进一步推进到**可指向的基因表达差异**（342维权重 → 对应到 E/I/M/C 输入与 IN/OUT 状态网络）。

---

## 0) 输入证据（可复核）

- A（真实时间结构）目录：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W1b_start0_len4380__20251221_115821`
- B2（打乱时间结构）目录：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W1b_start0_len4380__20251221_121143`

Agent级落盘（每组 100 runs，均齐全）：

- `behaviors_run_<run_id>.json`
- `genomes_run_<run_id>.npy`（全体Agent，shape=(N,342)，与 behaviors 严格对齐）

---

## 1) 关键口径（必须写清楚）

### 1.1 输入向量维度与顺序（33维）

`FeatureCalculator.features_to_vector()` 固定顺序（enable_optional_e_features=False，enable_i4_last_signal=True）：

- E1..E12（12维）
- I1..I4（4维）
- M1..M12（12维）
- C1..C5（5维）

合计：12+4+12+5=**33维**。

### 1.2 基因向量结构（342维）

- 0..169：OUT 状态网络权重（170）
- 170..339：IN 状态网络权重（170）
- 340：entry_threshold（Route2 下基本不作为硬门槛，可能是“死基因”）
- 341：exit_threshold（Route2 下改用 signal<=0 离场，可能是“死基因”）

每个状态网络 170维内部结构（ShallowNetwork）：

- W1：33×5=165（输入特征 → 5个隐藏神经元）
- W2：5（隐藏 → 输出）

因此一个具体权重可以被定位为：**(IN/OUT) × (W1/W2) × (feature_idx, hidden_idx)**。

---

## 2) 用于回溯的对比人群（W1b）

直接从 `behaviors_run_*.json` 汇总：

- **存活（alive, is_alive=true）**：
  - A：2256
  - B2：573
- **存活子代（alive_child, is_alive=true 且 birth_time>0）**：
  - A：1545
  - B2：332

> 这两组对比的意图很明确：  
> **W1b 的差异核心是“能否持续繁殖并维持人口”**，所以我们优先看“存活”与“存活子代”的基因表达差异。

---

## 3) 结果（v1）：差异最集中的位置

我们对比 **A_alive vs B2_alive**、以及 **A_alive_child vs B2_alive_child**，按每个基因维度的 Cohen’s d（效应量）做 Top 排名。

### 3.1 最强信号集中在：E1（价格位置）的权重通道（IN/OUT 同时出现）

Top 差异项（摘取前几条的共同结构）：

- OUT.W1：`E1_close_price_norm → hidden#1`（gene_idx=1，d≈+0.243）
- IN.W1：`E1_close_price_norm → hidden#1`（gene_idx=171，d≈+0.239）
- IN.W1：`E1_close_price_norm → hidden#2`（gene_idx=172，d≈-0.205）
- OUT.W1：`E1_close_price_norm → hidden#2`（gene_idx=2，d≈-0.203）

解释（只说到“证据允许的程度”）：

- A 的存活/繁殖优势，对应到基因表达上，首先表现为：**对“价格在归一化区间的位置（E1）”的敏感性通道发生系统性偏移**，而且在 OUT/IN 两套网络里都出现。

### 3.2 群体信号（C维度）也进入 Top 差异（提示“群体反馈回路”）

在存活人群中，出现了：

- OUT.W1：`C3_group_avg_pnl_pct → hidden#0`（gene_idx=150，d≈+0.181）
- IN.W1：`C3_group_avg_pnl_pct → hidden#0`（gene_idx=320，d≈+0.177）
- IN.W1：`C5_top_performers_signal → hidden#3`（gene_idx=333，d≈-0.172）

这更像是“系统级反馈”通道的差异：A 与 B2 在 W1b 中，对群体状态（尤其是群体PnL与头部信号）形成了不同的表达偏好。

### 3.3 I维度（I1_has_position）也出现差异，但不是最强项

例如：

- OUT.W1：`I1_has_position → hidden#1`（gene_idx=61，d≈+0.150）

含义倾向于：A 的存活人群在“是否持仓”的内部状态上，与某些隐藏通道形成了更一致的耦合。

---

## 4) 当前结论的边界（必须诚实）

- 这份回溯是 **“存活/存活子代人群”的关联性排名**，不是严格因果证明。  
  但它已经满足 B阶段的核心要求：**能把差异指向明确的输入通道与网络位置**，从而允许后续做“定点验证”（例如只冻结/扰动某些权重片段做复核）。
- Route2 下 `entry_threshold/exit_threshold` 很可能是“死基因”，不应过度解释其差异。

---

## 5) 下一步（v2，把回溯变成更硬的机制链）

建议的最小增强（仍不改 core）：

- 在 W1b 中，把“存活子代”进一步分层：按 `total_trades`、`win_rate`、`last_signal` 分箱
- 对每个分箱分别做 Top Δ权重，检查差异是否稳定（而非偶然）
- 对 Top 通道（例如 E1→hidden#1/#2、C3→hidden#0）做“符号一致性检查”：  
  OUT/IN 两套网络是否同向、是否呈现明确的策略分歧


