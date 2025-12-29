# V11 Step 32 — Orphan Detection Implemented in Quant (MEASURABLE, orders-level) — 2025-12-29

目的：记录 **Step 32（Orphan Detection 最小可测）** 已在实现仓库（Prometheus-Quant）落地，并冻结其“对外可审计口径”（实现锚点 + 关键假设 + verdict 规则）。

SSOT 规格：
- `docs/v10/V11_STEP32_ORPHAN_DETECTION_MIN_MEASURABLE_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`ed580cb`
- message：`v11: make orphan detection measurable (orders-level, clOrdId namespace + paging closure)`
- SSOT 契约版本（Quant）：`V11_EXCHANGE_AUDITOR_20251229`（已 bump）
- files changed（概览）：
  - `prometheus/v11/auditor/exchange_auditor.py`：重写 orphan detection（含 orders-history 查询 + 分页闭合）
  - `prometheus/v11/ops/broker_trader.py`：`clOrdId` 增加 `v11_` 前缀（命名空间）
  - `prometheus/v11/ops/run_v11_service.py`：manifest 新增审计字段（用于写实）

---

## 2) 冻结的关键口径（必须与 Spec 一致）

### 2.1 in-scope 判定（clOrdId 命名空间）

- 采用 `clOrdId` 前缀命名空间：`v11_`（用于把“本系统产生的订单”与账户历史/手工单隔离）
- 若交易所 orders-history 返回缺少 `clOrdId` 或分页不可闭合 → orphan detection 必须 `NOT_MEASURABLE`（不得 PASS）

### 2.2 分页闭合（硬规则）

- orders-history 必须证明集合闭合（hasMore 清空/游标走完）
- 分页不闭合 → `NOT_MEASURABLE`（并写入原因）

### 2.3 orphan 判定（FAIL）

对任一 in-scope order：
- 交易所可回查，但本地入册缺失 → `FAIL`
- 本地存在但归因锚点缺失/无效（`agent_id_hash` 与 `lifecycle_scope` 均缺失/空）→ `FAIL`

---

## 3) 对外效果（审计闭环的变化）

- ExchangeAuditor 的“orphan detection”从 `NOT_MEASURABLE（未实现）` → `MEASURABLE（orders-level）`
- 这使 auditor 总 verdict 能更可靠地区分：
  - `PASS`：分页闭合且 0 orphan
  - `NOT_MEASURABLE`：前提不足（clOrdId 缺失/分页不闭合）
  - `FAIL`：分页闭合且发现 orphan


