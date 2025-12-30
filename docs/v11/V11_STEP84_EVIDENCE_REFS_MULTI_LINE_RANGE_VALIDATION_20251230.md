# V11 Step 84 — EvidenceRefs Multi-line Range + Range-Dereference Validation — SSOT — 2025-12-30

目的：在 Step82/83 的单行解引用与 hash 对齐基础上，冻结 `line_end` 的多行范围语义，并对范围内记录执行一致性校验，防止“引用范围混入无关行”。

本文件只允许追加（additive-only）。

前置：
- Step 46：Evidence Gate Bundle Freeze（EvidenceRefs hardening + dereference）
- Step 82：freeze evidence_refs dereference（line_range + 语义）
- Step 83：sha256_16 ↔ evidence_ref_index 对齐

---

## 1) 范围引用语义（冻结）

当 `evidence_refs` 引用 `.jsonl` 文件时：
- `line_start` 与 `line_end` 必须同时存在
- `line_end >= line_start`
- 语义：引用范围是 **闭区间** `[line_start, line_end]`，表示一组连续记录

用途（例）：
- 一个冻结事件（freeze_id）可能对应多个 reject attempts（多次 place/cancel/replace 都被拒绝）
- 或一个 audit/paging trace 需要引用多条连续请求/响应记录

---

## 2) Range-Dereference Validation（新增 verifier 规则）

Verifier 对每个 `.jsonl` 的 range evidence_ref 必须：

1) **Range integrity**
- 范围内每一行都必须是合法 JSON 对象（不可跳过坏行）
- 每一行都必须包含 `run_id` 且与当前 run 一致

2) **Homogeneity（同质性）**

对 freeze 相关引用（本 Step84 首先覆盖 freeze 两类文件）：

### 2.1 `order_attempts.jsonl` 的 range 引用（冻结拒绝集合）
如果 range 被声明为“冻结拒绝集合”（由调用方 reason_code/usage 标记或由 verifier 根据字段推断）：
- 范围内每条记录必须满足：
  - `l1_classification == "L1_EXECUTION_FROZEN"`
  - `execution_frozen == true`
  - `rejected == true`
  - `freeze_id` 非空且 **全部相同**
  - `freeze_reason_code` 非空且 **全部相同**

### 2.2 `reconciliation_freeze_events.jsonl` 的 range 引用（冻结触发集合）
若 range 覆盖 freeze trigger（通常为 1 条，但允许多条用于批量引用）：
- 范围内每条记录必须满足：
  - `execution_frozen == true`
  - `freeze_id` 非空且 **全部相同**（若 range>1，则表示同一 freeze_id 的多条补充事件；否则应拆分引用）
  - `freeze_reason_code` 非空且 **全部相同**

3) **Cross-file semantic join（最小）**
当一个 reject range 引用了 trigger（直接或间接，通过同 run 里的 join 规则）：
- 该 `freeze_id` 的 trigger 与 reject 的 `freeze_reason_code` 必须一致

失败语义（冻结）：
- 任何违反 → FAIL（exit 1）
- 异常/无法读取 → ERROR（exit 2）
- CI fail-closed（exit!=0 阻断合并）

---

## 3) Fixture（PASS/FAIL 必须具备）

### 3.1 PASS fixture（必须）

必须包含一个 freeze_id，有：
- `reconciliation_freeze_events.jsonl` 至少 1 条 trigger
- `order_attempts.jsonl` 至少 2 条 reject（同 freeze_id、同 freeze_reason_code）
- `evidence_refs` 用一个 range 引用覆盖这 2 条 reject（line_start=1, line_end=2）

### 3.2 FAIL fixture（必须）

至少一种 FAIL：
- 在同一个 reject range 内混入不同 freeze_id 或不同 freeze_reason_code
- 或混入非 L1_EXECUTION_FROZEN 的 attempt
- 或 range 内有一行不是合法 JSON

---

## 4) 最小验收（硬）

必须证明：
- PASS：range dereference + 同质性校验通过（exit 0）
- FAIL：构造混入/不合法行后 fail-closed（exit 1）


