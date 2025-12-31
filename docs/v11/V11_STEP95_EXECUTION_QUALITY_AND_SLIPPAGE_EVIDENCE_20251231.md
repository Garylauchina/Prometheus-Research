# V11 Step 95 — Execution Quality & Slippage Evidence (Mac Fixtures First) — SSOT — 2025-12-31

目的：当 V11 发生真实交易（OKX demo/live）时，必须能对“成交质量”做**逐项可核验**的证据化：成交/未成交原因、部分成交、滑点、订单簿厚度风险、延迟与分页闭合。  
说明（additive-only 追加）：在 **First Flight（truth-first）** 口径下，Step95 的“采信”必须以交易所真值落盘为前提；fixtures/模拟仅允许用于本地开发调试，不得作为验收依据。

本文件只允许追加（additive-only）。

---

## 1) Scope（冻结）

覆盖（Step95 要求可证）：
- **A. Terminal outcome**：filled / partial / cancelled / rejected / live（P2 终态）
- **B. Reasonability**：未成交/拒单原因（本地 gate / 交易所返回）
- **C. Partial fills**：多笔成交/部分成交的 join 与闭包
- **D. Slippage**：成交均价 vs 参考价（ref price）口径冻结
- **E. Orderbook thickness risk**：下单前订单簿快照用于解释滑点/无法成交
- **F. Latency**：submit→ack→first_fill→terminal 的延迟证据
- **G. Closure**：paging closure + evidence_refs 可解引用 + sha256 对齐

不覆盖（稳定窗口禁止）：
- 策略/演化机制大改（ROI 繁殖、tickless 主循环替换等）
- 复杂的市场冲击模型（只要求最小可解释，不要求高精度建模）

---

## 2) Core Principles（冻结）

- **Truth-first for First Flight**（additive-only 追加，冻结口径）：First Flight 阶段的 Step95 验收只采信真实对接交易所 demo 的 run_dir（必须落盘真值：orders_history；若 filled/partial 则 fills/bills 必须可 join）。fixtures/模拟仅用于开发调试与快速迭代，不得作为 PASS 依据。
- **Honest verdict**：不可测必须 NOT_MEASURABLE，并给出 reason_codes；不得靠推理宣称 PASS。
- **Additive-only**：只增文件/字段/verifier；不改旧证据语义。
- **Join keys first**：所有质量指标必须能按 `run_id` + `client_order_id/clOrdId` + `ordId` join（hash 只能辅助）。

---

## 3) Reference Price Contract（冻结）

### 3.1 ref price types

同一笔交易允许同时计算多个 ref price，但必须明确其来源与时刻：
- `ref_mid`：\((bestBid + bestAsk) / 2\)
- `ref_mark`：交易所 mark price
- `ref_index`：交易所 index price
- `ref_last`：last trade price（若可得）

### 3.2 sampling point

ref price / orderbook snapshot 的采样点必须声明：
- `t_submit`：client_submit_ts_ms（P0）
- `t_ack`：okx_ack_ts_ms（若可得）
- `t_first_fill`：fills.jsonl 最早 fillTime（若 filled）

### 3.3 slippage definition

对每个 ref_type：
- \(slippage\_bps = 10_000 \times (avgFillPx - refPx) / refPx\)（多空方向由 side/posSide 解释，不在此步骤强制统一符号）

若无法获得 refPx 或 avgFillPx：该 ref_type 的 slippage 必须标记 NOT_MEASURABLE，并给出 reason_codes（例如 `missing_orderbook_snapshot`）。

---

## 4) Required Evidence Artifacts（run_dir，冻结）

### 4.1 Inputs (existing, reused)

必须存在（若某项不存在则该项 NOT_MEASURABLE 或 FAIL，按 verifier 规则）：
- `order_attempts.jsonl`（P0）
- `order_status_samples.jsonl` 与/或 `orders_history.jsonl`（P2）
- `fills.jsonl`（P3，若 filled/partial）
- `bills.jsonl`（P4，若 filled/partial）
- `paging_traces.jsonl`（若有分页接口）
- `auditor_report.json`（P5）
- `agent_roster.json`（Step93，agent→genome anchors）

### 4.2 New artifacts (Step95, additive-only)

新增（推荐全部落盘；若缺失则对应项 NOT_MEASURABLE）：
- `execution_quality_summary.json`（run-level 汇总，machine-readable）
- `price_reference_snapshots.jsonl`（t_submit/t_ack/t_first_fill 的 ref price 快照）
- `orderbook_snapshots.jsonl`（t_submit/t_ack 订单簿快照，至少 top-of-book；可选 depth N）
- `slippage_records.jsonl`（per order 的 slippage 计算结果，按 ref_type）
- `latency_records.jsonl`（per order 的延迟分解）

证据引用：
- `execution_quality_summary.json` 内必须包含对上述 artifacts 的 evidence_refs（可解引用）。

---

## 5) Scenario Matrix（development helper; truth-first acceptance, additive-only note）

本 Step 的“开发期验证”不要求真实市场必然出现所有情况；fixtures 可用于生成场景以迭代 verifier。  
但在 **First Flight（truth-first）** 口径下：fixtures 产生的 run_dir **不得**作为 PASS 采信依据；用于验收的 run_dir 必须真实对接交易所并落盘真值。

最低场景集合（每个场景生成一个独立 run_dir）：

- S1: filled（单笔成交）
- S2: partial_fills（多笔成交，累计 fillSz == sz）
- S3: accepted_but_no_fill_then_cancel（挂单未成交→取消）
- S4: exchange_rejected（交易所明确拒单：含 s_code/s_msg/http_status）
- S5: local_rejected（本地 gate 拒绝：应有明确 reason_code，且不得伪装 exchange）
- S6: paging_incomplete（分页不闭合 → NOT_MEASURABLE，验证 honest verdict）
- S7: thin_orderbook_slippage（订单簿快照显示深度不足，slippage_bps 异常可解释）

说明：
- S4/S6 可以通过模拟的 exchange_api_calls fixtures 实现（不必真实打 OKX）。
- S7 允许只做 top-of-book + 简化解释（不要求完整冲击模型）。

---

## 6) Verifier Requirements（冻结）

新增 `verify_step95_execution_quality.py`（read-only）：

### 6.1 Terminal outcome checks
- 每个 attempt 必须能定位 terminal outcome（P2）；缺失则 FAIL（若因为 paging 不闭合则 NOT_MEASURABLE）。

### 6.2 Reason checks
- rejected/未成交必须能定位到 reason：
  - exchange_rejected：必须有 s_code/s_msg/http_status（来自 api_calls snapshot 或 orders_history state）
  - local_rejected：必须有明确 local reason_code，并不得标记为 exchange_rejected

### 6.2.1 Exchange auto-split fill/bill coverage (must)（冻结）

交易所可能把同一笔订单自动拆分为多笔成交/账单（同一 `ordId` 多条 fill/bill）。该行为 **不是错误**，但 Step95 v1 必须保证“覆盖完整性”：
- 对任一 terminal order（P2 可证）：
  - 若 state=filled/partially_filled：
    - `fills.jsonl` 中必须能找到该 `ordId` 的 ≥1 条记录
    - `bills.jsonl` 中必须能找到该 `ordId` 的 ≥1 条记录（若账单端点可用）
- **paging closure**：
  - 若存在分页端点（orders/fills/bills 任一）：必须有 `paging_traces.jsonl` 证明分页闭合；否则该项必须 NOT_MEASURABLE，并给出 reason_codes（建议：`paging_incomplete`）。

说明：
- 多条 fill/bill 是正常现象；我们不要求“聚合动作”，只要求按 join key 覆盖完整且分页闭合。
- 若权限/接口限制导致无法拿到 fills/bills：必须 NOT_MEASURABLE（不得推断“无成交/无账单”）。

### 6.3 Slippage checks
- 若 filled：必须至少对 ref_mid 或 ref_mark 其中之一给出 slippage_bps；否则 NOT_MEASURABLE 并给出原因（缺少 snapshot）。

### 6.4 Orderbook thickness checks
- 若提供 orderbook_snapshots：必须能将 snapshot 与订单按 t_submit/t_ack join。
- 若未提供：该项 NOT_MEASURABLE，不阻断其它项。

### 6.5 Latency checks
- 对每笔订单输出 latency 分解记录（可缺省某些阶段，但必须明确缺省原因）。

### Verdict rules（硬）
- 关键闭环缺失（P0/P2 join 不成立、refs 不可解引用、sha256 不对）→ FAIL
- 因分页/权限/快照缺失导致不可测 → NOT_MEASURABLE（必须写 reason_codes）
- 其余 PASS

---

## 7) Acceptance Plan（冻结）

Phase A（Mac fixtures）：
- 跑 S1–S7 的 demo（每个场景一个 run_dir）
- 跑 Step88/93/95 verifiers（应按场景得到 PASS/NOT_MEASURABLE/FAIL 的预期）

Phase B（VPS demo truth sampling）：
- 每周抽样 1 次真实 run（或 one-shot），验证：
  - filled 的 slippage_bps 可测（至少一种 ref）
  - orderbook snapshot 若启用可解释

---

## 8) Change Log（追加区）

- 2025-12-31: 创建 Step95 SSOT（执行质量与滑点证据：Mac fixtures first + verifier）。


