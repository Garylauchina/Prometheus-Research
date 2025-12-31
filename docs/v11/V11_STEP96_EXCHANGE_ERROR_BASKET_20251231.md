# V11 Step 96 — Exchange Error Basket (Trader “Error Bucket”) — SSOT — 2025-12-31

目的：为真实交易（OKX demo/live）建立一个**可持续演进**的“交易所错误篓子”机制：把运行过程中遇到的交易所错误、写侧失败、真值不可测量原因，统一落盘为**可机读、可聚合、可回指证据**的记录。后续我们可以依赖该机制逐步排除意外情况（滑点/深度/权限/风控/参数/分页不闭合等），而不靠聊天推理。

本文件只允许追加（additive-only）。

---

## 1) Scope（冻结）

覆盖：
- 写侧（place/cancel/replace/flatten）失败或被拒绝
- 交易所响应错误（HTTP/OKX code/message）
- 真值不可测量（NOT_MEASURABLE）原因（例如分页不闭合、权限不足、缺少 ref snapshot）
- 本地 gate 拒绝（freeze/risk/invalid_desired_state 等），但必须与“exchange rejected”区分

不覆盖：
- 策略好坏判断（收益/回撤）本身
- 复杂统计建模（只要求可解释的证据入口）

---

## 2) Design Principles（冻结）

- **Evidence-first**：每条错误必须能回指 run_dir 内的证据（evidence_refs 或 file/line）。
- **Join-first**：必须能按 `run_id + client_order_id(clOrdId) + ordId(optional)` join 回交易链。
- **Dedup-friendly**：同类错误要能聚合统计（error_fingerprint / bucket_key）。
- **Honest verdict**：不可测量必须 NOT_MEASURABLE 并给出 reason_codes；不得硬报 PASS。
- **Additive-only**：只增字段/文件/verifier；不改旧语义。

补充（First Flight，truth-first，冻结口径）：
- First Flight 阶段，任何“模块测试 run”若未落盘交易所真值（至少 `orders_history.jsonl`；若 filled 则 `fills.jsonl`/`bills.jsonl`）则该 run **一概不采信**。
- 对应落盘要求若缺失：必须写入 `exchange_error_events.jsonl` 一条 `event_type=not_measurable`（或 `warning`）记录，推荐：
  - `classification=TRUTH_MISSING_SNAPSHOT`
  - `reason_code` ∈ {`missing_orders_history`, `missing_fills`, `missing_bills`}
  - scope 按实际：`system`（因为这是 run 级别真值缺口）

---

## 3) Required Artifacts（run_dir，冻结）

新增文件（Step96）：

### 3.1 `exchange_error_events.jsonl`（append-only）

每一条“值得记录的错误/不可测量原因”写一行 JSON。

最小字段（必须）：
- `ts_utc`
- `run_id`
- `tick`（可为 null）
- `event_type`：`exchange_error` / `local_reject` / `not_measurable` / `warning`
- `operation`：`place` / `cancel` / `replace` / `flatten` / `query`
- `scope`：`agent` / `system`
- `agent_id_hash`（scope=system 时必须为 null）
- `lifecycle_scope`（system 时必填，例如 `system_flatten`）
- `client_order_id`（clOrdId，可为 null，但如果是 write-path error 应尽量存在）
- `ordId`（可为 null）
- `classification`：稳定 vocabulary（见 §4）
- `reason_code`：稳定 vocabulary（短码，机器友好）
- `message`：人类可读补充（可选）
- `evidence`：
  - `evidence_file`
  - `evidence_line`
  - `evidence_refs`（可选；若存在必须可解引用）

交易所字段（仅当 event_type=exchange_error 时）：
- `http_status`（int|null）
- `exchange_code`（string|null，例如 OKX `sCode`）
- `exchange_msg`（string|null）
- `endpoint`（string|null）

聚合字段（必须）：
- `bucket_key`：string（用于统计聚合；规则见 §5）

### 3.2 `exchange_error_basket.json`（run-level summary）

目的：给交易员一个“一眼能看懂”的错误汇总入口（不替代 jsonl）。

最小字段：
- `run_id`
- `time_window_utc`：{`start`, `end`}
- `counts_by_bucket`：{bucket_key: count}
- `top_examples`：每个 bucket_key 给出 1–3 条 example（含 evidence refs）
- `not_measurable_reasons`：聚合的 reason_codes（若有）

---

## 4) Classification Vocabulary（冻结，初版）

`classification` 初始允许值（可追加）：
- `EXCHANGE_HTTP_ERROR`
- `EXCHANGE_REJECTED`
- `EXCHANGE_ACCOUNT_MODE`
- `EXCHANGE_PERMISSION`
- `EXCHANGE_RATE_LIMIT`
- `EXCHANGE_PARAM_INVALID`
- `EXCHANGE_INSTRUMENT_INVALID`
- `LOCAL_GATE_REJECTED`
- `LOCAL_INVALID_DESIRED_STATE`
- `TRUTH_PAGING_INCOMPLETE`
- `TRUTH_MISSING_SNAPSHOT`

`reason_code` 初始允许值（可追加）：
- `http_error`
- `exchange_rejected`
- `account_mode_restricted`
- `permission_denied`
- `rate_limited`
- `param_invalid`
- `instrument_invalid`
- `freeze_reject`
- `risk_reject`
- `invalid_desired_state`
- `paging_incomplete`
- `missing_ref_snapshot`

---

## 5) bucket_key Definition（冻结）

bucket_key 用于“同类错误聚合”，必须稳定且可预测：

建议规则（初版）：
- 若 event_type=exchange_error：
  - `bucket_key = "{classification}:{http_status}:{exchange_code}:{endpoint}"`
- 若 event_type=local_reject：
  - `bucket_key = "{classification}:{reason_code}"`
- 若 event_type=not_measurable：
  - `bucket_key = "{classification}:{reason_code}"`

注意：
- `message` 不参与 bucket_key（避免噪声导致无法聚合）
- endpoint 可做裁剪（只保留路径，不含 query）

---

## 6) Verifier Gate（冻结）

新增 `verify_step96_exchange_error_basket.py`（read-only）：

检查：
- 若存在 `exchange_error_events.jsonl`：
  - 每条记录满足 schema
  - bucket_key 非空且符合规则
  - evidence_refs 若存在必须可解引用
- 若存在 `exchange_error_basket.json`：
  - counts_by_bucket 与 events 聚合一致
  - top_examples 的 evidence 可解引用

Verdict：
- schema/refs/聚合不一致：FAIL
- 文件缺失：PASS（Step96 未启用不阻断），但若 run 中出现 exchange_error 却没有落盘 Step96，则应在 Step93 incident 中记录缺口（运营纪律）。

---

## 7) Integration Requirements（冻结）

写入点（最小）：
- BrokerTrader/connector 写侧：遇到 exchange error / local reject / not measurable，写一条 `exchange_error_events.jsonl`
- Auditor/verifier：遇到 NOT_MEASURABLE 原因（分页不闭合等），也应写入（scope=system，operation=query）

注意：
- `L1_EXCHANGE_REJECTED` 只能用于真实交易所响应；本地 skip/本地判定必须归类为 LOCAL_*（避免伪装真值）。

### 7.1 First-class bucket: paging closure / auto-split coverage（冻结）

交易所自动拆分（同一 `ordId` 多笔 fills/bills）是常态；交易员关心的不是“有没有拆分”，而是“我们是否拿全了”。

因此 v1 必须先落地这一类错误篓子事件：
- 若 fills/bills/orders 任一端点存在分页：
  - 只要分页未闭合（hasMore 未走完、游标未收敛、或 paging_traces 缺失导致无法证明闭合）：
    - event_type=`not_measurable`
    - classification=`TRUTH_PAGING_INCOMPLETE`
    - reason_code=`paging_incomplete`
    - operation=`query`
    - scope=`system`

并在 basket 中聚合为交易员可行动的 bucket（频次 + 例子）。

---

## 8) Acceptance Plan（冻结）

Phase A（Mac fixtures）：
- 用 mock api_calls + 固定错误码生成 3 类 bucket（param_invalid / rate_limit / paging_incomplete）
- 跑 Step96 verifier PASS

Phase B（VPS demo）：
- 每周抽样 1 次：若出现任何 exchange_error / not_measurable，必须能在 basket 中看到聚合与 example refs

---

## 9) Change Log（追加区）

- 2025-12-31: 创建 Step96 SSOT（交易所错误篓子：events.jsonl + basket summary + verifier）。


