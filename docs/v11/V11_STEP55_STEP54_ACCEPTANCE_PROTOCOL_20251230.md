# V11 Step 55 — Step54 Acceptance Protocol (Quant) — SSOT — 2025-12-30

目的：把 Step 54（Step53 compare 纳入 run-end/CI gates）的验收从“口头复述”冻结为**可重复执行、可机械复核**的协议与最小清单。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 53：`docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_20251230.md`
- Step 54：`docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_20251230.md`
- Evidence Gate Bundle：Step 46（Step41–45）

---

## 1) 验收对象（冻结）

Quant 仓库中 Step54 的落地应满足：
- compare 产物进入 run_dir（`run_dir/step53_compare/ablation_compare.json`）
- compare 产物被 run-end evidence packaging 递归纳入（FILELIST/SHA256SUMS/evidence_ref_index）
- manifest 写实（additive-only）
- 不可比为 WARNING（exit 0，不阻塞）但必须 reason 可见
- 工具/证据失败为 FAIL（exit 2）
- CI 有最小自动化验收（必跑）

---

## 2) 最小验收命令（冻结）

### 2.1 CI/本地测试脚本（推荐主入口）

在 Quant 运行：

```text
python3 tools/test_step54_integration.py
```

预期：
- exit code = 0
- 输出包含：
  - compare 产物生成成功
  - Step53 verifier PASS
  - evidence packaging 覆盖 `step53_compare/ablation_compare.json`

前置条件（写实）：
- 必须存在 Step51 的两次 run_dir（C_off/C_on）作为 compare 输入；否则 test 应明确失败原因（不允许静默跳过）。

---

## 3) 产物清单与断言（硬）

### 3.1 compare 产物存在性（硬）

在目标 run_dir 内必须存在：
- `step53_compare/ablation_compare.json`

且该文件可被 Step53 verifier 通过：

```text
python3 tools/verify_step53_ablation_compare.py step53_compare/ablation_compare.json
```

预期：
- exit code = 0

### 3.2 Evidence packaging 覆盖（硬）

目标 run_dir 的 evidence 包必须覆盖：
- `FILELIST.ls.txt` 包含 `step53_compare/ablation_compare.json`
- `SHA256SUMS.txt` 包含对应条目
- 当 gate-on 生成 `evidence_ref_index.json` 时，必须包含 `step53_compare/ablation_compare.json` 的索引项

---

## 4) manifest 写实断言（硬）

`run_manifest.json` 必须 additive-only 写入（不得删改旧字段）：

必含字段（键必须存在）：
- `step53_compare.enabled` (bool)
- `step53_compare.left_run_dir` (string|null)
- `step53_compare.right_run_dir` (string|null)
- `step53_compare.output_path` (string|null)
- `step53_compare.generation_status` (`pending|generated|skipped|failed`)
- `step53_compare.reason` (string|null)

硬规则：
- enabled=false → `generation_status="skipped"` 且 `reason="flag_disabled"`（或等价 reason_code）
- enabled=true 且 inputs 缺失 → `generation_status="skipped"` 且 reason 明确（例如 `missing_run_dirs`）
- enabled=true 且生成成功 → `generation_status="generated"`，reason 写实（例如 `comparability_passed` 或 `comparability_failed: ...`）
- enabled=true 且工具/证据失败 → `generation_status="failed"` 且 reason 写实（并导致 run-end gate exit 2）

---

## 5) Exit code 口径（冻结，必须一致）

与 Step53/Step54 口径一致：

- PASS → exit 0
  - compare 生成成功
  - `comparability.passed == true`

- WARNING / NOT_MEASURABLE 风格 → exit 0（但必须打印 WARNING）
  - compare 生成成功
  - `comparability.passed == false`
  - `comparability.reason` 非空

- FAIL → exit 2
  - 缺文件/解析失败/schema 必填字段缺失/hash 失败/Step53 verifier 失败

---

## 6) CI Gate（最小要求）

Quant CI 必须包含一条必跑项（任选其一）：

- 直接运行 `python3 tools/test_step54_integration.py` 并要求 PASS（exit 0）
  - 或者
- 在 CI fixture 中包含/生成一个 compare 产物，并运行 Step53 verifier PASS

若 CI 需要覆盖 WARNING 路径：
- 至少提供一种“不可比输入”的测试（不阻塞 pipeline），但必须验证：
  - compare 产物存在
  - comparability.passed=false + reason 非空
  - generate 脚本 exit 0 且打印 WARNING


