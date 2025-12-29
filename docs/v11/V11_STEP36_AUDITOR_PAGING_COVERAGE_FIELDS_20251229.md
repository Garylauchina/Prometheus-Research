# V11 Step 36 — Auditor Paging Coverage Fields (Freeze, Non-bypassable Proof) — 2025-12-29

目的：把 Step 34/35 的 `paging_traces.jsonl` 从“存在即可”提升为 **可量化的闭合证明**：  
在 `auditor_report.json` 冻结分页闭合覆盖率字段，使审计可以回答：
- 我们拉取了多少页？
- 是否证明闭合？闭合依据是什么？
- paging_traces 的证据范围在哪里（行号范围）？

背景：  
如果不冻结覆盖率字段，理论上可能出现“写了几条 paging_traces 但未覆盖全链”而仍宣称闭合的漏洞。

SSOT 关联：
- Step 34 Spec：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP34_PAGING_TRACES_APPEND_ONLY_20251229.md`
- Step 35 Spec：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP35_REQUIRE_PAGING_TRACES_IN_GATES_20251229.md`

---

## 1) auditor_report.json 新增字段（additive-only，冻结）

在 `auditor_report.json` 顶层或 `audit_scope` 下新增（推荐顶层 `paging_coverage`）：

`paging_coverage`（object）：
- `orders_history`（object）
- `fills`（object）
- `bills`（object）

每个 endpoint_family 的 object 必须包含：
- `attempted`：bool（本次审计是否尝试查询该端点）
- `page_count`：int（实际请求页数；至少 0）
- `closure_proved`：bool（是否证明闭合）
- `closure_rule`：string（例如 `has_more_false` / `cursor_exhausted` / `unknown`）
- `last_has_more`：bool|null（最后一页的 hasMore；若端点不提供则为 null）
- `last_cursor`：string|null（最后一页游标/after/before；若无则 null）
- `paging_traces_present`：bool（run_dir 是否存在 paging_traces.jsonl）
- `paging_traces_line_start`：int|null（1-based）
- `paging_traces_line_end`：int|null（1-based，>= start）
- `not_measurable_reasons`：list[string]（若 closure_proved=false，必须给出原因）

硬规则：
- 若 `attempted=true`，则 `page_count >= 1`（否则矛盾）
- 若 `closure_proved=true`，则 `paging_traces_present=true` 且 line_start/line_end 必须非空

---

## 2) 裁决口径（honest reporting）

### 2.1 单端点 closure 结论

- PASS：`attempted=true` 且 `closure_proved=true`
- NOT_MEASURABLE：`attempted=true` 且 `closure_proved=false`（并给出 reasons）
- N/A：`attempted=false`（不参与本次结论；不得被误报为 PASS）

### 2.2 与 Step 33（P3/P4）关系

当 Step 33 启用 P3/P4 时：
- fills closure 若 NOT_MEASURABLE → fills join 相关结论必须 NOT_MEASURABLE（不得 PASS）
- bills closure 若 NOT_MEASURABLE → bills join 相关结论必须 NOT_MEASURABLE（不得 PASS）

---

## 3) Gate/Verifier 最小校验（建议）

在 verifier 中新增一致性校验：
- 若 `auditor_report.paging_coverage.fills.attempted=true`：
  - 必须存在 `paging_traces.jsonl`
  - 且 line range 对应 traces 中至少包含 endpoint_family=fills 的记录
- 同理对 bills/orders_history

若不满足 → FAIL（用于 CI 与 run-end gate fail-closed）


