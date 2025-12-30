# V11 Step 81 — Freeze Evidence ↔ EvidenceRefs / Evidence Gate Bundle Alignment — SSOT — 2025-12-30

目的：将 Step80 的冻结证据链（trigger/reject）纳入 V11 Evidence Gate Bundle 的“可引用、可验真、可跨文件 join”的机器审计体系，避免冻结证据成为“孤立文本”。

本文件只允许追加（additive-only）。

前置：
- Step 46：Evidence Gate Bundle Freeze（evidence_refs + evidence_ref_index + dereference validation）
- Step 74-77：freeze 机制与 CI gate
- Step 80：freeze trigger/reject 双落盘语义冻结

---

## 1) 适用证据文件（冻结）

Step81 覆盖（至少）：
- `reconciliation_freeze_events.jsonl`（Freeze Trigger）
- `order_attempts.jsonl`（Freeze Reject attempt）
- `errors.jsonl`（可选补充，但不作为唯一事实链）

---

## 2) 必需字段冻结（跨文件 join 的最小键）

为支持机器 join，以下字段在 Step80 基础上 **冻结为必需**（除非注明可选）：

### 2.1 `reconciliation_freeze_events.jsonl`（trigger）
- `ts_utc`
- `run_id`
- `tick`（可为 null，但必须有结构化 reason 解释）
- `freeze_id`（新增冻结：用于 join，必须为短字符串/短 hash，单次 freeze 生命周期内不变）
- `execution_frozen` = true
- `freeze_reason_code`
- `evidence_refs`（当 Evidence Gate enabled 时：必须存在，且满足 EvidenceRefs hardening）

### 2.2 `order_attempts.jsonl`（reject）
- `ts_utc`
- `run_id`
- `tick`
- `operation`（place/cancel/replace）
- `agent_id_hash`（系统级必须 JSON null）
- `lifecycle_scope`
- `l1_classification = "L1_EXECUTION_FROZEN"`
- `execution_frozen` = true
- `rejected` = true
- `freeze_reason_code`（必须非空）
- `freeze_id`（新增冻结：必须存在，用于 join 到 trigger）
- `evidence_refs`（当 Evidence Gate enabled 时：必须存在，且满足 EvidenceRefs hardening）

说明：
- Step81 引入 `freeze_id` 作为“最小 join 主键”，避免仅凭 `freeze_reason_code` + 时间窗口进行模糊匹配。
- `freeze_id` 必须由 `ExecutionFreezeManager.trigger_freeze()` 生成并携带到 reject evidence（通过 freeze_manager 暴露只读属性/方法）。

---

## 3) Evidence Gate / Ref Index 对齐（冻结）

当 Evidence Gate enabled 时：
- `reconciliation_freeze_events.jsonl` 与 `order_attempts.jsonl` 必须被纳入：
  - `FILELIST.ls.txt`
  - `SHA256SUMS.txt`
  - `evidence_ref_index.json`（包含 rel_path/sha256_16/line_count/byte_size）

且所有 `evidence_refs` 必须：
- `file` 指向上述证据文件之一
- `.jsonl` 引用必须包含 `line_start/line_end`
- `sha256_16` 必须匹配 `evidence_ref_index.json`
- dereference validation 读取行范围后，必须满足：
  - 记录里的 `run_id` 与引用者 `run_id` 一致
  - 如存在 `audit_scope_id`，则一致

---

## 4) 跨文件一致性（Verifier 新规则）

新增 verifier 规则（Step81 最小可测）：

1) **Join completeness（冻结）**
- 对每条 `order_attempts.jsonl` 中的冻结拒绝记录（L1_EXECUTION_FROZEN）：
  - 必须能在 `reconciliation_freeze_events.jsonl` 中找到同 `freeze_id` 的 trigger 记录（同 run_id）

2) **Uniqueness（冻结）**
- 同一 `run_id` 下：
  - `reconciliation_freeze_events.jsonl` 的 `freeze_id` 必须唯一（不允许重复 id 代表不同事件）

3) **Reason consistency（冻结）**
- 对同一 `freeze_id`：
  - reject 的 `freeze_reason_code` 必须等于 trigger 的 `freeze_reason_code`

失败语义：
- 任何上述校验失败 → verifier FAIL → CI fail-closed

---

## 5) 最小验收（硬）

必须证明：
- fixture 中至少包含 1 个 freeze trigger + 1 个 freeze reject
- 两者共享同一 `freeze_id`
- verifier 能 PASS
- 故意篡改 `freeze_id`/`freeze_reason_code` 能 FAIL（证明规则生效）


