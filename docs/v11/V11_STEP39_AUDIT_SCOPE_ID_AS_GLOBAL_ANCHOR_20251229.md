# V11 Step 39 — audit_scope_id as Global Anchor (Cross-file Evidence Join) — 2025-12-29

目的：把 `audit_scope_id` 升级为审计链路的**全局主锚点**（global join key），让审计证据可以跨文件、跨模块稳定回指与复核，消除“同一 run 内多次审计/多 inst 导致的证据碎片化”。

背景：  
Step 34–38 已解决分页闭合 proof、覆盖率、混链、防范围漂移，但若缺少统一主锚点，仍可能出现：
- auditor_report 与 paging_traces/discrepancies 之间无法一键 join（只能靠文件名/行号猜）
- 同一 run 多次审计的证据混在一起（比较困难）

SSOT 关联：
- Step 38（manifest audit_scope anchors）：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP38_AUDIT_SCOPE_ANCHORS_IN_MANIFEST_20251229.md`
- Step 34–37（paging traces + coverage + query_chain）：相关 Step 文档

---

## 1) 必须写入 audit_scope_id 的证据文件（冻结）

当 run 执行 ExchangeAuditor（或等价审计）时，下列文件**每条记录**必须携带：
- `auditor_report.json`：顶层字段 `audit_scope_id`
- `auditor_discrepancies.jsonl`：每行字段 `audit_scope_id`
- `paging_traces.jsonl`：每行字段 `audit_scope_id`（可等于 `scope_id`，但字段名统一为 `audit_scope_id` 用于 join）

建议（但强烈推荐）：
- `errors.jsonl`：若错误与审计相关（paging incomplete / proof missing / verifier fail），必须带 `audit_scope_id`
- `run_manifest.json`：`audit_scope.audit_scope_id` 必须存在，并回指审计产物路径

硬规则：
- 同一 run 内可以有多个 `audit_scope_id`（多次审计），但每条记录必须明确属于哪一个 scope。

---

## 2) 一致性规则（hard）

在同一 run_dir 内：
- `run_manifest.audit_scope.audit_scope_id` 必须与 `auditor_report.audit_scope_id` 一致
- `auditor_discrepancies.jsonl` 与 `paging_traces.jsonl` 中的 `audit_scope_id` 必须能在 `auditor_report.audit_scope_id` 集合中找到匹配

若出现“同一 scope 的文件缺少 audit_scope_id / 或出现未知 audit_scope_id”：
- verifier 必须 FAIL（用于 CI 与 run-end gate fail-closed）

---

## 3) Verifier/gates 的最小校验项（建议冻结）

当检测到 run_dir 存在 `auditor_report.json`：
- 必须存在 `audit_scope_id`
- 若存在 `auditor_discrepancies.jsonl` 或 `paging_traces.jsonl`：
  - 必须能按 `audit_scope_id` join 到 auditor_report（或 manifest.audit_scope）

---

## 4) 兼容策略（additive-only）

为避免破坏旧 run：
- 若旧 run 缺少 `audit_scope_id`，可以把该类结论标记为 NOT_MEASURABLE（comparability downgrade），但不得误报 PASS。


