# V11 Step 87 — Generic EvidenceRefs Backfill View Bundle (beyond freeze) — SSOT — 2025-12-30

目的：将 Step81-86 在 freeze 证据链上验证过的机制（EvidenceRefs 结构化、range 解引用/同质性、sha256_16 对齐、append-only backfill、backfill view verifier）提升为 **通用证据链 bundle**，推广到审计关键证据（paging/orders/fills/bills/auditor outputs），避免“freeze 特例化”。

本文件只允许追加（additive-only）。

前置：
- Step 46：Evidence Gate Bundle Freeze（EvidenceRefs + evidence_ref_index + dereference）
- Step 81-86：freeze evidence refs alignment → backfill view verifier（已验证机制可行）

---

## 1) Bundle 范围（冻结：第一批必须覆盖）

第一批适用证据文件（冻结）：
- `paging_traces.jsonl`
- `auditor_report.json`
- `auditor_discrepancies.jsonl`

说明：
- 这些文件是“审计闭包证明/发现差异”的核心证据，属于高优先级推广对象。

可选扩展（后续 step 冻结）：
- `orders_history_raw.jsonl` / `fills_raw.jsonl` / `bills_raw.jsonl`（若存在）
- `order_attempts.jsonl` / `order_status_samples.jsonl`（执行证据）

---

## 2) 统一的 EvidenceRefs 规则（通用）

当 Evidence Gate enabled 时，所有上述文件中的 `evidence_refs` 必须满足：
- `file`
- `line_start/line_end`（引用 `.jsonl` 时必须）
- `sha256_16`（必须与 `evidence_ref_index.json` 对齐）
- `audit_scope_id`（若启用 multi-audit，则必须存在并一致）

允许使用 Step85 的 append-only backfill 机制：
- 缺失 `sha256_16` 可由 `evidence_refs_backfill.jsonl` 回填
- verifier 必须以 backfill view 校验（Step86 机制）

---

## 3) Range 同质性（按文件家族冻结）

### 3.1 `paging_traces.jsonl`

对任何 range 引用（[line_start,line_end]）：
- `run_id` 必须一致
- `scope_id` 必须一致
- `query_chain_id` 必须一致
- `endpoint_family` 必须一致
- `audit_scope_id` 必须一致（若启用）

目的：
防止“混链/混端点/混 scope”的引用伪造。

### 3.2 `auditor_discrepancies.jsonl`

对任何 range 引用：
- `run_id` 必须一致
- `audit_scope_id` 必须一致（若启用）
- `discrepancy_kind`（若存在）必须一致或属于允许集合（必须被冻结）

### 3.3 `auditor_report.json`

`auditor_report.json` 通常是单文件 JSON（非 jsonl）：
- evidence_refs 必须指向其所依赖的 jsonl 证据文件范围（paging_traces/discrepancies）
- verifier 必须能解引用这些范围并验证一致性（本 bundle 的核心价值）

---

## 4) 通用 Backfill Integrity（继承 Step86）

对 `evidence_refs_backfill.jsonl`：
- 指向有效文件/有效行/有效 ref_index
- sha256_16 必须等于 evidence_ref_index 中 target_file 的 sha256_16
- 同 key 不允许冲突回填（幂等允许重复相同值）

---

## 5) 最小验收（硬）

必须证明：
- PASS fixture：audit artifacts（paging_traces + auditor_report + discrepancies）在 backfill view 下满足：
  - sha256_16 对齐
  - range 同质性（scope_id/query_chain_id/endpoint_family 等）
- FAIL fixture：混入不同 query_chain_id 或不同 endpoint_family 的 range 引用必须 fail-closed


