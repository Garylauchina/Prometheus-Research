# V10 验收裁决摘要（消融）：M 消融（M={}/置零）下 A vs B2 — 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **G0.6 / G3.3（Prior leakage）**。  
目标：验证此前 A>B2 的 `system_roi` 差异是否依赖 **M 通道**（交互阻抗/摩擦建模）——若依赖，应在 M 消融后显著退化或消失。

---

## 0) 需要从 Quant 回传的两条证据路径（必须填）

- **A组（真实时间结构 + M消融）**：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_30__ablation_M_zeroed__20251221_015927/multiple_experiments_summary.json`
- **B2组（打乱log-return重建价格 + M消融）**：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_30__ablation_M_zeroed__20251221_020620/multiple_experiments_summary.json`

同时回传（或在summary里能读到）：

- seeds 列表（或可复现的 seed 生成方式）
- 数据文件与时间窗（CSV路径/起止时间）
- `audit_declaration.ablation` 值（应为 `M_zeroed` 或等价声明）

---

## 1) Gate 0（只看“尺子是否干净”）

- **G0.3 数值健康**：**PASS**
  - 证据：两组均 `has_nan=false, has_inf=false, has_explosion=false`
- **G0.5 对照物理合理**：**PASS**
  - 证据：B2 明确声明 `null_hypothesis=shuffle_log_returns_rebuild_price`（收益率打乱后重建价格），无非物理跳变爆炸
- **G0.6 Prior leakage audit**：**PASS**
  - 证据：`audit_declaration.ablation="M_zeroed"`，A为 `group_id="A_real"`，B2为 `group_id="B2_shuffle_returns"`；且本轮输出未出现爆炸迹象（有利于审计一致性）

---

## 2) Gate 1（Primary endpoints，A vs B2）

> 本轮仍按锁定的两个主指标裁决：`system_roi` 与 `extinction_rate`。

### 2.1 Primary #1：system_roi（基于 current_total）

- A：mean = **-9.781%**，median = **-8.262%**，IQR = [**-11.984%**, **-6.953%**]
- B2：mean = **-12.650%**，median = **-12.339%**，IQR = [**-14.359%**, **-10.698%**]

统计检验（建议）：Mann–Whitney U（双侧）

- U = **687.0**
- p = **0.000471**
- Cliff’s delta δ = **0.5267**（A总体优于B2，中等偏强效应）

**裁决（Primary #1）：PASS（A仍显著优于B2）**

### 2.2 Primary #2：extinction_rate

- A：extinct = **21/30**，rate = **70.0%**
- B2：extinct = **23/30**，rate = **76.7%**

统计检验（建议）：Fisher exact（双侧）

- odds = **0.7101**
- p = **0.7710**
- risk_diff(A-B2) = **-6.67pp**（A略低，但不显著）

**裁决（Primary #2）：FAIL（差异不显著）**

---

## 3) Gate 3（Prior leakage 消融裁决：核心结论）

对照“未消融基线”的裁决记录：

- 基线文件：`docs/v10/V10_ACCEPTANCE_DECISION_A_vs_B2_20251221.md`

### 3.1 预期（写死的判读逻辑）

- 若此前 A>B2 的差异主要由 **M 通道**承载：  
  M 消融后 `system_roi` 的 A>B2 应**显著减弱或消失**（p变大、效应量显著变小，甚至方向不稳定）。
- 若 M 消融后 A>B2 依旧强且稳定：  
  说明时间结构信号主要来自 **非M通道**（E/I/C 或纯价格结构），或存在其它“隐含预设”未被本消融覆盖（需要继续拆解）。

### 3.2 本轮裁决（TBD）

- **结论**：**通过（对“M通道存在 prior leakage”的担忧显著降低）**
- **一句话解释（人话）**：把 M 维度拿掉后，A 依旧显著优于 B2，说明此前的“时间结构优势”**不是主要靠 M 通道的先验建模撑起来的**；下一步应继续做 **C消融**（以及必要时审计其它硬规则/默认值），把怀疑面进一步缩小。

---

## 4) 复核脚本（拿到两条路径后可直接跑）

```python
import json
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu, fisher_exact

A_path = "/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_30__ablation_M_zeroed__20251221_015927/multiple_experiments_summary.json"
B2_path = "/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_30__ablation_M_zeroed__20251221_020620/multiple_experiments_summary.json"

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


