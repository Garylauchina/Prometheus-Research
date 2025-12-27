# V10 Order Confirmation Protocol (OKX execution_world) — 2025-12-26

目的：解决“通信/异步导致的不一致”，保证交易员（Execution）记录的每一笔交易都能被交易所 API 返回的 JSON 复现与回查。

本协议适用于 `execution_world`（OKX demo/live）。`offline_sim` 不适用：相关字段必须写 `null + reason_code`，不得伪造真值。

---

## 0) 第一性原理（hard）

- **唯一真值来源**：交易所可回查 JSON（orders / fills / bills / positions / equity）。
- **Execution + Ledger 的职责**：
  - Execution：提交请求（place/cancel/close），不做内部成交模拟。
  - Ledger：归档事实（append-only），提供最小真值特征给决策层。
- **唯一允许新增字段**：`agent_id`（归因）与 `clOrdId`（本地绑定键）。

---

## 1) 主键/外键（hard）

- **订单主键**：`ordId`（交易所生成）
- **本地绑定键**：`clOrdId`（我们生成；用于将 `agent_id` 绑定到订单）
- **成交主键**：`tradeId`（若可获取）
- **账单行主键**：通常为 `billId`/`id`（以 OKX 文档为准）；若账单行包含 `ordId`/`tradeId`，它们为强外键

结论：对账的“共同键”优先为 `ordId`（订单层共同键），账单行本身仍必须有独立主键用于去重/幂等。

**重要边界（避免漏洞）：**

- bills 里**不保证**每一行都有 `ordId`（例如资金费/划转/系统调整等类型可能没有可归因订单）；这些行仍是“系统级真值事件”，但**不可归因到某个 Agent 订单**。
- 同一个 `ordId` 可能对应**多条** bills 行（分笔费用/多次结算/部分成交），因此 bills 必须以 `billId`（或等价唯一键）去重与幂等。

---

## 2) 订单确认分层（P0–P5）

### P0) 绑定层（required）

- 下单请求必须带 `clOrdId`。
- `clOrdId` 必须与 `agent_id` 在本地 evidence 中绑定（append-only）。

### P1) Ack 层（required, not sufficient）

- `place_order` 返回 `sCode=0` 仅证明请求被接受，不证明成交/最终状态。
- 必须落盘：请求与响应的关键字段（至少 `clOrdId`、`sCode/sMsg`、HTTP status、latency、脱敏 `ordId` 信息若有）。

### P2) Order Status 层（required）

以交易所 JSON 为准轮询订单状态，直至：
- 达到终态（如 filled/canceled），或
- 超时（进入 degraded truth）

每次查询都必须 append-only 落盘（不得只记录最终态）。

### P3) Fills 层（recommended; required for fee/fill claims）

- 若要对“成交数量/成交价/手续费”下结论，必须能用 `ordId` 回查到 fills（包含 `tradeId` 等成交事实）。
- 若 fills 不可用或不可稳定回查：相关字段必须 `null + reason_code`，并将结论降级为 NOT_MEASURABLE（不得“猜测成交”）。

### P4) Bills 层（recommended; required for accounting closure claims）

- 若要对“费用/资金费/已实现 pnl/余额变化”做闭环结论，必须能回查 bills（按时间窗 + 分页）。
- 若 bills 行包含 `ordId`：以 `ordId` 进行归因 join；否则必须明确降级策略（NOT_MEASURABLE）。
  - 对于 **无 `ordId` 的 bills 行**：只能归为“系统级事件”，不得强行分摊到 Agent（除非另有交易所 JSON 提供可回查关联键）。

### P5) 最终一致性窗口（required）

允许异步延迟存在一个窗口（例如 \(T_{eventual}\)），但必须记录：
- `truth_quality`: `ok | degraded | unknown`
- `reason_code`: `timeout | rate_limited | api_error | paging_gap | demo_missing_field | ...`

超过窗口仍无法完成 P2（或需 P3/P4 的断言）：必须触发执行冻结（Execution sends 0 orders），避免继续污染证据。

---

## 3) 证据文件（最低要求）

以下均为 append-only（或一次性 manifest），不得重写既有记录。

- `order_attempts.jsonl`：P1 证据（每次下单/撤单请求）
- `order_status_samples.jsonl`（或 `.json` append-only）：P2 证据（每次状态查询）
- `fills_query_evidence.jsonl` / `fills_samples.json`：P3 证据（若做 fill/fee 结论）
- `account_bills_samples.jsonl`：P4 证据（若做账务闭环结论）
- `execution_fingerprint.json`：调用计数/错误率/延迟分布的统计摘要

**分页/完整性（hard，避免“漏页导致伪不一致”）：**

- 任何可分页端点（orders-history / fills / bills）必须落盘：
  - 请求参数（时间窗、cursor/after/before 等）
  - 响应返回的分页游标/hasMore（若有）
  - 每次响应的 `data_count`
- 若存在 `hasMore=true` 或游标未走到尽头即停止：相关结论必须降级为 `NOT_MEASURABLE`（因为无法证明“已完整拉取”）。

---

## 4) PASS / NOT_MEASURABLE / FAIL（裁决口径）

- **PASS（最小）**：所有 ack 的订单都能完成 P2（可回查到终态），且证据落盘可复核。
- **NOT_MEASURABLE**：
  - 需要 P3/P4 才能支持的结论，但对应接口不可用/字段缺失/超时，且已如实 `null + reason_code`。
- **FAIL（硬失败）**：
  - 出现内部伪造成交/伪造费用/伪造仓位变化（无交易所 JSON 证据仍写为真值）。
  - 发生 ack 后 P2 长期不可回查且仍继续发单（未进入执行冻结）。
  - evidence 非 append-only 或主键关联断裂（`clOrdId→ordId` 无法回指）。

---

## 5) Freeze（接口与语义冻结）

本协议通过 Gate4 后：
- 只允许向后兼容扩展（新增字段），禁止更改字段语义/类型。
- 破坏性变更必须提升版本并重跑最小 PROBE 与 Gate4 关键验收。


