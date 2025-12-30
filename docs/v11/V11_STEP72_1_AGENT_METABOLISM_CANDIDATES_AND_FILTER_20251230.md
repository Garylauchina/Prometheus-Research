# V11 Step 72.1 — Agent Metabolism Candidates & Filter (Fact-Only, Non-Invasive) — SSOT — 2025-12-30

目的：把“时间是最大资源”的哲学命题，收敛为 **必要且可行** 的工程化观测方案：给出代谢指标候选清单、筛选门槛与最终的最小集合（只观测，不入基因、不入 probe、不改 DecisionEngine）。

本文件只允许追加（additive-only）。

关联：
- Step72（代谢观测契约）：`docs/v11/V11_STEP72_AGENT_METABOLISM_OBSERVABILITY_CONTRACT_20251230.md`

---

## 1) 筛选门槛（冻结）

任何候选指标必须逐条通过以下门槛（Fail 任一条 → 暂缓）：

- **必要性（Necessity）**：没有它会导致演化观察出现系统性盲区（例如无法区分策略差异 vs 系统拥塞/限频造成的 truth 退化）。
- **可测性（Measurable）**：在现有证据链下能稳定测得；测不到必须能明确标注 `NOT_MEASURABLE`，且不会被误读为 0。
- **可归因（Attributable）**：能归因到 `agent_id_hash`（优先）或至少 world-level；若只能近似必须写明“近似等级”和不可比边界。
- **可审计（Auditable）**：指标必须能从落盘证据复算/交叉验证（至少 hash/refs 可对齐）。
- **边际成本（Cost）**：采集与写盘成本不能显著扰动 tick 时间预算（避免观察污染）。
- **不改变基线（Non-invasive）**：只做 research-side 输出，不进入 probe/决策、不改变基线语义。

---

## 2) 候选清单（不冻结，仅供筛选）

### 2.1 M_intent（意图代谢，always measurable）
- open/close/hold count
- action_rate = (open+close)/ticks_observed
- 连续 HOLD 段长度分布

### 2.2 M_exec（执行代谢，truth-dependent）
- orders submitted/rejected
- fills_count
- fee_total（按币种写实）
- P2 latency 分位数（若有 monotonic latency evidence）

### 2.3 M_resource（系统资源代谢）
- agent 决策耗时（CPU-time proxy，ns/ms）
- agent API call count（按 endpoint_family 分桶）
- paging 页数、重试次数、transport error 计数（若证据存在）
- IO/磁盘写入字节数（倾向 world-level）
- 进程内存（RSS）变化（倾向 world-level）

---

## 3) 通过门槛的“最小集合”（冻结）

本版本（V11）只建议纳入两个指标族，先观测、低扰动、强归因：

### 3.1 必选 A：每 agent 决策耗时（CPU-time proxy）
- **必要性**：解释规模扩大后“同策略但稳定性/吞吐退化”的现象；识别个体对 tick 时间预算的占用差异。
- **可测性**：强（`time.perf_counter_ns()` / monotonic）。
- **可归因**：强（包裹 agent 决策调用前后即可）。
- **成本**：低（两个时间戳 + 差值）。
- **审计**：中-强（append-only ticks 或 summary 可复核；如需可加 evidence_refs）。

输出建议（fact-only）：
- per-agent: `decision_cpu_time_ns_p50/p95`（或 ms）
- per-agent: `decision_cpu_time_ns_total`

### 3.2 必选 B：每 agent API 占用（calls/pages，按 endpoint_family）
- **必要性**：解释 truth_quality 退化、限频、拥塞导致的 NOT_MEASURABLE；评估个体对外部“时间通道”的占用。
- **可测性**：中-强（前提：请求/分页 traces 已落盘且带归因锚点）。
- **可归因**：中（需每次请求携带 `agent_id_hash` 或 system-level anchor；做不到则降级为 world-level）。
- **成本**：中（可复用 paging_traces 框架，增量可控）。
- **审计**：强（traces append-only，可复算）。

输出建议（fact-only）：
- per-agent: `api_calls_total`
- per-agent: `api_calls_by_endpoint_family{...}`
- per-agent: `paging_pages_total`
- 若不可归因：输出 world-level + `NOT_MEASURABLE`（agent-level）

---

## 4) 明确暂缓项（冻结）

以下项在 V11 baseline 暂缓（原因：归因弱、噪声大、成本高、或易污染观察）：
- agent 级别内存占用（难以归因）
- agent 级别 IO/磁盘字节（归因弱，易引入自扰）
- 任何需要 OS 级采样且无法落盘复核的指标

---

## 5) 观察污染控制（冻结）

硬规则：
- 默认只输出 `agent_metabolism_summary.json`（run 汇总）；ticks 级别输出为可选项。
- 采集开销必须被明确记录（如有），避免“为测量而测量”反向影响 tick 频率与 comfort。
- 对 truth-dependent 指标严格执行 `NOT_MEASURABLE + null`，不得当 0。


