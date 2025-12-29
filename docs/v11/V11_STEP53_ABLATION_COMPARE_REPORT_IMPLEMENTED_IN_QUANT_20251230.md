# V11 Step 53 — Ablation Compare Report — Implemented in Quant — 2025-12-30

目的：记录 Step 53 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step53 add ablation_compare.json (fact-only cross-run report)`
- **Commit (short)**: `5e3ae71`
- **Commit (full)**: `5e3ae71f469b00f23718fab0be12f0e30bf343fc`

新增文件（Quant）：
- `tools/generate_ablation_compare.py`
- `tools/verify_step53_ablation_compare.py`
- `runs_step53/compare_20251229_181909/ablation_compare.json`（示例产物）

---

## 2) 产物与复核入口（事实）

生成命令（示例）：

```text
python3 tools/generate_ablation_compare.py \
  runs_step51/step51_C_off_20251229_172513 \
  runs_step51/step51_C_on_20251229_172518
```

输出路径（示例）：
- `runs_step53/compare_20251229_181909/ablation_compare.json`

输入 run（示例）：
- left: `runs_step51/step51_C_off_20251229_172513/ablation_summary.json`
- right: `runs_step51/step51_C_on_20251229_172518/ablation_summary.json`

---

## 3) 可比性检查（事实）

Quant 工具实现了 Step50 的“控制变量法”检查：
- 检查 `ablation_experiment` 除 `variant` 外字段一致
- 检查 `feature_contract_version` 一致
- 检查 `evidence_gate_bundle`（bundle_name/bundle_version/steps_included）一致

不满足时：
- `comparability.passed=false`
- `comparability.reason` 给出原因
- 仍可生成产物，但必须明确标记不可比（用于离线复核/CI 策略可选）

---

## 4) Diff（事实差异统计，NO interpretation）

Quant 产物包含（事实字段）：
- `diff.decision_intent_counts_total_diff`（open/close/hold/total 的 delta）
- `diff.c_probe_stats`（mask_1_count + min/max 对比）

禁止项（符合 SSOT）：
- 不输出 ROI/因果推断/策略好坏判断等“结论性文本”

---

## 5) 验收脚本（事实）

脚本：
- `python3 tools/verify_step53_ablation_compare.py <path_to_ablation_compare.json>`

验收维度（4 项）：
- Schema completeness
- Comparability check
- Diff facts（无解释）
- Evidence refs（与 Step46 bundle 规则一致）

---

## 6) 已知对齐建议（记录，不改变 Step53 SSOT）

以下为“口径一致性建议”，用于后续 Quant 小修正，避免工具口径漂移：

- **Exit code 语义建议**：将 “不可比（comparability.passed=false）” 作为 `WARNING` 而非默认阻塞（更贴近 V11 baseline 的 NOT_MEASURABLE 风格：不阻塞 pipeline，但必须明确标记 reason）。
- **checked_fields 输出建议**：去重并固定顺序，减少无意义 diff 噪声。


