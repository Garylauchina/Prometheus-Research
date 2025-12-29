# V11 Step 45 — Evidence Refs Semantic-Join Validation (Beyond run_id) — 2025-12-29

目的：在 Step 44（可解引用校验：run_id/audit_scope_id 自洽）基础上，进一步防止“指向同一 run 内的**无关行**”这种投机：  
把 dereference 校验升级为 **语义 join 锚点一致性校验**，覆盖 paging 链与审计 scope 的关键字段。

前置 SSOT：
- Step 41：`docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`
- Step 42：`docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`
- Step 43：`docs/v11/V11_STEP43_EVIDENCE_REF_INDEX_20251229.md`
- Step 44：`docs/v11/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_20251229.md`

---

## 1) verifier 行为（冻结，gate-on 时）

gate-on（Step 42）且有 `evidence_ref_index.json`（Step 43）时：
- verifier 对 audit 链关键产物的 evidence_refs 做 dereference（Step 44）
- 在此基础上新增 **semantic-join 校验**（本 Step 45）

覆盖文件（最小）：
- `auditor_report.json`
- `auditor_discrepancies.jsonl`
- 审计/证据链相关 `errors.jsonl`

---

## 2) 语义 join 锚点（冻结字段集合）

本 Step 45 关心的“锚点字段”：
- `audit_scope_id`（全局 join key）
- `scope_id`（paging trace 的 audit 执行域）
- `query_chain_id`（paging query 链）
- `endpoint_family`（例如：orders_history / fills / bills）
- `inst_id`（标的）
- `time_window_ms`（审计窗口）
- `clOrdId_namespace_prefix`（命名空间前缀，例如 `v11_`）

说明：
- 上述字段不要求所有文件都包含，但 **一旦引用了某类证据（paging_traces / auditor_*）就必须能在引用链中对齐这些锚点**。

---

## 3) 校验规则（冻结）

### 3.1 auditor_report.json → paging_traces.jsonl 的一致性

若 auditor_report 的某个检查项通过 evidence_refs 引用了 `paging_traces.jsonl` 的行范围，则被引用行必须满足：
- `run_id` 一致（Step 44）
- `audit_scope_id` 一致（Step 44）
- 且若被引用行含以下字段，则必须与 run_manifest.audit_scopes[] 中对应 audit_scope_id 的条目一致：
  - `inst_id`
  - `time_window_ms`
  - `clOrdId_namespace_prefix`
- 若被引用行含 `scope_id`：同一检查项引用的所有 paging_traces 行的 `scope_id` 必须一致（禁止混 scope）
- 若被引用行含 `query_chain_id`：同一检查项引用的所有 paging_traces 行的 `query_chain_id` 必须一致（禁止混链）
- 若被引用行含 `endpoint_family`：必须匹配该检查项宣称的 endpoint family（或 report 中明确字段）

任一不满足 → FAIL（exit 1，fail-closed）

### 3.2 auditor_discrepancies.jsonl 的一致性（最小）

对每条 discrepancy 的 evidence_refs（若引用 `.jsonl`）：
- run_id 与 audit_scope_id 必须一致（Step 44）
- 若引用 paging_traces：同 3.1 的 scope_id/query_chain_id/endpoint_family 不混原则

### 3.3 允许的缺省策略（避免引入“新字段强制化”）

如果被引用行里缺少某些字段（例如旧 trace 没有 inst_id）：
- verifier 不因此直接 FAIL
- 但必须至少做到：
  - run_id、audit_scope_id 一致
  - scope_id/query_chain_id 不混（若存在）
  - endpoint_family 不混（若存在）

---

## 4) 最小验收（CI fixtures）

必须新增至少 2 个“投机负例”（都必须 FAIL），且 **形式层面合法**（不触发 Step 42/43/44）：

负例 A：`query_chain_id` 混链
- evidence_refs 指向同一个 `paging_traces.jsonl`，line_range 合法、hash 合法、run_id/audit_scope_id 合法
- 但引用范围内至少两行的 `query_chain_id` 不同
- 预期：Step 45 FAIL（mixed query_chain_id）

负例 B：`endpoint_family` 不匹配
- evidence_refs 指向 paging_traces 的行，run_id/audit_scope_id 合法
- 但被引用行的 `endpoint_family` 与 report/检查项宣称的不一致（或明显不属于该 check）
- 预期：Step 45 FAIL（endpoint_family mismatch）

可选负例 C：`scope_id` 混域（如果实现已使用 scope_id）

PASS fixture 需要保证：
- paging_traces 的引用范围内 query_chain_id/scope_id/endpoint_family 对齐且不混


