# V10 验收裁决摘要（消融）：C 消融（C={}/置零）下 A vs B2 — 2025-12-21

本文件用于执行 `docs/v10/V10_ACCEPTANCE_CRITERIA.md` 的 **G0.6 / G3.3（Prior leakage）**。  
目标：验证此前 A>B2 的 `system_roi` 差异是否依赖 **C 通道**（群体态/生态反馈）——若依赖，应在 C 消融后显著退化或消失。

---

## 0) 需要从 Quant 回传的两条证据路径（必须填）

- **A组（真实时间结构 + C消融）**：`<PASTE_PATH_TO_A_SUMMARY_JSON>`
- **B2组（打乱log-return重建价格 + C消融）**：`<PASTE_PATH_TO_B2_SUMMARY_JSON>`

同时回传（或在summary里能读到）：

- seeds 列表（或可复现的 seed 生成方式）
- 数据文件与时间窗（CSV路径/起止时间）
- `audit_declaration.ablation` 值（应为 `C_zeroed` 或等价声明）

---

## 1) Gate 0（只看“尺子是否干净”）

- **G0.3 数值健康**：`PASS/FAIL`（NaN/Inf/爆炸即Fail）
- **G0.5 对照物理合理**：`PASS/FAIL`（B2构造是否仍物理合理）
- **G0.6 Prior leakage audit**：`PASS/FAIL`
  - 证据：确认本轮唯一变化是 `C` 被置空/置零；核心逻辑未改；summary里声明了ablation。

---

## 2) Gate 1（Primary endpoints，A vs B2）

> 本轮仍按锁定的两个主指标裁决：`system_roi` 与 `extinction_rate`。

### 2.1 Primary #1：system_roi（基于 current_total）

- A：mean=<TBD> median=<TBD>（可补分位数）
- B2：mean=<TBD> median=<TBD>

统计检验（建议）：Mann–Whitney U（双侧）

- U=<TBD>
- p=<TBD>
- Cliff’s delta δ=<TBD>

**裁决（Primary #1）：PASS/FAIL（判定“是否退化/是否仍A显著优于B2”）**

### 2.2 Primary #2：extinction_rate

- A：extinct=<TBD>/<TBD> rate=<TBD>
- B2：extinct=<TBD>/<TBD> rate=<TBD>

统计检验（建议）：Fisher exact（双侧）

- odds=<TBD>
- p=<TBD>
- risk_diff(A-B2)=<TBD>

**裁决（Primary #2）：PASS/FAIL**

---

## 3) Gate 3（Prior leakage 消融裁决：核心结论）

对照“未消融基线”的裁决记录：

- 基线文件：`docs/v10/V10_ACCEPTANCE_DECISION_A_vs_B2_20251221.md`

### 3.1 预期（写死的判读逻辑）

- 若此前 A>B2 的差异主要由 **C 通道**承载：  
  C 消融后 `system_roi` 的 A>B2 应**显著减弱或消失**（p变大、效应量显著变小，甚至方向不稳定）。
- 若 C 消融后 A>B2 依旧强且稳定：  
  说明时间结构信号主要来自 **非C通道**（E/I/M 或纯价格结构），或存在其它“隐含预设”未被本消融覆盖（需要继续拆解）。

### 3.2 本轮裁决（TBD）

- **结论**：通过 / 不通过 / 证据不足
- **一句话解释（人话）**：<TBD>

---

## 4) 复核脚本（拿到两条路径后可直接跑）

```python
import json
import numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu, fisher_exact

A_path = "<PASTE_PATH_TO_A_SUMMARY_JSON>"
B2_path = "<PASTE_PATH_TO_B2_SUMMARY_JSON>"

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


