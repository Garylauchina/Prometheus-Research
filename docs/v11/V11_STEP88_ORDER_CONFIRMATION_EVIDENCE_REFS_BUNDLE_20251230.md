# V11 Step 88 — Order Confirmation Protocol (P0–P5) EvidenceRefs Bundle — SSOT — 2025-12-30

目的：把“真实订单确认链”（P0–P5）纳入 Step87 的通用证据链体系：EvidenceRefs + backfill view + sha256_16 + range 同质性 + paging closure proof，形成可审计、可验真的最小闭环。

本文件只允许追加（additive-only）。

前置：
- Step 33-37：fills/bills join + paging_traces + query_chain_id/scope_id
- Step 41-46：EvidenceRefs 标准 + hardening + dereference + bundle freeze
- Step 87：Generic evidence refs bundle（paging/auditor artifacts）

---

## 1) P0–P5 的最小可测定义（冻结）

对每一笔“下单 intent”（或系统 lifecycle 写操作），至少需要证明：

- **P0 Intent Recorded**：意图与归因落盘（`order_attempts.jsonl`）
- **P1 Ack**：交易所返回可识别的 ack（通常含 `ordId` 或等价字段）并可被引用
- **P2 Terminal Status**：该订单进入终态（filled/canceled/rejected 等），且可被引用
- **P3 Fills Closure**：fills 侧能闭包（paging closure proved），并能 join 到 `ordId`
- **P4 Bills/Fee/PnL Closure**：bills 侧能闭包（paging closure proved），并能 join 到 `ordId`/`tradeId`（以 OKX 字段为准）
- **P5 Post-run Auditor Join**：auditor 报告能引用上述证据范围并给出 PASS/NOT_MEASURABLE/FAIL（truthful）

注：Step88 不要求一定发生真实成交（filled），但必须证明 **状态链闭包**（P2）与 **查询链闭包**（P3/P4 的 paging closure）。

---

## 2) 必需证据文件（冻结：最小集合）

执行侧（execution evidence）：
- `order_attempts.jsonl`
- `order_status_samples.jsonl`（或等价的状态采样/确认文件）

交易所真值侧（truth evidence）：
- `fills.jsonl` / `fills_raw.jsonl`（以 Quant 实际命名为准）
- `bills.jsonl` / `bills_raw.jsonl`（以 Quant 实际命名为准）
- `orders_history.jsonl` / `orders_history_raw.jsonl`（可选但推荐）

审计侧（audit evidence）：
- `paging_traces.jsonl`（必须：证明 paging closure）
- `auditor_report.json`（必须）
- `auditor_discrepancies.jsonl`（若有差异则必须）

---

## 3) Join Keys（冻结：最小 join 主键）

必须冻结以下 join 键（以 OKX 为准，字段名以 Quant 实际 schema 冻结）：
- `clOrdId`（本地 client order id，必须带 namespace）
- `ordId`（交易所订单主键）
- `tradeId`（成交主键，用于 fills/bills）
- `billId`（账单主键）

最小 join 规则（冻结）：
- `order_attempts` 必须能定位到一个 `clOrdId`
- `clOrdId -> ordId` 必须可证（通过 ack/status/orders-history 任一真值侧证据）
- `fills` 中的每条记录必须可 join 到 `ordId`（以及 tradeId 的幂等性）
- `bills` 中的每条记录必须可 join 到 `ordId` 或 `tradeId`（以 OKX 规则为准），并具备 billId 幂等性

---

## 4) EvidenceRefs / Backfill / sha256 / Range（继承并强制）

对以上证据文件：
- Evidence Gate enabled 时：
  - evidence_refs 必须满足 hardening（line_range + sha256_16）
  - 允许使用 backfill view（Step85/86）回填 sha256_16
  - range 引用必须满足同质性（Step84），尤其是 `paging_traces` 的 query_chain_id/endpoint_family 同质性（Step87）

---

## 5) Paging Closure Proof（冻结）

P3/P4 必须证明 paging closure：
- 对每个 endpoint_family（orders_history/fills/bills），必须存在一条或多条 paging trace
- 在 `paging_traces.jsonl` 中必须证明 closure（hasMore=false 或等价闭包条件）
- trace range 必须同质（scope_id/query_chain_id/endpoint_family/inst_id 等，按 Step87）

---

## 6) Verifier（Step88，新增规则）

新增 verifier（或扩展现有 auditor verifier），最小必须校验：
- P0：存在 order_attempts 记录（且归因 anchors 完整）
- P1/P2：存在 ordId 并终态可证（order_status_samples 或 orders_history 真值）
- P3：fills paging closure proved + ordId join 完整
- P4：bills paging closure proved + ordId/tradeId join 完整
- P5：auditor_report evidence_refs 可解引用到上述文件范围，并与 run_id/audit_scope_id 一致

失败语义（冻结）：
- join 断裂 / paging closure 缺失 → FAIL（exit 2 或 CI FAIL，按 bundle 约定冻结）
- truth 不可测（例如 demo 限制）→ NOT_MEASURABLE（但必须带 reason_codes 与 evidence_refs）

---

## 7) Fixture（PASS/FAIL 必须具备）

PASS fixture（最小）：
- 至少 1 个订单样本，在文件级别满足 P0–P5 的可引用闭环（即使无真实成交也必须 P2 终态 + paging closure）

FAIL fixture（最小）：
- 构造缺失 paging_traces 或 ordId join 断裂 → verifier 必须 fail-closed


