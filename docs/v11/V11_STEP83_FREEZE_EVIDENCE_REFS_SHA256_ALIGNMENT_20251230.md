# V11 Step 83 — Freeze EvidenceRefs SHA256 Alignment (sha256_16 ↔ evidence_ref_index) — SSOT — 2025-12-30

目的：补齐 Step82 的“hash 级防篡改”要求：当 evidence gate enabled 时，freeze 相关 `evidence_refs` 必须携带 `sha256_16`，并与 `evidence_ref_index.json` 严格匹配（fail-closed）。

范围（最小版，冻结）：
- `reconciliation_freeze_events.jsonl`（Freeze Trigger）
- `order_attempts.jsonl`（Freeze Reject）

本文件只允许追加（additive-only）。

前置：
- Step 43：`evidence_ref_index.json`
- Step 46：Evidence Gate Bundle Freeze（EvidenceRefs hardening）
- Step 80/81：freeze evidence chain + freeze_id join
- Step 82：freeze evidence refs dereference（line_range + 语义校验）

---

## 1) 何时强制（冻结）

当且仅当 **Evidence Gate enabled** 时，本 Step83 的强制要求生效：
- enabled：必须满足本文件所有规则，否则 CI fail-closed
- disabled：可不填 `sha256_16`（不推荐）

---

## 2) EvidenceRefs 字段冻结（新增强制）

对以下记录的 `evidence_refs[]`：
- `reconciliation_freeze_events.jsonl` 中所有 trigger 记录
- `order_attempts.jsonl` 中所有冻结拒绝记录（`l1_classification="L1_EXECUTION_FROZEN"`）

当 Evidence Gate enabled 时，必须满足：
- `evidence_refs[].sha256_16` **必填**
- `evidence_refs[].file` 必须在 `evidence_ref_index.json` 的 `rel_path` 集合中存在

### 2.1 单向引用最小策略（为避免循环依赖）

允许采用最小的 **单向引用** 策略来避免循环依赖：
- trigger 记录的 `evidence_refs` **可为空/缺失**（最小版）
- reject 记录必须包含至少 1 条 `evidence_refs` 指向 trigger 文件（例如 `reconciliation_freeze_events.jsonl`），并携带 `sha256_16`

一旦某条记录包含 `evidence_refs`，则其中的 `sha256_16` 必须满足本 Step83 的严格对齐规则（fail-closed）。

---

## 3) sha256_16 对齐规则（严格）

Verifier 必须对每条 freeze 相关 `evidence_refs` 执行以下校验：

1) **Index presence**
- 在 `evidence_ref_index.json` 中查到 `rel_path == evidence_ref.file` 的条目，否则 FAIL

2) **Hash equality**
- `evidence_refs.sha256_16 == evidence_ref_index[rel_path].sha256_16`，否则 FAIL

3) **Line range validity（与 Step82 保持一致）**
- `.jsonl` 引用必须包含 `line_start/line_end` 且在 `line_count` 范围内，否则 FAIL

失败语义（冻结）：
- 任何不一致 → exit 1（FAIL）
- 异常/无法读取 index → exit 2（ERROR）
- CI fail-closed（exit != 0 阻断合并，并标注 CRITICAL SECURITY ISSUE）

---

## 4) Fixture（PASS/FAIL 必须具备）

### 4.1 PASS fixture（必须）

必须包含：
- `evidence_ref_index.json`
- `reconciliation_freeze_events.jsonl`（含 evidence_refs.sha256_16）
- `order_attempts.jsonl`（含 evidence_refs.sha256_16）

且 sha256_16 与 index 完全一致。

### 4.2 FAIL fixture（必须）

必须证明 gate 有效（至少一种）：
- 篡改某条 evidence_refs.sha256_16（与 index 不一致）→ verifier FAIL
- 或引用一个不存在于 index 的 file → verifier FAIL

---

## 5) 最小验收（硬）

必须证明：
- PASS：Step83 verifier 对 PASS fixture exit 0
- FAIL：对 FAIL fixture exit 1（证明 fail-closed 生效）


