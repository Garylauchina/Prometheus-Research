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

补充（观测纪律，冻结）：
- **Outcome-neutral**：交易成功/失败都属于真实样本，都是演化与环境交互的一部分；不以“必须成功成交”作为系统评价标准。
- **Recording-first**：系统的硬要求是“记录可审计的真值链路”：每次尝试必须落盘其结果（成功/拒绝/超时/不可测量）以及原因与证据回指；**不记录才是缺陷**。

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

### 7.2 Agent-facing Feedback Projection（可选扩展，冻结口径）

动机：
- “失败”是演化的重要环境反馈，但失败原因分布极其长尾；若把所有细节直接喂给 Agent，容易造成高维噪声与过拟合。
- 因此需要一个 **稳定、低维、可审计** 的投影，把 Step96 的事件空间映射为“Agent 可消费”的反馈输入。

原则（冻结）：
- **先粗后细**：Agent 默认只吃粗粒度信号；细粒度只用于审计/人工诊断，或作为后续可选增强。
- **稳定 vocabulary**：投影字段必须来自 Step96 的稳定 `classification/reason_code/bucket_key`，不得依赖自由文本 message。
- **可回指**：任何投影出来的计数/状态，都必须能回指到 `exchange_error_events.jsonl` 的 bucket_key 或示例 evidence。

建议的三层粒度（v0，冻结）：
- **L0（结果态 / outcome）**：仅表达“是否发生 write-side attempt + 其终态”
  - allowed: `success` / `partial_success` / `failed` / `in_progress` / `not_measurable`
- **L1（粗分类 / coarse class）**：表达失败来自哪里（生态围栏 vs 本地门控 vs 真值缺口）
  - allowed: `exchange_error` / `exchange_rejected` / `local_reject` / `truth_gap`
- **L2（稳定原因 / stable reasons）**：用 top-K bucket_key（或 reason_code）表达最近最重要的约束
  - 使用 Step96 `bucket_key`（推荐）或 `{classification}:{reason_code}`（简化版）

窗口定义（v0，冻结）：
- v0 版本先 **硬编码为上一 tick（t-1）窗口**：所有 “last_* / prev_* / group_*_prev” 的统计默认只覆盖上一 tick 内发生的 attempts（若该 tick 内无 attempts，则视为该信号不可用）。
- 不可用处理（hard）：上一 tick 无事件/无真值 → `mask=0`（或字段为 null + reason_code），不得伪造为 0。
- 未来版本允许扩展为“事件窗/扫描周期”（tickless / event-driven），但必须以 additive-only 方式引入新字段（例如 `window_kind`/`window_span_ms`），并在 run_manifest 中冻结扫描周期与代谢/行动频率口径。

L0（结果态）判定规则（v0，冻结，truth-first）：
- 目标：用“请求数量 vs 成交数量（fills 汇总）+ 订单终态”做稳定判定，不引入主观描述。
- 输入真值：
  - `requested_sz`：来自 `order_attempts.jsonl` 的请求数量（合约张数 sz）
  - `filled_sz`：来自 `fills.jsonl`（同一 `ordId` 或 `clOrdId`）的成交数量汇总
  - `terminal_state`：来自 `orders_history.jsonl`（或订单终态快照）的 state
- 判定：
  - `success`：`filled_sz >= requested_sz` 且 order 为终态（例如 filled）
  - `partial_success`：`0 < filled_sz < requested_sz` 且 order 为终态（例如部分成交后取消/过期/被 1000 maker 限制截断等）
  - `failed`：`filled_sz == 0` 且 order 为终态且未成交（rejected/canceled/expired 等）
  - `in_progress`：run 结束时仍非终态（live/open/partially_filled 但仍挂单）
  - `not_measurable`：缺失 fills/orders_history 真值或 paging 不闭合，导致无法可靠计算 filled_sz 或终态
- 约束：
  - 任何 `partial_success` 必须能回指 fills/bills 证据（否则一律 not_measurable）
  - 若交易所发生“自动拆分/多笔 fills”，filled_sz 以汇总为准；若 paging 不闭合则 not_measurable（并写 TRUTH_PAGING_INCOMPLETE）

补充：单标量“成功率 / fill_ratio”（v0，冻结，truth-first）：
- 定义：`fill_ratio = clamp(filled_sz / requested_sz, 0.0, 1.0)`，其中：
  - `requested_sz` 来自一次 write attempt 的请求数量（合约张数）
  - `filled_sz` 来自同一次 attempt 对应的 fills 真值汇总
- 语义：
  - `fill_ratio = 0.0`：未成交（或最终未产生任何 fills）
  - `fill_ratio = 1.0`：完全成交
  - `0.0 < fill_ratio < 1.0`：部分成交
- NOT_MEASURABLE：
  - 若缺失 fills/orders_history 真值，或 paging 不闭合导致 `filled_sz` 不可信，则 `fill_ratio=null` 并写 Step96 `TRUTH_PAGING_INCOMPLETE`/`TRUTH_MISSING_SNAPSHOT`

投影输出建议（可选新增 artifact，additive-only）：
- `agent_feedback_summary.json`（run-level，read-only 汇总，不替代 jsonl）
  - `run_id`
  - `time_window_utc`: {`start`, `end`}
  - `attempt_counts`:
    - `total_write_attempts`
    - `success`
    - `partial_success`
    - `failed`
    - `not_measurable`
  - `coarse_counts`（L1 聚合）：{`exchange_error`, `exchange_rejected`, `local_reject`, `truth_gap`}
  - `top_buckets_last_N`：[{`bucket_key`, `count`, `example_evidence`}]（N 建议 10–50，避免高维）

建议追加字段（使 Agent 可直接查询“上次成功率”，v0）：
- `last_attempt_by_agent`：{agent_id_hash: {...}}
  - `last_client_order_id`（clOrdId，可为 null）
  - `last_ordId`（可为 null）
  - `last_outcome`：L0 结果态（success/partial_success/failed/in_progress/not_measurable）
  - `last_fill_ratio`：float|null（见上；NOT_MEASURABLE 时为 null）
  - `last_bucket_keys`：string[]（可选，保留 0–3 个最关键 bucket，供调试/审计）

### 7.3 Genome dimension suggestion (minimal, additive-only)

目的：
- 你提出的底层逻辑是“Agent 能读到上次交易 fill_ratio（0~1）并影响下一次决策”。
- 为避免基因直接编码交易所细节，基因只控制“如何使用这个反馈”，而不是控制错误类别。

建议新增一个基因维度（v0）：
- `fill_feedback_weight` ∈ [0, 1]
  - 语义：Agent 在本次决策中，对 “last_fill_ratio” 的关注强度/权重（0=忽略，1=强依赖）
  - 落盘要求：必须进入 `agent_roster.json` 的 genome anchors（已有 Step93 roster 纪律），并在 `decision_trace.jsonl` 里显式写出该基因值（或其派生参数）

冻结口径（与你当前确认一致）：
- **基因终身不变**：该权重在 Agent “出生→死亡”生命周期内保持不变；只能通过繁殖/变异产生新个体时改变（不得 per-tick 漂移）。
- **无事件不参与**：若上一 tick/事件窗没有可用的交易真值反馈（fill_ratio 不可测或无交易），该通道必须 `mask=0`，即使权重很大也不得参与决策。
- **初始化分布**：新生个体默认从 `Uniform(0, 1)` 初始化该权重（避免主观偏置）。
- **变异方式（建议）**：在繁殖时对该权重做小幅扰动后 clamp 回 \([0,1]\)（例如 `w' = clamp(w + ε, 0, 1)`；ε 可取零均值小噪声），避免大跳变。

追加：群体执行反馈权重（v0，additive-only）
- `group_fill_feedback_weight` ∈ [0, 1]
  - 语义：Agent 对 “上一 tick 的群体 fill_ratio 聚合值（group_fill_ratio_prev_tick）” 的关注强度
  - 纪律：同上（终身不变 / 无事件 mask=0 / Uniform 初始化 / 小幅变异）
  - 说明：该权重与 `fill_feedback_weight`（个体自身 last_fill_ratio）正交，便于做单项消融（只开 self / 只开 group / 都开 / 都关）。

群体聚合口径（v0，冻结）：
- `group_fill_ratio_prev_tick = mean(self_fill_ratio_prev_tick over population)`（均值）
- 我们不把该聚合器定义为“抗黑天鹅功能”；它只是一个简单、可复现的群体反馈统计口径。

注意（冻结）：
- v0 不要求立刻做复杂学习；只要求：**fill_ratio 真值可得、可回指、可被决策读取**。

落盘/接入点（建议，非强制）：
- Decision 输入快照里引用该 summary（例如 `decision_trace.jsonl.input_context.agent_feedback_ref` 指向文件）
- 或在 features contract 中新增极少量维度（例如 4 维 coarse_counts 的近期窗口归一化值 + mask），坚持 additive-only

边界（冻结）：
- v0 不要求把“失败原因”做成可学习 embedding；只要求低维、稳定、可审计。

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


