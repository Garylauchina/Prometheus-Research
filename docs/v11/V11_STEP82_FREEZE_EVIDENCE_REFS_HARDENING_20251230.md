# V11 Step 82 — Freeze EvidenceRefs Hardening (Trigger/Reject) — SSOT — 2025-12-30

目的：在 Step80/81 的冻结证据链之上，补齐 Evidence Gate Bundle 语义：当 evidence gate enabled 时，freeze 相关记录的 `evidence_refs` 必须 **可解引用且可验真**，避免“形式正确但语义无关”的引用。

范围（最小版，冻结）：
- `reconciliation_freeze_events.jsonl`（Freeze Trigger）
- `order_attempts.jsonl`（Freeze Reject）

本文件只允许追加（additive-only）。

前置：
- Step 46：Evidence Gate Bundle Freeze（EvidenceRefs + evidence_ref_index + dereference validation）
- Step 80：freeze trigger/reject 双落盘
- Step 81：freeze_id join + 跨文件一致性 verifier

---

## 1) 何时强制（冻结）

当且仅当 **Evidence Gate enabled**（Quant 侧已有 gate bundle 开关语义）时，本 Step82 的强制要求生效：
- 若 enabled：必须满足本文件所有 hardening 规则，否则 CI fail-closed
- 若 disabled：可不填 `evidence_refs`（但不推荐）

---

## 2) EvidenceRefs 结构冻结（必须）

对以下两类记录，`evidence_refs` 必须存在且为非空 list：

### 2.1 Trigger 记录（reconciliation_freeze_events.jsonl）
每条 trigger 记录必须包含 `evidence_refs`，且其中至少 1 个 ref 指向：
- `file = "reconciliation_freeze_events.jsonl"`

### 2.2 Reject 记录（order_attempts.jsonl, L1_EXECUTION_FROZEN）
每条冻结拒绝 attempt 必须包含 `evidence_refs`，且其中至少 1 个 ref 指向：
- `file = "order_attempts.jsonl"`

每个 evidence_ref 必须包含字段（冻结）：
- `file`（相对 run_dir 的路径）
- `line_start`（1-based）
- `line_end`（1-based，且 >= line_start）
- `sha256_16`（必须匹配 evidence_ref_index）
- `audit_scope_id`（可选：若 run 启用了 audit_scopes，则必须一致；否则可省略/为 null）

---

## 3) Index/Hash 对齐（必须）

当 evidence gate enabled 时：
- `reconciliation_freeze_events.jsonl` 与 `order_attempts.jsonl` 必须出现在：
  - `FILELIST.ls.txt`
  - `SHA256SUMS.txt`
  - `evidence_ref_index.json`

并且：
- `evidence_refs[].sha256_16` 必须等于 `evidence_ref_index.json` 中对应文件的 `sha256_16`
- `line_start/line_end` 必须在对应 `.jsonl` 的 `line_count` 范围内

---

## 4) Dereference Validation（必须，新增规则）

Verifier 必须对 freeze 相关 evidence_refs 执行解引用校验（读行→parse json→校验语义）：

对引用 `reconciliation_freeze_events.jsonl` 的 ref：
- 解引用到的记录必须包含：
  - `run_id`（与当前 run 一致）
  - `execution_frozen=true`
  - `freeze_id` 非空
  - `freeze_reason_code` 非空

对引用 `order_attempts.jsonl` 的 ref：
- 解引用到的记录必须包含：
  - `run_id`（与当前 run 一致）
  - `l1_classification="L1_EXECUTION_FROZEN"`
  - `execution_frozen=true`
  - `rejected=true`
  - `freeze_id` 非空
  - `freeze_reason_code` 非空

跨文件一致性（最小 join）：
- 对同一个 `freeze_id`：
  - trigger 的 `freeze_reason_code` 必须等于 reject 的 `freeze_reason_code`

---

## 5) 最小验收（硬）

必须证明：
- PASS：fixture 中 trigger/reject 均带 `evidence_refs`，可解引用且语义一致
- FAIL：构造一个“sha256_16 不匹配”或“line_range 指向无关记录”或“freeze_reason_code 不一致”，verifier 必须 fail-closed


