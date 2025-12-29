# V11 Step 46 — Evidence Gate Bundle Freeze Implemented in Quant — 2025-12-29

目的：记录 Step 46（Evidence Gate Bundle 冻结：bundle 版本化 + fixtures 套件冻结 + exit code 语义冻结 + 必需产物清单）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点与验收事实（含 SHA）。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`022b366`
- Quant commit（完整）：`022b366f9ab03b6c3a89c2484e16d1057944ea64`
- message：`v11: Step46 freeze evidence gate bundle (version+fixtures+exit codes)`

---

## 2) 落地摘要（用户验收事实）

修改文件：
- `tools/verify_step26_evidence.py`：新增 bundle 常量与输出
- `prometheus/v11/ops/run_v11_service.py`：run-end gate 写入 manifest.evidence_gate 的 bundle 信息
- `tools/ci_test_evidence_gate_bundle.py`：新增 CI 套件（冻结 fixtures 行为）

Bundle Machine-Readable 输出（实现侧）：
- `bundle_name`: `V11_EVIDENCE_GATE_BUNDLE_20251229`
- `bundle_version`: `2025-12-29.1`
- `bundle_steps_included`: `[41, 42, 43, 44, 45]`
- `verifier_commit_sha`: 写入 `run_manifest.evidence_gate`

Exit code 语义（实现侧冻结）：
- verifier：PASS=0 / FAIL=1 / ERROR=2
- run-end gate：PASS=0 / FAIL=2（保持既有约定）

Frozen fixtures（实现侧冻结）：
- PASS：`tests/fixtures/step26_min_run_dir/`
- FAIL：`tests/fixtures/step44_fail_run_id_mismatch/`
- FAIL：`tests/fixtures/step45_fail_mixed_query_chain/`
- FAIL：`tests/fixtures/step45_fail_mixed_endpoint/`

CI：新增脚本对上述 4 个 fixture 行为做不可绕过回归验证，并通过。


