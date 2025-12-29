# V11 Step 54 — Integrate Step53 into Evidence Gates (Quant) — SSOT — 2025-12-30

目的：把 Step 53 的 `ablation_compare.json` 从“可选工具产物”升级为**可复核闭环的一部分**：当我们声明做了对照/消融比较时，它必须被 run-end evidence gate/CI gate 自动生成与自动复核（或明确标记未启用）。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 46：Evidence Gate Bundle（evidence_refs 可复核规则）
- Step 50：ablation_experiment 模板（控制变量法）
- Step 51：ablation_summary.json（单 run 事实统计）
- Step 53：ablation_compare.json（跨 run 事实差异对照）

---

## 1) 范围（冻结）

本 Step 只涉及 **Prometheus-Quant** 的 gate/runner 集成与 CI fixture 扩展：
- run-end evidence gate：把 compare 产物纳入打包与校验
- CI gate：增加最小 fixture（或在现有 fixture 上扩展）验证 compare 产物的 schema 与可复核性

注意：
- Step 54 不引入任何新的比较指标，不改变 Step 53 schema。
- Step 54 不要求每次 run 都生成 compare；它是 **可选开关**，但必须“写实、可审计”。

---

## 2) 开关与行为（冻结）

### 2.1 开关（推荐实现之一）

Runner（或 run-end gate）提供一个开关，使 compare 生成可控且可审计：

- `--enable-step53-compare`（bool）
- `--compare-left-run-dir <path>`
- `--compare-right-run-dir <path>`
- `--compare-output-dir <path>`（可选，默认 `runs_step53/compare_<timestamp>`）

> 也允许通过 `run_manifest.ablation_experiment` 中的 `compare_inputs` 明确输入，但必须保证可复核与路径稳定。

### 2.2 运行写实（必须）

`run_manifest.json` 必须写入（additive-only）：
- `step53_compare.enabled`: bool
- `step53_compare.left_run_dir`: string|null
- `step53_compare.right_run_dir`: string|null
- `step53_compare.output_path`: string|null
- `step53_compare.generation_status`: `generated` / `skipped` / `failed`
- `step53_compare.reason`: string|null（例如 `flag_disabled`, `missing_inputs`, `schema_fail`）

---

## 3) Gate 规则（硬，必须对齐 Step53 口径）

当 `step53_compare.enabled==true`：

必须执行：
1) 生成 `ablation_compare.json`（调用 Step53 工具）
2) 运行 `verify_step53_ablation_compare.py` 对产物做最小验收
3) 把 compare 目录纳入 evidence packaging：
   - `FILELIST.ls.txt`
   - `SHA256SUMS.txt`
   - `evidence_ref_index.json`（如 gate-on）

### 3.1 Exit codes（冻结）

本 Step 继承 Step53 已收敛的口径（避免阻塞误用）：

- **PASS → exit 0**
  - compare 产物生成成功
  - `comparability.passed == true`

- **WARNING / NOT_MEASURABLE 风格 → exit 0（但必须打印 WARNING）**
  - compare 产物生成成功
  - `comparability.passed == false`
  - 必须在 compare 产物中写明 `reason`

- **FAIL（工具/证据链失败）→ exit 2**
  - 输入缺失、JSON 解析失败、schema 必填字段缺失、sha256 计算失败
  - 产物不存在或无法被 verifier 复核

> 说明：不可比不是“失败”，但必须可观测（WARNING + reason），用于后续调查。

### 3.2 Evidence refs（硬）

`ablation_compare.json.evidence_refs` 必须至少回指两份 `ablation_summary.json`，并满足 Step46 的可复核规则（在 gate-on 下由 verifier 或 bundle 校验）。

---

## 4) CI 最小验收（Quant 必须达成）

必须提供最小 CI 断言：
- 能在 fixture 目录中生成（或携带）一份 `ablation_compare.json`
- 运行 `verify_step53_ablation_compare.py` 返回 PASS（exit 0）
- 对于不可比 fixture：verify 仍 PASS（结构合格），但 compare 工具必须打印 WARNING，且 comparability.passed=false + reason 非空

---

## 5) 交付物清单（冻结）

Quant 侧交付物（最小）：
- gate/runner 集成（可选开关 + manifest 写实）
- compare 产物纳入 `FILELIST/SHA256SUMS/evidence_ref_index`
- CI fixture 与 workflow 扩展（最小一条）

Research 侧交付物：
- 本 SSOT 文档
- 一份 “Implemented in Quant” 记录文档（在 Quant 合入后补）


