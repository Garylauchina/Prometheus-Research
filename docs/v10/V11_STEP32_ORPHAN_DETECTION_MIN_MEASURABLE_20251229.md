# V11 Step 32 — Orphan Detection: Minimal MEASURABLE (Orders-level) — 2025-12-29

目的：把 ExchangeAuditor 的 **Orphan Detection** 从 `NOT_MEASURABLE` 推进到 **最小可测（MEASURABLE）**，以便对 execution_world 的关键风险给出可复核结论：
- 交易所存在“我们产生的订单事实”，但本地证据链无法找到归因锚点（`agent_id_hash` / `lifecycle_scope`）→ **orphan（FAIL）**

适用范围（最小版本）：
- **orders-level**（P2 终态层）：只对“订单集合闭包 + 本地入册覆盖 + 归因锚点存在性”做判定  
- fills/bills（P3/P4）不作为 Step 32 的强制范围（后续 Step 扩展）

SSOT 关联：
- Orphan hard definition：`docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`（§0）
- Auditor contract：`docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`
- Order confirmation protocol：`docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`

---

## 0) 关键定义（冻结）

### 0.1 “我们产生的订单”（in-scope order）

Orphan detection 只能对“可证明属于本系统产生”的订单做裁决，否则会把账户历史/手工单混进来造成误判。

最小可测口径（推荐，冻结为 baseline）：
- 以 `clOrdId` 的**命名空间前缀**判定 in-scope：  
  - 例：`clOrdId` 以 `v11_` 开头（具体前缀由 Quant 实现冻结并写入 manifest）
- 如果交易所 orders-history 查询返回的记录不含 `clOrdId`（或实现未在本地证据中落盘 `clOrdId`），则 orphan detection 对该 run **NOT_MEASURABLE**（不得猜测）。

### 0.2 Orphan（硬定义）

对任一 in-scope 订单，若满足任一条件则为 orphan（FAIL）：
- 交易所可回查到该订单（orders-history / order status），但本地 `order_attempts.jsonl` 与 `order_status_samples.jsonl` 中**找不到对应记录**（入册缺失）
- 本地找得到订单记录，但其归因锚点缺失/无效：
  - `agent_id_hash` 为空字符串/缺失（应为非空 string 或 JSON null）
  - 且 `lifecycle_scope` 也缺失/为空（system-level 动作必须非空 string）

说明：
- system-level 订单允许 `agent_id_hash = null`，但必须有 `lifecycle_scope`（例如 `system_flatten`）。

---

## 1) 最小可测输入（Auditor 必须具备）

### 1.1 本地证据（run_dir）

必须存在：
- `order_attempts.jsonl`（至少包含：`clOrdId`、归因锚点、ack 信息）
- `order_status_samples.jsonl`（至少包含：`clOrdId` 或 `ordId`、P2 状态样本）
- `run_manifest.json`（包含：`run_id`、审计时间窗/inst_id、以及 `clOrdId_namespace_prefix`（推荐新增））

### 1.2 交易所只读查询（最小）

必须能完成：
- orders-history（或等价端点）：按时间窗与 instId 拉取订单集合

分页闭合（硬规则）：
- 若端点存在 `hasMore=true` 或游标未走完即停止 → 本次 orphan detection **NOT_MEASURABLE**（不得报 PASS）

---

## 2) 最小算法（orders-level）

1) 从交易所 orders-history 拉取订单集合（分页闭合）
2) 过滤 in-scope：`clOrdId` 满足命名空间前缀（例如 `v11_`）
3) 构建本地索引：
   - `local_by_clOrdId`：来自 `order_attempts.jsonl` 与 `order_status_samples.jsonl`
4) 对每个 exchange in-scope clOrdId：
   - 若本地完全缺失 → `orphan_exchange_order_without_local_record`（FAIL）
   - 若本地存在但归因锚点缺失/无效 → `orphan_missing_attribution_anchor`（FAIL）

可选（不作为 Step 32 强制）：
- 若 exchange 记录提供 `ordId`，可追加验证 `ordId` 与本地记录一致（用于识别 clOrdId 冲突/重用）。

---

## 3) 裁决规则（单项 check 的 verdict）

对 Orphan Detection 这一项检查：
- **PASS**：分页闭合，且 0 orphan
- **NOT_MEASURABLE**：任一前提不满足（例如缺 clOrdId、分页不闭合、时窗/instId 不可证明）
- **FAIL**：分页闭合，且发现 ≥1 orphan

对 auditor 总 verdict（沿用既有 honest reporting 原则）：
- 若 Orphan Detection 是必做项且为 NOT_MEASURABLE → auditor 总 verdict 至少为 NOT_MEASURABLE（不得 PASS）

---

## 4) 审计输出（新增字段建议，additive-only）

在 `auditor_report.json` 的 summary_counts 建议追加：
- `orphan_in_scope_orders_count`
- `orphan_missing_local_record_count`
- `orphan_missing_attribution_anchor_count`
- `orphan_detection_paging_incomplete_count`

在 `auditor_discrepancies.jsonl` 新增 discrepancy_type（additive-only）：
- `orphan_exchange_order_without_local_record`（FAIL）
- `orphan_missing_attribution_anchor`（FAIL）
- `orphan_detection_paging_incomplete`（NOT_MEASURABLE）
- `orphan_detection_missing_clOrdId`（NOT_MEASURABLE）


