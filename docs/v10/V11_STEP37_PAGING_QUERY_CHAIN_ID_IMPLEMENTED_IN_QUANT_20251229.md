# V11 Step 37 — paging query_chain_id/scope_id Implemented in Quant — 2025-12-29

目的：记录 Step 37（为 paging_traces 增加 `scope_id/query_chain_id` 并在 verifier 中对“混链” fail-closed）已在实现仓库（Prometheus-Quant）落地，并冻结其审计锚点。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP37_PAGING_QUERY_CHAIN_ID_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`1ab1180`
- message：`v11: add paging query_chain_id/scope_id and fail mixed-chain proofs in verifier`

实现仓库摘要（关键点）：
- ExchangeAuditor：
  - 生成 `scope_id`（每次审计执行唯一）
  - 生成 `query_chain_id`（基于 endpoint_family|inst_id|start_ms|end_ms|scope_id|sequence_no 的短 hash）
  - `paging_traces.jsonl` 每条记录落盘 `scope_id/query_chain_id`（additive-only）
  - `auditor_report.paging_coverage` 追加 `scope_id/query_chain_id`
- Evidence verifier：
  - 对每个 endpoint_family 的 `line_range` 做逐行一致性校验：
    - endpoint_family 一致
    - scope_id 一致
    - query_chain_id 一致
  - 任一混链 → exit 1（FAIL，用于 CI 与 run-end gate）
- CI fixture：
  - paging_traces/auditor_report 同步加入 scope_id/query_chain_id，验证 PASS 与混链 FAIL 场景

---

## 2) 冻结的 hard 口径（与 Step 37 Spec 一致）

- 当 `closure_proved=true`：
  - `scope_id/query_chain_id` 必须非空
  - `paging_traces_line_range` 内不得出现混链（不同 scope_id 或不同 query_chain_id）
  - 混链必须 FAIL（不可绕过）


