# V11 Step 60 — Gate Compare Bundle in run-end/CI (Quant) — SSOT — 2025-12-30

目的：把 Step59 的 `compare_bundle.json` 从“可选工具产物”升级为 **run-end evidence gate + CI gate 的闭环产物**。  
原则：fact-only、可复核、fail-closed（工具/证据失败即阻断）。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 54：compare 进入 run-end evidence gate（`step53_compare/ablation_compare.json`）
- Step 59：compare bundle contract（`compare_bundle.json` + verifier）
- Step 56/58：CI gates 与 fixtures/verifier 链路

---

## 1) 目录结构（冻结）

当 Step54 启用 `--enable-step53-compare` 时：
- compare 产物目录：`run_dir/step53_compare/`
  - `ablation_compare.json`
  - `compare_bundle.json`（Step60 新增）

> 说明：优先与 Step54 复用同目录，避免证据分叉与漏打包。

---

## 2) run-end gate 行为（硬）

当 compare 生成成功后（无论 comparability PASS/FAIL）：
1) 生成 `compare_bundle.json`
   - 调用 `tools/generate_step59_compare_bundle.py <step53_compare_dir>`
2) 校验 `compare_bundle.json`
   - 调用 `tools/verify_step59_compare_bundle.py <path_to_compare_bundle.json>`
3) evidence packaging 必须覆盖：
   - `FILELIST.ls.txt`
   - `SHA256SUMS.txt`
   - `evidence_ref_index.json`（gate-on）
   - 必须包含：`step53_compare/compare_bundle.json`

---

## 3) 失败语义（冻结）

### 3.1 Step59 生成/验证失败（硬）

以下任一情况 → FAIL（exit 2）：
- compare_bundle 生成脚本输入缺失/解析失败/sha256 计算失败（exit 2）
- compare_bundle verifier schema 缺失或 evidence refs 不合规（exit 1）
- compare_bundle 文件不存在或无法纳入证据包（FILELIST/SHA256SUMS/evidence_ref_index 缺失）

### 3.2 NOT_MEASURABLE 风格（必须保留）

`comparability.passed == false` 不应导致 fail：
- compare_bundle 仍必须生成（exit 0）
- bundle 内必须写实 `comparability.reason`

---

## 4) CI 最小要求（建议）

在 Step56 gate 链路中，建议新增一项断言（可与 Step54 integration test 同一脚本或新增 test）：
- 生成 compare 后，必须存在 `compare_bundle.json`
- `verify_step59_compare_bundle.py` 必须 PASS
- evidence packaging 覆盖 `step53_compare/compare_bundle.json`

---

## 5) Quant 交付物（冻结）

Quant 最小改动集：
- runner/run-end gate 在 Step54 compare 成功后串联 Step59 生成与验证
- 把 compare_bundle 纳入 evidence packaging
- CI gate（可选本 step 完成，但推荐同 PR 一并加）

Research 侧：
- 本 SSOT
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录


