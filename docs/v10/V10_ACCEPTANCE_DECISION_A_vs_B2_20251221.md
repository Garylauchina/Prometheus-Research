# V10 验收裁决摘要：A（真实时间结构） vs B2（打乱收益率顺序） — 2025-12-21

本文件是基于 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的一次**正式裁决记录**（Decision Record）。  
目标：用量化交易实例检验“演化测量方法”是否能稳定利用市场时间结构（A>B2），并输出可复核证据链。

---

## 0) 数据源与复核路径（来自 Prometheus-Quant）

> 注意：本次对照实验目录命名存在混乱风险，因此以“文件路径”为唯一证据源。

- **A组（真实时间结构）**：  
  `prometheus/v10/experiments/results_B_shuffle_30_20251221_004609/multiple_experiments_summary.json`
- **B2组（零假设：打乱log-return顺序后重建价格）**：  
  `prometheus/v10/experiments/results/multiple_experiments_summary.json`

补充：存在一份**无效的对照尝试**（数值爆炸/溢出），不得用于裁决：  
`prometheus/v10/experiments/results_B2_shuffle_returns_30_20251221_010656/multiple_experiments_summary.json`

---

## 1) Gate 0：工程与会计完整性（硬门槛）

- **G0.1 可复现**：未在本裁决中复跑验证（待后续补齐）。
- **G0.2 可审计（落盘）**：✅ 通过  
  两组 summary 均包含 `audit_declaration` 与资金三元组字段（`allocated_capital/system_reserve/current_total`）。
- **G0.3 数值健康**：✅ 通过（仅针对本裁决使用的A与B2文件）  
  A与B2均未出现 `NaN/Inf/指数级溢出`；但“无效对照尝试”存在溢出，已剔除。
- **G0.4 统计口径正确**：✅ 通过  
  同时存在 `profitable_agents_all` 与 `profitable_agents_alive`。
- **G0.5 对照物理合理**：✅ 通过（B2）  
  B2使用“打乱收益率顺序后重建价格”，避免了“直接置换价格”导致的非物理跳变爆炸。

**Gate 0 裁决：PASS（可进入Gate 1）。**

---

## 2) Gate 1：非随机性（Primary endpoints 裁决）

本项目 Primary endpoints 已锁定为：

1) `system_roi`（基于 `current_total`）  
2) `extinction_rate`（`alive_agents==0` 的 run 占比）

样本量：A组 n=30，B2组 n=30（按 run 计）。

### 2.1 Primary #1：system_roi（A vs B2）

- **A mean**：-6.5836%  
- **B2 mean**：-10.1940%  
- **A median**：-5.9541%  
- **B2 median**：-9.6259%

统计检验（两独立样本，双侧）：**Mann–Whitney U**

- U = 700.0  
- p = 0.000225  

效应量（Cliff’s delta）：

- δ = 0.5556（A总体优于B2，属于中等偏强的效应）

**裁决（Primary #1）：PASS（A显著优于B2）。**

> 解读（量化视角）：在“破坏时间结构”的零假设下，系统净值劣化更明显；说明系统的确在利用时间结构产生净值差异（哪怕两组整体仍为负）。

### 2.2 Primary #2：extinction_rate（A vs B2）

- **A 灭绝率**：17/30 = 56.67%  
- **B2 灭绝率**：18/30 = 60.00%

统计检验（双侧）：**Fisher exact**

- odds ratio = 0.8718  
- p = 1.0

效应量：

- risk_diff（A-B2）= -3.33pp  
- risk_ratio（A/B2）≈ 0.944

**裁决（Primary #2）：FAIL（差异不显著，且效应量很小）。**

> 解读（量化视角）：在当前参数/选择压力下，“是否灭绝”对时间结构的敏感度不强（或被其它因素淹没）。它更像生态可持续性指标，而非“时间结构是否存在”的敏感探针。

### 2.3 Gate 1 总裁决

- Primary #1（system_roi）：✅ PASS  
- Primary #2（extinction_rate）：❌ FAIL

**Gate 1 裁决：PARTIAL PASS（存在非随机结构信号，但未在生存性指标上体现）。**

---

## 3) 结论（本轮裁决）

- **方法论“非随机性”获得硬证据（在system_roi上）**：A显著优于B2，且效应量不小。  
- **但“可持续性/生存性”并未获得支持**：灭绝率A与B2无显著差异。

因此，本轮结论应表述为：

> **系统目前能够“测到并利用”市场时间结构（净值层面），但尚不能证明这种利用能转化为更低灭绝率/更强生态可持续性。**

---

## 4) 下一步（最小改动优先）

按验收标准的顺序，下一步优先做 Gate 3（因果归因）而不是继续堆新指标：

1) **消融实验（Gate 3）**：验证“差异来自哪些观测通道”
   - 方案C-M：置空 `M`（交互阻抗）后重跑A与B2，看 `system_roi` 的 A>B2 差异是否显著减弱。
   - 方案C-C：置空 `C`（群体态）后同理。

2) **时间窗迁移（Gate 2.3）**：在两个不重叠窗口复现 A>B2（system_roi）

3) **工程改进（非策略）**：为避免未来路径混乱
   - 在 `audit_declaration` 中强制写入 `group_id`（A/B2/C-…）与数据生成方式摘要（return-shuffle参数）。

---

## 5) 复核脚本（可复制执行）

在本机执行以下脚本可复核关键统计（需要 `scipy`）：

```python
import json
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu, fisher_exact

A_path = "/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B_shuffle_30_20251221_004609/multiple_experiments_summary.json"
B2_path = "/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results/multiple_experiments_summary.json"

def load(p):
    return json.loads(Path(p).read_text())

def extract(d):
    roi = np.array([s["system_roi"] for s in d["all_stats"]], dtype=float)
    alive = np.array([s.get("alive_agents", 0) for s in d["all_stats"]], dtype=int)
    extinct = (alive == 0)
    return roi, extinct

A = load(A_path); B = load(B2_path)
A_roi, A_ext = extract(A)
B_roi, B_ext = extract(B)

mw = mannwhitneyu(A_roi, B_roi, alternative="two-sided")
cliff = ((A_roi[:,None] > B_roi[None,:]).sum() - (A_roi[:,None] < B_roi[None,:]).sum()) / (len(A_roi)*len(B_roi))

Ae, As = int(A_ext.sum()), int((~A_ext).sum())
Be, Bs = int(B_ext.sum()), int((~B_ext).sum())
odds, p = fisher_exact([[Ae, As],[Be, Bs]], alternative="two-sided")

print("system_roi mean A/B2:", A_roi.mean(), B_roi.mean())
print("system_roi median A/B2:", np.median(A_roi), np.median(B_roi))
print("Mann-Whitney U p:", mw.pvalue, "U:", mw.statistic, "Cliff delta:", cliff)
print("extinction A/B2:", Ae, "/", len(A_ext), "vs", Be, "/", len(B_ext), "Fisher p:", p, "odds:", odds)
```


