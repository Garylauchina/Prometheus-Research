# V11 Step 72.2 — Metabolism Pre-Implementation Checklist & Lifespan Views (De-fence) — SSOT — 2025-12-30

目的：在实现 Step72（代谢观测）之前，冻结一份 **必要且可行** 的实施前检查清单，并把“寿命（lifespan）”从隐性围栏中拆出来：用事实可复核的三视角 \(L_{time}, L_{exec}, L_{budget}\) 来描述个体表型（只观察，不反向影响决策/判定）。

本文件只允许追加（additive-only）。

关联：
- Step72：`docs/v11/V11_STEP72_AGENT_METABOLISM_OBSERVABILITY_CONTRACT_20251230.md`
- Step72.1：`docs/v11/V11_STEP72_1_AGENT_METABOLISM_CANDIDATES_AND_FILTER_20251230.md`

---

## 1) 去围栏原则（冻结）

本系列“代谢/寿命”定义的目标是 **去围栏（de-fence）** 而不是加围栏：
- 只新增 fact-only 观测输出；
- 不改变死亡/繁殖判定规则；
- 不进入基因/不进入 probe/不进入 DecisionEngine；
- 不把不可测当作 0（严格 `NOT_MEASURABLE + null`）。

---

## 2) 实施前 Checklist（冻结）

### 2.1 证据可用性（必须）
- `decision_trace.jsonl` 可读取、可按 `agent_id_hash` 聚合、tick 范围写实可追溯。
- `research_bundle/` 与 `entry.json` 链路完整（Step65/67/68/69 已冻结）。

### 2.2 归因完整性（必须）
- 任一“agent-level”指标必须能归因到 `agent_id_hash`：
  - 若只能 world-level：必须明确降级，并把 agent-level 结果标为 `NOT_MEASURABLE`。
- 若 M_exec/M_resource 依赖外部真值 join：join 不完整必须 `NOT_MEASURABLE`。

### 2.3 可测性与写实规则（必须）
- truth-dependent 字段：不可测 → `null` + `measurement_status="NOT_MEASURABLE"` + `reason_codes[]`。
- 严禁用 0 伪装 unknown。

### 2.4 采集成本上限（必须）
- 默认只产出 summary（run 汇总）；ticks 级输出为可选项。
- 采集与写盘不得显著拉长 tick（若有明显影响必须在 manifest 写实记录“measurement_overhead”说明）。

### 2.5 与基线隔离（必须）
- 不修改 feature/probe contract、不触发 Step52 对齐链路。
- 不改 LifecycleJudge 的制度；寿命视角只用于研究解释与分组。

### 2.6 验收最小用例（必须）
- 在 CI 的 `runs_step54_test`（或等价 fixtures）上，能够生成：
  - `research_bundle/agent_metabolism_summary.json`
  - 并在 `research_bundle/entry.json` 中被索引（带 sha256_16/byte_size 可复核）。

---

## 3) “寿命”三视角（冻结）

寿命不定义为单一标量阈值，而定义为三个互补的事实视角（可分别 NOT_MEASURABLE）：

### 3.1 \(L_{time}\)：时间寿命（时间尺度）
候选事实字段（示例）：
- `ticks_observed`
- `wall_clock_duration_ms`（若可得）

风险提示（写实）：
- tick 与墙钟受系统负载/网络环境影响，跨 run 比较需谨慎。

### 3.2 \(L_{exec}\)：执行寿命（闭环能力尺度）
语义：个体完成了多少“可审计的执行闭环事件集合”（P2/P3/P4 可得性视项目阶段而定）。

候选事实字段（示例）：
- `p2_terminal_orders_count`（若可得）
- `fills_count`（若可得）

规则：
- 若执行闭环不可测：该视角 `NOT_MEASURABLE`，不得用 0 代替。

### 3.3 \(L_{budget}\)：资源寿命（预算尺度）
语义：在有限“时间资源/外部通道资源”预算下的持续性表型。

最小集合（来自 Step72.1）：
- per-agent 决策耗时（CPU-time proxy）
- per-agent API 占用（calls/pages，按 endpoint_family）

规则：
- 若 API 归因不可得：agent-level 的 API 占用视角 `NOT_MEASURABLE`，可降级输出 world-level。

---

## 4) “高 ROI 被高代谢吃掉”的事实表述（冻结）

允许写入 research-side 的事实观察动机如下（不得扩展为策略/判定规则）：

- 在资源约束生态中，高 ROI 可能伴随高代谢（更高交易成本、更高 API/CPU 占用）。
- 高代谢可能通过两条路径降低可持续性：
  - **经济成本路径**：fee/slippage 等直接降低净收益（体现在 equity/PnL 真值）。
  - **可执行性路径**：限频/拥塞导致 truth 退化、闭环不可测、系统冻结（表现为 NOT_MEASURABLE 增多或 fail-closed 触发）。

注意：
- 该表述仅用于研究解释与分组，不反向影响死亡/繁殖判定，也不进入决策输入。

---

## 5) 后续推进建议（非冻结）

实现优先级：
- 先实现 summary（低扰动）；
- 再视需要增加 ticks（高信息量但可能更扰动）。


