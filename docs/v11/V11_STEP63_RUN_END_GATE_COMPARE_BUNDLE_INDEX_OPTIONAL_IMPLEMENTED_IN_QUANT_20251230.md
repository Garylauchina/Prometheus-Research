# V11 Step 63 — Run-End Gate Optional: Compare Bundle Index — Implemented in Quant — 2025-12-30

目的：记录 Step63 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP63_RUN_END_GATE_COMPARE_BUNDLE_INDEX_OPTIONAL_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step63 run-end gate optional compare_bundle_index`
- **Commit (short)**: `07c620c`
- **Commit (full)**: `07c620c3c594ea3529f8bbbafffed8fd80f894f4`

修改文件（Quant）：
- `prometheus/v11/ops/run_v11_service.py`
- `tools/test_step63_integration.py`

---

## 2) CLI/开关（事实）

新增：
- `--enable-step63-index`（默认 false）
- `--step63-scan-root <path>`（enabled=true 时必需）

---

## 3) Manifest 记录（事实 / additive-only）

新增对象（字段冻结）：
- `step63_compare_bundle_index`
  - `enabled`
  - `scan_root`
  - `output_file`
  - `generate_exit_code`
  - `verify_exit_code`
  - `bundle_count`
  - `status`（`pass|fail|skipped`）

样例（PASS/FAIL/SKIPPED）已在 Quant 集成测试覆盖。

---

## 4) 失败语义（事实）

当 `enabled=true`：
- generate / verify / bundle_count<1 任一失败 → run-end gate **exit 2（fail-closed）**
- 同时写入 `errors.jsonl`，并在 manifest 标记失败状态（例如 `manifest.status = "step63_index_failed"`）

当 `enabled=false`：
- `status="skipped"`，不影响既有 gate 行为。

---

## 5) Evidence 集成（事实）

Step63 成功生成的 `compare_bundle_index.json` 会被自动纳入：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`


