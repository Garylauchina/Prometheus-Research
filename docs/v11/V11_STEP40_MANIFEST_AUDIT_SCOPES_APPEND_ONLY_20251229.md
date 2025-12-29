# V11 Step 40 — run_manifest.audit_scopes[] (Append-only, Multi-audit Safe) — 2025-12-29

目的：把“同一 run 内多次审计/多 inst 审计”的范围记录从单一字段升级为 **append-only 列表**，避免后写覆盖前写导致丢历史、不可复核。

背景：
- Step 38 引入 `run_manifest.audit_scope`（单一对象）
- Step 39 引入 `audit_scope_id` 全链路 join
当同一 run 出现多次审计（例如周期末 + 额外补审、或多 inst），单对象会被覆盖，证据链不再可线性追踪。

SSOT 关联：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP38_AUDIT_SCOPE_ANCHORS_IN_MANIFEST_20251229.md`
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP39_AUDIT_SCOPE_ID_AS_GLOBAL_ANCHOR_20251229.md`

---

## 1) run_manifest.json 新增字段（additive-only）

新增顶层数组：
- `audit_scopes`：list[object]（append-only，顺序=发生顺序）

每个元素（最小字段集）：
- `audit_scope_id`：string（全局主锚点）
- `auditor_contract_version`：string
- `auditor_schema_version`：string
- `clOrdId_namespace_prefix`：string（例如 `v11_`）
- `inst_id`：string 或 list[string]
- `time_window_ms`：{ start_ms:int, end_ms:int }
- `endpoints_attempted`：list[string]（orders_history|fills|bills）
- `artifacts`（推荐）：{ auditor_report_path, auditor_discrepancies_path, paging_traces_path }
- `ts_utc_start` / `ts_utc_end`（推荐）

硬规则：
- **append-only**：同一 run 内不得覆盖/修改既有元素，只能追加新元素。
- `audit_scope_id` 在数组内必须唯一；重复视为 FAIL（实现或 verifier）。

---

## 2) 兼容策略（向后兼容）

为兼容旧 run 或单次审计：
- 允许保留 `audit_scope`（单对象）作为 legacy 镜像
- 当 `audit_scopes[]` 存在时：
  - `audit_scope`（若存在）必须等于 `audit_scopes[-1]`（最后一次审计的镜像），否则 FAIL/NOT_MEASURABLE（按 gate 策略）

---

## 3) Verifier / gates 最小校验（建议冻结）

当检测到审计产物存在（auditor_report / paging_traces / discrepancies）：
- 必须能在 `audit_scopes[]` 中找到对应 `audit_scope_id`
- `audit_scope_id` 在 arrays 中必须唯一
- `audit_scopes[].artifacts` 路径必须存在于 FILELIST/SHA256 覆盖范围内（避免证据盲区）

不满足：
- CI / run-end gate 必须 fail-closed（exit!=0）


