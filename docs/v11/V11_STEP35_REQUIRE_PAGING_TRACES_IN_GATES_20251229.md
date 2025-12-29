# V11 Step 35 — Require paging_traces.jsonl in Gates (Verifier / Run-end / CI) — 2025-12-29

目的：把 Step 34 已落地的 `paging_traces.jsonl` 从“可选日志”升级为 **硬证据**：  
凡是声称 P3/P4（fills/bills）分页闭合与 join 可测（Step 33），就必须提供 paging_traces 作为 closure proof，并被 gates 强制验证，避免“实现写了 trace 但 gate 不看 → 仍可绕过”。

SSOT 关联：
- Step 33（P3/P4 可测）：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP33_FILLS_BILLS_JOIN_MIN_MEASURABLE_20251229.md`
- Step 34（paging traces 规范）：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP34_PAGING_TRACES_APPEND_ONLY_20251229.md`

---

## 1) Gate 适用范围（冻结）

当且仅当 run 宣称/启用以下任一能力时，必须强制要求 paging_traces：
- ExchangeAuditor 执行了 fills/bills 查询（P3/P4）
- 或 auditor_report 声称 fills/bills paging closure 为 PASS（可测）
- 或 run_manifest/auditor_scope 指明启用了 P3/P4 检查

---

## 2) Gate 硬要求（缺失即不可通过）

对满足 §1 的 run：

### 2.1 证据包文件硬要求

run_dir 必须包含：
- `paging_traces.jsonl`（append-only）
- 并纳入 `FILELIST.ls.txt` 与 `SHA256SUMS.txt`

### 2.2 语义硬要求（proof）

必须能在 paging_traces 中找到本次审计范围内的查询链：
- `endpoint_family in {fills, bills}`（以及必要时 orders_history）
- 对每条查询链：能证明闭合（has_more=false 或游标耗尽等价条件）

若 paging_traces 显示未闭合或无法证明闭合：
- 该检查项 verdict 必须 `NOT_MEASURABLE`（不得 PASS）

---

## 3) Gate 行为（实现仓库建议）

### 3.1 CI gate（Step 29/31）

- fixture 必须包含最小 `paging_traces.jsonl`，并被 verifier 校验
- verifier FAIL/ERROR → CI FAILED（fail-closed）

### 3.2 run-end gate（Step 30/31）

- run-end packaging 必须把 paging_traces 纳入 FILELIST/SHA256
- run-end verifier 必须检查 paging_traces 存在性与覆盖范围
- verifier exit!=0 → runner exit 2（fail-closed）

---

## 4) 与 PASS/NOT_MEASURABLE/FAIL 的关系（honest reporting）

- paging_traces 缺失：对 P3/P4 相关结论一律 NOT_MEASURABLE（不得 PASS）
- paging_traces 存在但显示未闭合：对 P3/P4 相关结论一律 NOT_MEASURABLE
- paging_traces 闭合且发现本地缺失/重复主键污染：仍按 Step 33 的 FAIL 规则裁决


