# V11 Step 80 — Freeze Evidence Semantics Freeze — SSOT — 2025-12-30

目的：冻结（execution_frozen）不仅要“阻断写操作”，还必须形成 **机器可审计、可统计、可验证** 的事实证据链；避免仅靠 stdout/return False 造成审计盲区。

本文件只允许追加（additive-only）。

前置：
- Step 74/75/76/77：freeze 运行时机制 + CI gate
- Step 78/79：静态门禁，阻断旁路与 pre-check 漏洞回退

---

## 1) 冻结的两类事实事件（必须区分）

冻结相关事实分两类：

1) **Freeze Trigger（冻结被触发）**
- “系统进入冻结态”的事实
- 需要记录：触发时刻、触发原因、上下文（run_id/tick/audit_scope_id 等）

2) **Freeze Reject（写操作被拒绝）**
- “在冻结态下尝试写操作但被拒绝”的事实
- 需要记录：operation（place/cancel/replace）、intent 归属（agent/system）、拒绝原因与证据引用

两类都必须落盘，且 append-only。

---

## 2) 证据落盘（强制）

### 2.1 Freeze Trigger → `reconciliation_freeze_events.jsonl`（强制）

每次触发冻结必须追加一条记录（append-only），字段最小集合（冻结）：
- `ts_utc`
- `run_id`
- `tick`（若不可得则为 null，但必须有 `reason_code` 解释）
- `freeze_reason_code`（冻结）
- `freeze_reason_detail`（可选，结构化/字符串均可，但必须与 reason_code 一致）
- `execution_frozen` = true
- `audit_scope_id`（若启用 multi-audit；否则可为 null）
- `evidence_refs`（若启用 Evidence Gate Bundle；否则可省略）

### 2.2 Freeze Reject → `order_attempts.jsonl`（强制）

任何写操作（place/cancel/replace）在冻结态下被阻断时，必须：
- **仍然写入一条 attempt 记录**（append-only）
- 用明确的 L1 分类标记冻结拒绝（冻结语义）：
  - `l1_classification = "L1_EXECUTION_FROZEN"`（或等价枚举，但必须在 taxonomy 中冻结）

attempt 字段最小集合（冻结）：
- `ts_utc`
- `run_id`
- `tick`
- `operation`（冻结：`place_order` / `cancel_order` / `replace_order`）
- `agent_id_hash`（系统级必须为 JSON null）
- `lifecycle_scope`（系统级必须为非空字符串；agent 级也可填）
- `intent_source`（SSOT 词表）
- `intent_kind`（SSOT 词表）
- `l1_classification`（必须是冻结拒绝）
- `execution_frozen` = true
- `freeze_reason_code`（同 ExecutionFreezeManager）
- `rejected` = true
- `evidence_refs`（若启用 Evidence Gate Bundle；否则可省略）

说明：
- freeze reject 不得触达 connector，不得产生任何 “写已发送” 的证据（例如 ack/order id）。
- 该 attempt 是“事实：曾尝试 + 被阻断”，用于 post-run 审计与统计。

### 2.3 `errors.jsonl`（可选补充，不作为唯一证据）

允许同时写入 `errors.jsonl` 作为 operator 可读提示，但不得以此替代 2.1/2.2 的事实证据。

---

## 3) 机器可验证约束（Verifier / CI）

新增 verifier 规则（建议纳入 Evidence Gate Bundle 的扩展或新增 acceptance 脚本）：

冻结后必须满足：
- **不出现**任何 connector 写成功的证据（例如 order ack / status samples 的 “已发出写请求” 语义）
- **必须出现**至少 1 条 Freeze Trigger 记录（2.1）
- **必须出现**至少 1 条 Freeze Reject attempt（2.2），且：
  - `l1_classification == L1_EXECUTION_FROZEN`
  - `execution_frozen == true`
  - `freeze_reason_code` 非空

备注：fixture 必须包含冻结场景，防止“代码正确但无人测试”。

---

## 4) 最小验收（硬）

必须证明：
- 触发冻结时：`reconciliation_freeze_events.jsonl` 追加 1 条记录
- 冻结后尝试写入时：`order_attempts.jsonl` 追加冻结拒绝记录（L1_EXECUTION_FROZEN）
- verifier/CI 能在 fixture 上自动校验这些事实（fail-closed）


