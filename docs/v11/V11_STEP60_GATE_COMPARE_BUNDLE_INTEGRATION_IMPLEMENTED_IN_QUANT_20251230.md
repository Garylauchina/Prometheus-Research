# V11 Step 60 — Gate Compare Bundle in run-end/CI — Implemented in Quant — 2025-12-30

目的：记录 Step60 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP60_GATE_COMPARE_BUNDLE_INTEGRATION_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step60 gate compare_bundle in run-end evidence chain`
- **Commit (short)**: `d2305e9`
- **Commit (full)**: `d2305e93a5bd334653f4d596a4f854bcefdcdfaa`

修改文件（Quant）：
- `prometheus/v11/ops/run_v11_service.py`
- `tools/test_step54_integration.py`

---

## 2) 串联位置与目录结构（事实）

串联位置（写实）：
- 在 Step54 compare 生成成功分支中，自动调用 Step59：
  - 生成 `compare_bundle.json`
  - 验证 `compare_bundle.json`

目录结构（冻结实现）：
- `run_dir/step53_compare/`
  - `ablation_compare.json`（Step53）
  - `compare_bundle.json`（Step60）

---

## 3) run-end 失败语义（事实）

任一步骤失败（生成或验证）：
- 在 manifest 中标记 `step53_compare.generation_status='failed'`
- `reason` 写实（例如 `bundle_generate_exit_2` / `bundle_verify_failed_exit_1` / timeout 等）

NOT_MEASURABLE 风格保留（事实）：
- `comparability.passed=false` 不阻断 compare 与 bundle 的生成（exit 0），但必须写实 reason

---

## 4) Evidence packaging 覆盖（事实）

由于 Step54 已实现 run_dir 递归打包，`step53_compare/compare_bundle.json` 被自动纳入：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`（gate-on）

---

## 5) CI/测试覆盖（事实）

Quant 扩展了：
- `tools/test_step54_integration.py`

新增断言（最小）：
- `compare_bundle.json` 生成成功
- `compare_bundle.json` 存在
- `verify_step59_compare_bundle.py` PASS
- `FILELIST.ls.txt` 包含 `step53_compare/compare_bundle.json`


