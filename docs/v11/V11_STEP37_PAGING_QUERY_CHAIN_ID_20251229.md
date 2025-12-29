# V11 Step 37 — Paging Query Chain ID (Prevent Mixed Chains) — 2025-12-29

目的：消除分页闭合证明的“混链歧义”。  
即使有 `paging_traces.jsonl` 与 `paging_coverage.line_range`，在同一 run 内多次查询同一 endpoint_family 时，仍可能出现 line_range 覆盖了不止一个查询链的记录，导致可复核性下降。

本 Step 37 通过新增 **查询链唯一键** 来做到“每个 closure proof 可唯一归属到一次查询链”，并被 verifier 强制校验。

SSOT 关联：
- Step 34 paging_traces：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP34_PAGING_TRACES_APPEND_ONLY_20251229.md`
- Step 35 gates require paging_traces：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP35_REQUIRE_PAGING_TRACES_IN_GATES_20251229.md`
- Step 36 paging_coverage：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP36_AUDITOR_PAGING_COVERAGE_FIELDS_20251229.md`

---

## 1) paging_traces.jsonl 新增字段（additive-only，冻结）

每条 paging trace 追加：
- `scope_id`：string（一次审计执行的 scope 标识；同一 run 内多次审计必须不同）
- `query_chain_id`：string（一次“分页查询链”的唯一键）

### 1.1 query_chain_id 生成规则（推荐最小）

query_chain_id 必须满足：
- 同一（endpoint_family, inst_id, time_window, scope_id）内稳定一致
- 不同查询链必然不同（避免复用）

推荐构造（示例）：
- `query_chain_id = short_hash(endpoint_family|inst_id|start_ms|end_ms|scope_id|sequence_no)`

> 注：hash 只需短哈希（例如 sha256 前 12–16 hex），目的不是加密而是稳定标识。

---

## 2) auditor_report.paging_coverage 增强（additive-only，冻结）

对每个 endpoint_family：
- 追加 `scope_id`
- 追加 `query_chain_id`

并新增硬规则：
- 若 `attempted=true` 且 `closure_proved=true`：
  - `scope_id/query_chain_id` 必须非空
  - `paging_traces_line_start/end` 指定范围内的 traces 必须：
    - 全部 `endpoint_family` 匹配
    - 全部 `scope_id` 匹配
    - 全部 `query_chain_id` 匹配

---

## 3) Verifier 硬校验（fail-closed）

当 `paging_coverage.*.closure_proved=true`：
- line_range 内若出现不同 `query_chain_id` 或不同 `scope_id` → **FAIL**
- line_range 内若缺少对应 endpoint_family 的记录 → **FAIL**

目的：让“闭合证明”不可通过“混链/拼接”绕过。


