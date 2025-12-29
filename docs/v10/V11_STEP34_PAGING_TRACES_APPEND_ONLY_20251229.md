# V11 Step 34 — Paging Traces (Append-only Evidence for Closure Proof) — 2025-12-29

目的：把“分页闭合（paging closure）”从口头承诺升级为 **可复核证据**：  
对所有可分页端点（orders-history / fills / bills），每次请求/响应的分页状态必须 append-only 落盘，形成 `paging_traces.jsonl`，并纳入证据包 hash/index。

背景问题：  
在 execution_world 中，“未走完分页却提前停止”会导致：
- 误判 orphan / 误判缺失本地记录（伪不一致）
- 误报 PASS（不可证明完整性）
因此分页闭合必须可证明，否则相关结论只能 NOT_MEASURABLE。

SSOT 关联：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`（分页/完整性 hard rules）
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP33_FILLS_BILLS_JOIN_MIN_MEASURABLE_20251229.md`

---

## 1) 产物与命名（冻结）

新增证据文件（run_dir 内）：
- `paging_traces.jsonl`（append-only）

必须纳入：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`

---

## 2) 最小字段（每条记录必须包含）

每一条 paging trace 代表“一次分页请求/响应”：
- `ts_utc`
- `run_id`
- `audit_component`：`exchange_auditor | broker_trader | ledger`（谁发起的只读查询）
- `endpoint_family`：`orders_history | fills | bills`
- `inst_id`（若适用）
- `time_window`：`start_ms` / `end_ms`（或等价时间锚）
- `page_idx`（从 1 开始）
- `request_params`（脱敏后的关键参数：after/before/cursor/limit）
- `response_meta`：
  - `data_count`
  - `has_more`（若交易所提供）
  - `next_cursor` / `after` / `before`（若交易所提供）
- `http_status`（若可得）
- `okx_s_code` / `okx_s_msg`（若可得）
- `truth_quality`：`ok | degraded | unknown`
- `reason_code`（当 truth_quality != ok 或分页未闭合时必须）

---

## 3) 闭合判定（proof rule）

对每个（endpoint_family, inst_id, time_window）查询链，必须能用 paging_traces 证明：
- **闭合（closure）**：最后一页 `has_more=false`（或游标耗尽的等价条件）
- 或明确 **不可闭合**：记录为 NOT_MEASURABLE（例如超时/限频/字段缺失）

硬规则：
- 缺少 paging_traces → 与分页相关的结论一律 NOT_MEASURABLE（不得 PASS）
- paging_traces 显示未闭合（has_more=true 但停止）→ 相关结论 NOT_MEASURABLE

---

## 4) 与 Step 32/33 的关系（裁决口径）

- Step 32（orders-level orphan detection）：
  - orders-history 未闭合 → orphan detection NOT_MEASURABLE（不得 PASS）
- Step 33（fills/bills join）：
  - fills 未闭合 → fills check NOT_MEASURABLE
  - bills 未闭合 → bills check NOT_MEASURABLE

---

## 5) 实现要求（Quant）

实现仓库必须：
- 在 ExchangeAuditor 的 orders-history / fills / bills 查询中落盘 paging_traces.jsonl
- 任何提前退出/异常必须写 `truth_quality` + `reason_code`
- gate（run-end / CI）必须要求 paging_traces 存在且覆盖本次审计范围，否则降级 NOT_MEASURABLE


