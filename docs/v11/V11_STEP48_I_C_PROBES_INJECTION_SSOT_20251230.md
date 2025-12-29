# V11 Step 48 — I/C Probes Injection SSOT (Ledger Triad + C_prev_net_intent) — 2025-12-30

目的：把 Step 47（Ledger triad 已落地）的剩余部分收口为可验收落地规则：
- **I 维度**：execution_world 下必须由 Ledger truth triad 注入，禁止读取 agent-local `has_position`/`position_direction`
- **C 维度**：最小探针 `C_prev_net_intent` 来自 `decision_trace.jsonl` 的 **上一 tick** 意图统计，避免同 tick 顺序偏置

前置：
- Step 47 Spec：`docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`
- Step 47 Quant 落地（Ledger triad）：`docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`

---

## 1) I 维度注入（execution_world，冻结）

### 1.1 I 三元组（SSOT）

I 维度必须使用 Ledger triad（或 gated mask）：
- `position_exposure_ratio`（float|null）
- `pos_side_sign`（int|null，-1/0/+1）
- `positions_truth_quality`（ok/unreliable/unknown）

规则（硬）：
- 若 `positions_truth_quality != "ok"`：
  - `position_exposure_ratio` 与 `pos_side_sign` 必须为 `null`
  - 不得用 `0.0/0` 伪装成 flat
- 若 `positions_truth_quality == "ok"`：
  - triad 必须完整、合法

### 1.2 注入路径（硬边界）

在 Quant 里，任何构造 DecisionEngine 输入向量的代码路径必须满足：
- I 维度来源 = Ledger snapshot / ProbeGating 输出（而非 Agent 内部状态）
- 若某 I probe 为 null/unknown：必须通过 mask/quality 表达不可用，不得“填 0 当真值”

---

## 2) C 维度最小探针（execution_world baseline，冻结）

### 2.1 定义

最小 C 探针：
- `C_prev_net_intent = open_ratio(t-1) - close_ratio(t-1)`，范围 \([-1, +1]\)

其中：
- `open_ratio(t-1) = open_count(t-1) / total_count(t-1)`
- `close_ratio(t-1) = close_count(t-1) / total_count(t-1)`
- total_count = open+close+hold（只统计“有决策记录的 agent”）

### 2.2 数据源与证据

来源必须是：
- `decision_trace.jsonl`（append-only）
- 使用 tick=t-1 的记录聚合，生成 tick=t 的 probe

禁止：
- 同 tick 内串行/随机顺序的“看别人已决策”方式（会引入顺序偏置，不可复核）

### 2.3 tick=1 的缺省（硬）

tick=1 没有上一 tick：
- `C_prev_net_intent` 必须为 `null`（或 mask=0）
- 必须写 `reason_code="no_prev_tick"`（或等价可审计字段）
- 禁止伪造 0

---

## 3) 合约与验收（Quant 落地必须达成）

必须提供：
- feature/probe contract 的明确字段与顺序（若已存在固定向量：必须注明 I/C 的 index 与缺失策略）
- 证据：至少一个 PASS fixture 或最小 run 证明
  - tick=1：C 为 null/unknown
  - tick=2：C 来自 tick=1 的统计
  - I triad：quality!=ok 时 I 值为 null（mask=0 或 quality 标记）

交付物纪律：
- 1 个 commit（含短/长 SHA）
- 变更文件列表 + 最小验收输出（CI 或脚本）


