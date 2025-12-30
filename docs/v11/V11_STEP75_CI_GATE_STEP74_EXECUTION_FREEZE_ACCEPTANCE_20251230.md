# V11 Step 75 — CI Gate: Step74 Execution Freeze Acceptance (Quant) — SSOT — 2025-12-30

目的：将 Step74（Real-time Reconciliation Freeze / execution_frozen）升级为 **CI 必跑且不可回退** 的验收项，锁定：
- once frozen, always frozen
- write operations blocked（place/cancel/replace）
- evidence 落盘（errors.jsonl / reconciliation_freeze_events.jsonl）
- manifest 写实（execution_freeze section）

本文件只允许追加（additive-only）。

前置：
- Step74 SSOT：`docs/v11/V11_STEP74_REAL_TIME_RECONCILIATION_FREEZE_20251230.md`
- Step74 Quant 已实现：`tools/test_step74_execution_freeze.py`

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml` 的 `verify_step54_integration` job 尾部）：

```text
python3 tools/test_step74_execution_freeze.py
```

预期：
- exit 0 → PASS
- exit 非 0 → FAIL（阻断合并）

---

## 2) 失败语义（冻结）

- 任一断言失败 → CI FAIL（阻断合并）
- 不允许在 CI 中跳过（不得用条件判断把该测试静默跳过）

---

## 3) 最小断言（硬）

CI 必须至少证明（由 `tools/test_step74_execution_freeze.py` 覆盖）：
- Freeze manager 初始化正确（默认 not_frozen）
- `p2_overdue` 触发后：
  - `execution_frozen=true`
  - place/cancel/replace 被拒绝（fail-closed）
  - 写入 `errors.jsonl`（error_type=execution_frozen + reason_code）
  - 写入 `reconciliation_freeze_events.jsonl`（freeze_id + reason_code）
  - manifest section 生成正确（execution_freeze 写实）
- `account_restricted` 触发后同样冻结
- disabled freeze 行为写实（enabled=false 不触发冻结）

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


