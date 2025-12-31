# V11 Step 47 — Gene/Feature/Ledger SSOT Audit & Refactor (I/C + Ledger Truth) — 2025-12-30

目的：对 V11 execution_world 的 **基因表（Gene）/特征维度（E/I/M/C）/账簿真值字段（Ledger truth）** 做一次“一次性总审计 + SSOT 冻结”，把旧术语/旧字段（尤其 `has_position`）从执行世界语义里彻底移除，避免语义漂移与“旧代码复活”风险。

范围：
- execution_world（truth-driven）为唯一主线
- V10 锁版不做语义改动；V11 允许语义升级，但必须明确 breaking-change 的边界与迁移方式

---

## 1) 核心改动：`has_position` → 三元真值表达（SSOT）

### 1.1 旧字段（禁止作为真值特征）

`has_position`（bool/0/1）在 execution_world 下存在致命歧义：
- 它容易把“未知/缺失”伪装成“0=空仓”
- 它无法表达方向与敞口强度

因此：V11 execution_world **不得再把 `has_position` 作为 I 维度输入或 Ledger truth 的主字段**。

### 1.2 新 SSOT（必须替代）

用三元组表达持仓真值：

- `position_exposure_ratio`：float|null  
  - 语义：仓位敞口比例（dimensionless），\(0.0\) 表示空仓  
  - 取值范围：\[0, 1+\]（是否允许 >1 取决于 margin 口径；若允许必须写明口径）
  - 若 `positions_truth_quality != "ok"` → 必须为 `null`（禁止伪造 0）

- `pos_side_sign`：int|null  
  - 语义：方向符号，`-1`=short，`0`=flat，`+1`=long  
  - 若 `positions_truth_quality != "ok"` → 必须为 `null`

- `positions_truth_quality`：string（枚举）
  - 语义：持仓真值质量
  - 允许值：`ok` / `unreliable` / `unknown`

可选可读性派生字段（不进入核心决策向量，且不得掩盖 unknown）：
- `has_position_derived`: bool|null  
  - 规则：仅当 `positions_truth_quality=="ok"` 时可计算 `position_exposure_ratio > ε`，否则为 `null`

---

## 2) E/I/M/C 维度角色（冻结口径）

- **E (Environment)**：交易所市场环境事实（OKX 原始/映射后的 market data），对所有 Agent 一致；必须有 provenance/evidence。
- **I (Identity)**：个体“自我真值”输入（execution_world 下必须来自 Ledger truth），不得来自 agent-local 状态模拟。
- **M (Market Interaction / Friction)**：与执行相关的摩擦/统计事实（例如 MFStats/comfort），来源是 BrokerTrader/订单生命周期的事实统计；不是策略解释器。
- **C (Collective)**：群体现象信号（social/internal），来自 `decision_trace.jsonl` 的 **上一 tick** 统计，避免顺序偏置；不是交易所真值。

---

## 3) C 维度最小化（避免维度爆炸）

V11 baseline 推荐最小 C 探针（单一连续值）：
- `C_prev_net_intent = open_ratio(t-1) - close_ratio(t-1)`，范围 \([-1, +1]\)
- tick=1：无上一 tick → **必须为 null/unknown + reason_code="no_prev_tick"**（禁止伪造 0）

注意：
- C 是“演化规则/实验变量”，必须通过消融测试验证：`C_off` vs `C_on`
- C 不是不可观测基因；它是可观测 probe

### 3.1 观测纪律补充：避免“主观引导从众”（additive-only，冻结建议）

我们在讨论中达成的更新观点：
- “从众/同步”更像自然涌现结果，不应被我们通过显式输入特征强行诱导。
- 因此在稳定窗口（Step93）内，建议默认 **不把 C_prev_net_intent 作为核心决策向量输入**（可保持 C_off / mask=0），只保留为观测/分析用途。

这不是删除 C（避免 breaking），而是冻结一个更保守的默认使用口径：
- C 仍可用于消融实验与分析（C_on vs C_off）
- 但若进入核心决策向量，必须有明确实验目的与对照组记录（见 Step50/53）

### 3.2 群体执行反馈（fill_ratio）应归入 M（friction），而非 C（collective intent）（冻结建议）

我们新增的“执行反馈”候选信号本质是执行质量/生态围栏强弱的 proxy，应归入 M（friction）家族，并区分个体层与群体层两条通道：
- signal（可观测，非基因）：
  - `self_fill_ratio_prev_tick`：上一 tick 内该 Agent 自身的成交成功率（0..1；来自交易真值推导：filled_sz/requested_sz）
  - `group_fill_ratio_prev_tick`：上一 tick 内群体成交成功率的聚合（0..1；来自全体 self_fill_ratio 的聚合）
- gene（个体偏好，终身不变）：
  - `self_fill_feedback_weight ∈ [0,1]`：个体对 `self_fill_ratio_prev_tick` 的使用强度
  - `group_fill_feedback_weight ∈ [0,1]`：个体对 `group_fill_ratio_prev_tick` 的使用强度

聚合口径（v0，冻结）：
- `group_fill_ratio_prev_tick = mean(self_fill_ratio_prev_tick over population)`（均值）
- 说明：我们不为其预设“抗黑天鹅”等功能目标；群体分布形态应由演化自然形成，而不是由聚合器人为塑形。

口径纪律：
- v0 窗口硬编码为 t-1（上一 tick）；无事件/不可测 → mask=0（不得伪造 0）
- 不要求交易员理解原因；原因仍进入 Step96（bucket_key/reason_code）供审计

消融建议（单项可解释）：
- A: 仅启用 self（group off）
- B: 仅启用 group（self off）
- C: self+group 都启用
- D: self+group 都关闭（基线）
并保持 seed/初始化分布/mutation_rate/truth_profile/市场输入一致（按 Step50/53 纪律记录）。

与 Step52（维度冻结）的兼容性建议（稳定窗口优先）：
- **v0（推荐）**：先作为“非核心 side-channel 输入”落盘（例如在 decision trace 的 input_context 引用），避免立即 bump feature_dim/genome_schema
- **v1（后续）**：若证明有价值，再把 `group_fill_ratio_prev_tick` 变成正式 probe（feature_dim +1），并按 Step52 纪律同步 bump：
  - `feature_contract_version`
  - `genome_schema_version`
  - `decision_input_dim`

---

## 4) Ledger truth 字段（SSOT 冻结建议）

每 tick 的 Ledger snapshot（append-only）至少应能提供：
- `equity`（float|null）
- `capital_health_ratio`（float|null，derived；truth 缺失时为 null）
- `position_exposure_ratio`（float|null，derived；见 1.2）
- `pos_side_sign`（int|null，derived；见 1.2）
- `positions_truth_quality`（string：ok/unreliable/unknown）
- `reason_code`（string|null；只要出现 null truth 或 quality!=ok 必填）

禁止规则：
- 任何 truth 缺失不得写 0 伪装成有效值
- 任何 derived 值在输入 truth 缺失时必须为 null

---

## 5) 迁移与验收（Quant 落地要求）

Quant 侧落地必须满足：
- execution_world 的 I 输入只来自 Ledger truth（或 gated/masked），不读 agent-local `has_position/position_direction`
- 所有内部引用从 `has_position` 迁移到 `position_exposure_ratio + pos_side_sign + positions_truth_quality`
- 若保留 `has_position`，只能作为派生可读字段，且 unknown 时必须为 null（不得进入核心向量）

交付物纪律（Quant）：
- 1 个 commit（含 SHA），包含：
  - 替换/迁移点清单（文件路径）
  - feature/probe contract 更新（若存在）
  - 最小 fixture/证据包验证（不允许口头说明代替）


