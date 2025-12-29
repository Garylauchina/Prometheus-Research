# V11 Step 33 — Fills/Bills Join: Minimal MEASURABLE (P3/P4) — 2025-12-29

目的：在 Step 32（orders-level orphan detection）基础上，把 ExchangeAuditor 的可测范围扩展到：
- **P3 fills**（成交事实）
- **P4 bills**（费用/资金费/余额变动等账务事实）

让 “成交/费用相关结论” 从长期 `NOT_MEASURABLE` 逐步变为 **可机械复核（MEASURABLE）**，并且严格遵守分页闭合与不发明真值原则。

适用范围（最小版本）：
- execution_world（OKX demo/live）
- **仅做“存在性 + 归因 join + 分页闭合证明”**  
  不做完整会计恒等式平账（那属于 post-run ledger audit 的更高阶步骤）。

SSOT 关联：
- Order confirmation protocol（P0–P5）：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`
- Registry audit taxonomy：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V10_BROKERTRADER_REGISTRY_AUDIT_CHECKLIST_20251226.md`
- Step 32 Spec（orders-level）：`/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP32_ORPHAN_DETECTION_MIN_MEASURABLE_20251229.md`

---

## 0) 关键边界（hard）

- **分页不闭合 → NOT_MEASURABLE**（不得 PASS）：fills/bills 任一分页端点无法证明“已完整拉取”，相关结论一律 NOT_MEASURABLE。
- **不强行归因**：bills 行若缺 `ordId`（资金费/系统事件等），只能归为 system-level，不得分摊到 Agent（除非交易所 JSON 提供可回查关联键）。
- **in-scope 限定**：仍以 `clOrdId` 命名空间前缀（例如 `v11_`）过滤“本系统订单集合”，避免账户历史/手工单污染。

---

## 1) 最小 join keys（冻结）

- orders → fills：优先 `ordId`（订单主键）；fills 的去重键为 `tradeId`（若可得）
- orders → bills：若 bills 行包含 `ordId`，以 `ordId` join；bills 的去重键为 `billId/id`

说明：
- 若 fills/bills JSON 不含上述关键字段，则该类别结论必须降级为 NOT_MEASURABLE，并写明 `reason_code`。

---

## 2) 最小可测算法（P3/P4）

### 2.1 P3 fills（存在性 + join + 幂等）

1) 选择 in-scope orders 集合（来自 Step 32 的 orders-history 分页闭合集合，按 `clOrdId` 前缀过滤）
2) 通过交易所 fills 端点拉取时间窗内 fills 集合（分页闭合）
3) 对每条 fill：
   - 必须能解析 `ordId`（否则该条为 `fills_missing_ordId` → NOT_MEASURABLE）
   - 若 `ordId` 属于 in-scope orders：
     - 必须能在本地找到对应订单入册锚点（`order_attempts/order_status_samples`）
4) 统计并输出：
   - `fills_in_scope_count`
   - `fills_missing_local_record_count`（FAIL 的候选）
   - `duplicate_trade_id_count`（若发现重复 tradeId → FAIL）

裁决（fills check）：
- PASS：分页闭合 + 0 `fills_missing_local_record` + 0 `duplicate_trade_id`
- NOT_MEASURABLE：分页不闭合 / 缺关键字段（不可证明）
- FAIL：分页闭合且发现 in-scope fills 在本地证据缺失，或重复 tradeId 污染

### 2.2 P4 bills（存在性 + join + system-level 分流）

1) 拉取时间窗内 bills 集合（分页闭合）
2) 对每条 bill：
   - 若含 `ordId` 且 `ordId` 属于 in-scope orders：
     - 必须能在本地找到对应订单入册锚点
   - 若不含 `ordId`：
     - 归类为 `system_level_bill_without_ordId`（WARN），不得硬分摊
3) 去重/幂等：
   - bills 必须以 `billId/id` 去重；重复 billId → FAIL

裁决（bills check）：
- PASS：分页闭合 + 0 `bills_missing_local_record` + 0 `duplicate_bill_id`
- NOT_MEASURABLE：分页不闭合 / 缺关键字段（不可证明）
- FAIL：分页闭合且发现 in-scope bills 在本地证据缺失，或重复 billId 污染

---

## 3) Auditor 输出（additive-only 建议字段）

在 `auditor_report.json.summary_counts` 建议追加：
- `fills_paging_incomplete_count`
- `fills_checked_count`（已有字段可复用）
- `fills_in_scope_count`
- `fills_missing_local_record_count`
- `duplicate_trade_id_count`
- `bills_paging_incomplete_count`
- `bills_checked_count`（已有字段可复用）
- `bills_in_scope_count`
- `bills_missing_local_record_count`
- `duplicate_bill_id_count`
- `system_level_bill_without_ordId_count`

在 `auditor_discrepancies.jsonl` 新增 discrepancy_type（append-only）：
- `fills_paging_incomplete`（NOT_MEASURABLE）
- `bills_paging_incomplete`（NOT_MEASURABLE）
- `fills_missing_local_record`（FAIL）
- `bills_missing_local_record`（FAIL）
- `duplicate_trade_id_in_registry`（FAIL）
- `duplicate_bill_id_in_registry`（FAIL）
- `bill_without_order_id`（WARN，沿用既有 taxonomy）

---

## 4) 总 verdict 规则（honest reporting）

- 若 P3/P4 被纳入本次审计范围（scope）：
  - 任一分页不闭合 → 总 verdict 至少 NOT_MEASURABLE
  - 任一 FAIL 条件命中 → 总 verdict 为 FAIL


