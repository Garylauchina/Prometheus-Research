# V11 Step 74 — Real-time Reconciliation Freeze (Execution World, Minimal Measurable) — SSOT — 2025-12-30

目的：把“证据链/真值链断裂时立即停止继续污染”的原则工程化为一个最小可测机制：当出现不可解释差异或关键真值缺失时，系统进入 **execution_frozen**，并且 **禁止任何新的下单写操作**（直到 run 结束或人工介入）。该机制必须可审计、可复核、fail-closed。

本文件只允许追加（additive-only）。

前置：
- BrokerTrader 作为唯一写入口（intent-only → execution）
- ExchangeAuditor/证据包（FILELIST/SHA256SUMS/evidence_ref_index）
- errors.jsonl / run_manifest.json 已存在写实机制

---

## 1) 术语（冻结）

- **reconciliation**：在 execution_world 中不发明记账，而是对“本地证据链”与“交易所可查询真值”做一致性检查（或最小必要的完整性检查）。
- **execution_frozen**：冻结状态；冻结期间系统仍可读、仍可落盘证据，但 **不得发送任何新订单/撤单等写操作**。

---

## 2) 触发条件（最小集合，冻结）

触发条件分为两类：**证据链断裂** 与 **真值链断裂**。任一满足即冻结。

### 2.1 证据链断裂（Evidence broken）
- `EVIDENCE_GATE_FAIL`：run-end evidence gate 判定 FAIL（exit 2）属于后验；本 Step 要求 **运行中**也能冻结。
- `MISSING_CRITICAL_EVIDENCE`：出现关键文件/关键行段缺失，导致后续不可审计（例如订单已提交但无法找到对应 ack/status 证据）。

### 2.2 真值链断裂（Truth degraded / mismatch）
最小可测触发（建议优先实现）：
- `P2_OVERDUE`：存在已提交订单但在预期窗口内无法获得 P2 终态（timeout 由 world 参数提供，需写实记录）。
- `ACCOUNT_RESTRICTED`：交易所返回账户受限/禁止交易/风控限制类状态（以 OKX 原始字段为证据）。
- `UNEXPLAINED_BALANCE_DELTA`：出现余额/权益变动，但无法通过已知的 fills/bills/fees/pnl 证据集解释（需要最小 join 完整性）。
- `TRUTH_PROFILE_DEGRADED`：truth_profile/truth_quality 指示关键真值不可用且不可补救（例如 positions_truth_quality=unknown 且为必需）。

规则（冻结）：
- 触发时必须写入 `errors.jsonl`（reason_code 固定词表，见第 5 节）。
- 触发后必须设置 `execution_frozen=true` 并在本 run 余下时间禁止写操作。

---

## 3) 行为语义（冻结）

冻结后的硬行为：
- BrokerTrader/Runner 必须拒绝任何新的写动作（place/cancel/replace）。
- 允许继续：只读查询、审计查询、写盘 errors/manifest/诊断信息。
- 必须在 decision_trace 中写实记录：所有 agent intent 被强制改写为 `HOLD`（或直接跳过决策），并在 trace/manifest 中记录 `frozen=true` 与 reason_code。

说明：
- freeze 与 “立即退出（sys.exit）”不同：freeze 允许继续收集证据帮助定位问题；但不允许继续交易污染证据链。

---

## 4) 证据落盘（冻结）

新增/强化以下落盘（additive-only）：

- `errors.jsonl`
  - 新增 `error_type="execution_frozen"`
  - 必含：`reason_code`、`ts_utc`、`run_id`、`audit_scope_id`（若有）、`evidence_refs`（若可提供）

- `reconciliation_freeze_events.jsonl`（建议新增，append-only）
  - 每次触发写一行，字段最小集合：
    - `ts_utc`
    - `run_id`
    - `freeze_id`（短 hash）
    - `reason_code`
    - `details`（fact-only，不解释）
    - `evidence_refs`（可选）

---

## 5) reason_code 词表（冻结）

最小词表：
- `p2_overdue`
- `account_restricted`
- `unexplained_balance_delta`
- `truth_profile_degraded`
- `missing_critical_evidence`

允许 additive 扩展，但不得复用旧语义。

---

## 6) Manifest 记录（additive-only，冻结）

在 `run_manifest.json` 增加对象：

```json
{
  "execution_freeze": {
    "enabled": true,
    "frozen": true,
    "freeze_reason_code": "p2_overdue",
    "freeze_ts_utc": "YYYY-MM-DDTHH:MM:SS.ssssssZ",
    "freeze_event_rel_path": "reconciliation_freeze_events.jsonl",
    "status": "frozen"
  }
}
```

`status` 词表（冻结）：
- `not_frozen`
- `frozen`

---

## 7) 验收（最小）

最小验收用例（可以用 fixture/模拟）：
- 模拟 P2 overdue 或 account_restricted：
  - 系统设置 `execution_frozen=true`
  - 后续不再有任何 order_attempt/write evidence
  - `errors.jsonl` 与（若实现）`reconciliation_freeze_events.jsonl` 有对应记录
  - manifest 写实 `execution_freeze` 字段

---

## 8) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + 样例错误记录 + manifest 片段）


