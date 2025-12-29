# V11 Step 64 — CI Gate: Step63 Acceptance (Quant) — SSOT — 2025-12-30

目的：将 Step63（run-end gate optional compare_bundle_index）从“可用功能”升级为 **CI 必跑且不可回退** 的验收项，防止未来改动破坏 fail-closed / manifest / evidence packaging 语义。

本文件只允许追加（additive-only）。

前置：
- Step 63 SSOT：`docs/v11/V11_STEP63_RUN_END_GATE_COMPARE_BUNDLE_INDEX_OPTIONAL_20251230.md`
- Step 63 Quant 已实现：`tools/test_step63_integration.py`

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml`）：

```text
python3 tools/test_step63_integration.py
```

预期：
- exit 0 → PASS
- 非 0 → FAIL（阻断合并）

---

## 2) 失败语义（冻结）

- 任何断言失败（PASS/FAIL/SKIPPED 任一场景不符合契约）→ CI FAIL
- 不允许在 CI 中跳过（不得用条件判断把该测试静默跳过）

---

## 3) 最小断言（硬）

CI 必须至少证明（由 `tools/test_step63_integration.py` 覆盖）：
- enabled=true PASS：生成 index、verify PASS、bundle_count>=1、manifest 字段写实
- enabled=true FAIL：scan_root 不存在 → exit 2（fail-closed）且 manifest/status/errors 记录正确
- enabled=false SKIPPED：不影响既有 gate 行为，manifest.status=skipped

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


