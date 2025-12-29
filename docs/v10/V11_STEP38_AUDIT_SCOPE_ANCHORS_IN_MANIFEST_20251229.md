# V11 Step 38 — Audit Scope Anchors in run_manifest (Freeze, Non-drifting) — 2025-12-29

目的：把“本次审计到底审了什么范围”从隐含逻辑升级为 **run-level 可复核锚点**。  
解决的问题：即使 Step 34–37 已经把 paging closure proof 做到不可绕过，如果 `audit scope`（inst_id/time_window/prefix）不写入 `run_manifest.json`，仍可能发生“同名审计，但范围漂移”导致结论不可比。

SSOT 关联：
- Step 32–33（orphan + fills/bills join）
- Step 34–37（paging_traces + paging_coverage + query_chain_id/scope_id）

---

## 1) run_manifest.json 新增字段（additive-only，冻结）

在 `run_manifest.json` 顶层新增 `audit_scope`（object）：

- `audit_scope_id`：string（推荐等于 auditor 的 `scope_id`；同一 run 内若多次审计，应写 `audit_scopes[]` 追加记录）
- `auditor_contract_version`：string（例如 `V11_EXCHANGE_AUDITOR_...`）
- `auditor_schema_version`：string
- `clOrdId_namespace_prefix`：string（例如 `v11_`，用于 in-scope 过滤）
- `inst_id`：string（例如 `BTC-USDT-SWAP`；若多 inst，写数组）
- `time_window_ms`：object
  - `start_ms`：int
  - `end_ms`：int
- `endpoints_attempted`：list[string]（`orders_history|fills|bills`）
- `artifacts`：object（可选但推荐）
  - `auditor_report_path`：string
  - `auditor_discrepancies_path`：string
  - `paging_traces_path`：string

硬规则：
- `audit_scope_id` 不得缺失（若本 run 声称执行过 auditor）
- `inst_id/time_window_ms/prefix` 缺失 → 该 run 的审计结论不得与其他 run 对比（必须标注 NOT_MEASURABLE for “comparability”）

---

## 2) 一致性要求（hard）

当 `audit_scope` 存在时：
- `audit_scope.audit_scope_id` 必须与 `auditor_report.scope_id`（或等价字段）一致
- `audit_scope.inst_id` 与 auditor 实际查询的 inst_id 必须一致（或为 superset）
- `audit_scope.time_window_ms` 必须与 paging_traces 内的 time_window 一致（或为 superset，且必须写明包含关系）

若不一致：
- verifier 应 FAIL（用于 CI/run-end gate）

---

## 3) 实现要求（Quant）

实现仓库需要：
- runner 在 run_end 落盘前将 `audit_scope` 写入 `run_manifest.json`（additive-only）
- auditor_report 内必须包含同等 scope 信息（或能回指 manifest 的 audit_scope_id）
- verifier 可追加校验（建议）：
  - manifest.audit_scope 与 auditor_report/paging_traces 的一致性


