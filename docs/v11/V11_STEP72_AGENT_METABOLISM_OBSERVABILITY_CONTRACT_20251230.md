# V11 Step 72 — Agent Metabolism Observability (Fact-Only, Non-Genetic) — SSOT — 2025-12-30

目的：在不改动基因/特征向量/DecisionEngine 的前提下，为后续演化观察增加一个 **个体代谢（metabolism）** 的 fact-only 观测输出：描述每个 Agent 在一个 run 内“消耗/摩擦/执行负担”的可复核统计。

本 Step 明确约束：
- **不新增 probe 维度**，不进入 DecisionEngine 输入。
- **不修改 Genome/Agent 的语义**。
- 输出仅作为 research_bundle 的附加事实产物（additive-only）。

---

## 1) 概念边界（冻结）

“代谢”只允许表示 **可审计的成本/频次/执行摩擦统计**，不得表达解释性/因果性/策略性结论。

代谢拆分为两层（冻结）：

- **M_intent（意图代谢，always measurable）**
  - 数据源：`decision_trace.jsonl`
  - 语义：Agent 在 tick 序列中表达了多少次 open/close/hold 意图（及其强度/置信度若存在）
  - 不依赖交易所真值

- **M_exec（执行代谢，truth-dependent）**
  - 数据源：BrokerTrader + ExchangeAuditor 的 orders/fills/bills（及其 evidence chain）
  - 语义：实际成交次数/成交量、手续费、拒单率、延迟、撤单等
  - 依赖真值与 join 完整性；不可测必须写实为 NOT_MEASURABLE（不得当 0）

---

## 2) 输入数据（冻结）

### 2.1 必需输入（M_intent）
- `decision_trace.jsonl`
  - 必须可按 `agent_id_hash` 聚合（或可推导的 agent 标识）
  - 必须包含 tick 序列（或可推导 tick）

### 2.2 可选输入（M_exec）
- orders/fills/bills 相关审计/证据（建议使用已对齐的审计 artifacts）：
  - `order_attempts.jsonl` / `order_status_samples.jsonl`（如存在）
  - ExchangeAuditor 输出（如存在）：`auditor_report.json` / `auditor_discrepancies.jsonl`
  - paging traces（如存在）：`paging_traces.jsonl`

归因硬规则（冻结）：
- 任何 M_exec 指标必须能通过 `agent_id_hash` 或等价锚点归因；无法归因 → NOT_MEASURABLE。

---

## 3) 输出产物（冻结）

输出目录（推荐但不强制）：`research_bundle/`

### 3.1 逐 tick 输出（可选）
- `agent_metabolism_ticks.jsonl`
  - 每行一个 tick（或 tick+agent 组合），仅包含事实字段
  - 可用于时间序列分析与窗口统计

### 3.2 run 汇总输出（必需）
- `agent_metabolism_summary.json`
  - fact-only 汇总：对每个 agent 输出窗口统计（counts/ratios/fees 等）
  - 必须包含 `measurement_status`（见下一节）

并纳入：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`
- `research_bundle/entry.json`（Step67）应把这些产物列入 `artifacts[]`

---

## 4) measurement_status（冻结）

任何输出（ticks/summary）中，涉及 truth-dependent 的字段必须同时携带可测性标记：

- `measurement_status` 词表（冻结）：
  - `MEASURABLE`
  - `NOT_MEASURABLE`

规则（冻结）：
- 若缺少真值、缺少 join、缺少归因、或审计 verdict 为 NOT_MEASURABLE/FAIL，相关 M_exec 字段必须为 `null` 且 `measurement_status="NOT_MEASURABLE"`，并给出 `reason_codes[]`。
- **严禁**用 0 伪装 unknown。

---

## 5) 最小指标集合（冻结）

### 5.1 M_intent（必需，MEASURABLE）
对每个 `agent_id_hash`：
- `intent_open_count`
- `intent_close_count`
- `intent_hold_count`
- `intent_action_rate = (open+close)/ticks_observed`（若 ticks_observed 可得）

### 5.2 M_exec（可选，truth-dependent）
若可测，对每个 `agent_id_hash`：
- `orders_submitted_count`
- `orders_rejected_count`
- `fills_count`
- `fee_paid_total`（按币种/单位写实，若不可统一则拆分）
- `p2_latency_ms_p50` / `p2_latency_ms_p95`（若有 monotonic latency evidence）

---

## 6) Manifest 记录（additive-only，冻结）

在 `run_manifest.json` 增加：

```json
{
  "agent_metabolism": {
    "enabled": true,
    "summary_rel_path": "research_bundle/agent_metabolism_summary.json",
    "ticks_rel_path": "research_bundle/agent_metabolism_ticks.jsonl",
    "m_exec_enabled": true,
    "status": "pass"
  }
}
```

`status` 词表（冻结）：`pass|fail|skipped`

---

## 7) 失败语义（冻结）

本 Step 默认 **不作为 fail-closed gate**（只做观测输出），但必须满足写实原则：
- M_intent 无法生成 → `status="fail"`（建议同时写入 errors.jsonl）
- M_exec 不可测 → `m_exec_enabled=true` 但在 summary 中写 `NOT_MEASURABLE`（不是 fail）

---

## 8) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + 样例 summary + entry.json 引用片段）


