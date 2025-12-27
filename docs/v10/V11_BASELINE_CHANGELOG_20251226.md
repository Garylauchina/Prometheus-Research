# V11 Baseline (Execution-world refactor) — Changelog / SSOT — 2025-12-26

目的：完整记录本次“大版本重构”的 **核心语义变化** 与 **冻结契约集合**，避免后续实现与验收口径混用。

本文件是 V11 的 SSOT（single source of truth）：后续只允许追加补充（additive），不允许悄悄改旧语义。

---

## 0) V11 定义（一句话）

V11 将 execution_world 统一为：**意图产生（core）与真实执行/入册（BrokerTrader）严格分离，所有交易真值以交易所可回查 JSON 为准，并通过订单确认协议与入册审计实现可复核闭环。**

---

## 1) 关键新增/冻结的模块（V11 baseline）

- **BrokerTrader（代理交易员：执行 + 入册唯一写入口）**
  - 合同：`docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`
  - 核心：所有下单/撤单/回查必须通过 BrokerTrader，runner 禁止绕过（避免审计黑洞）。

- **Order Confirmation Protocol（P0–P5 订单确认协议）**
  - 合同：`docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`
  - 核心：ack≠成交；必须 P2 终态可回查；P3/P4 才能做成交/账务结论；分页不完整→NOT_MEASURABLE。

- **ExchangeAuditor（只读交叉核验：落盘为主）**
  - 合同：`docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`
  - 本版本：evidence-only（不干预、不修复、不参与编排控制逻辑）。
  - 补充冻结（Step 19.1）：审计报告必须自包含 `exit_code` 与拆分后的 `contract_versions`；并冻结 verdict→exit_code 映射（`PASS→0 / NOT_MEASURABLE→0+WARNING / FAIL→2`）。
  - 当前状态（baseline honest reporting）：当必做检查项未实现（例如 orphan detection / 分页未闭合）时，总 verdict 必须为 `NOT_MEASURABLE`（不得误报 PASS）。

- **Registry Audit Checklist（入册漏洞 taxonomy，append-only）**
  - 合同：`docs/v10/V10_BROKERTRADER_REGISTRY_AUDIT_CHECKLIST_20251226.md`
  - 核心：用 discrepancy_type 逐步覆盖未知入册漏洞（新增条目即可扩展覆盖面）。

- **LifecycleJudge（死亡/繁殖审判）**
  - 合同：`docs/v10/V10_LIFECYCLE_JUDGE_MODULE_CONTRACT_20251226.md`
  - 核心：审判与执行解耦；不交易；只产出 append-only 生命周期裁决事件。

---

## 2) 核心语义（breaking-level）

### 2.1 Execution-world intent-only（禁止内部模拟）

- Agent/Decision 只产出 **intent**（不“自认为成交”、不内部改仓位/资金为真值）。
- 资金/仓位/成交/费用真值必须来自交易所可回查 JSON（或 `null + reason_code`）。
- 相关设计落地已写入：`docs/v10/V10_DESIGN.md`（execution_world hard semantics + 编排）。

### 2.5 基因维度 / 特征合同的关键变更（Gene/Feature contract）

这次重构不仅是“执行链路模块化”，也同步推进了 **基因表达所消费的特征口径**（尤其是 I 维度真值化与 truth gating），属于 breaking-level 变化：

- **I 维度从内部状态 → 真值驱动（execution_world）**
  - `has_position`（0/1）与 `position_direction`（-1/0/+1）被明确标注为 **offline_sim legacy / DEPRECATED**
  - execution_world 的 I 维度改为（Ledger-backed）：
    - `position_exposure_ratio`（连续值，0.0=flat，但仅在 truth ok 时成立）
    - `pos_side_sign`（-1/0/+1）
    - `positions_truth_quality`（ok/unreliable/unknown）
  - **hard rule**：`positions_truth_quality != ok` 时，`position_exposure_ratio` 必须为 `null/unknown`（不得伪造为 0）
  - 参考：`docs/v10/V10_DESIGN.md`

- **truth_profile + ProbeGating：固定维度、真值可用性由 gating 决定**
  - Core 不再“根据 demo/live 丢维度”，而是消费固定 probe 向量；缺失用 `unknown/mask + reason_code` 表达
  - **Unknown must not be fabricated as 0**：只有同时给出 mask/quality/reason 才允许数值占位
  - 参考：`docs/v10/V10_TRUTH_PROFILE_AND_PROBE_GATING_CONTRACT_20251226.md`

- **最小“历史投影”特征（避免维度爆炸）**
  - 允许 derived-only 的最小投影指标：
    - `capital_health_ratio = equity / bootstrap_equity`
    - `position_exposure_ratio = abs(pos_size * mark_price) / equity_or_bootstrap`
  - 规则：必须由 raw truth 字段推导；缺输入→unknown（不得补 0）
  - 参考：`docs/v10/V10_TRUTH_PROFILE_AND_PROBE_GATING_CONTRACT_20251226.md`

- **C 维度（群体现象 / social signal）：上一 tick 的 intent 统计（t-1），用于“演化规则”消融**
  - 定位：C 在 V11 baseline 中被定义为 **social/internal signal**（来自 core 的 intent 现象），不是交易所真值；不得用成交/收益/ROI 作为 C 输入（避免隐性策略与 truth_profile 混用）。
  - 证据来源（可复核）：`decision_trace.jsonl` 的 `record_type="agent_detail"`（字段 `intent_action ∈ {open, close, hold}`）
  - 推荐最小 probe（单探针，连续）：
    - `C_prev_net_intent = open_ratio(t-1) - close_ratio(t-1)`，范围 \([-1, +1]\)
    - 解释：>0 表示群体偏 open，<0 表示群体偏 close，≈0 表示群体偏 hold/分裂
  - 可选扩展（信息更全，但维度更大）：
    - `C_prev_open_ratio`、`C_prev_close_ratio`（`hold_ratio = 1 - open - close` 可隐含）
    - `C_prev_intent_entropy`（衡量一致性/分裂度；用于观察“同步性”收敛）
  - tick=1 规则（hard）：无 \(t-1\) 记录时，C 必须为 `unknown/null + reason_code="no_prev_tick"`（不得伪造为 0）；当且仅当上一 tick 的统计真实为 0 时，才允许写入数值 0。
  - 实验协议（验证“规则是否成立”，而非引入隐性基因）：做 `C_off vs C_on` 消融，保持 seed/初始化分布/mutation_rate/truth_profile/市场输入一致，对比可复现的可观测差异（生存率、intent_entropy 曲线、群体耦合度等）。

### 2.6 E 维度（市场输入）口径变化：CCXT-OHLC → OKX native probes + provenance

E 维度在 execution_world 里不仅“数据源”变化，也牵涉到 **哪些 E probes 可用/不可用** 的 breaking change 风险：

- **从“CCXT 对齐的 OHLCV + 盘口”转向“OKX 原生 ticker/books 映射”**
  - execution_world 的 E probes 必须绑定到 **一个 canonical OKX endpoint + field path**，并落盘 provenance：
    - `inst_id_used`
    - `source_endpoint_used`
    - `source_ts_used` / `source_ts_ms_used`
    - `input_quality_flags` + `reason_code`
  - 参考：`docs/v10/V10_OKX_NATIVE_E_PROBES_MAPPING_CONTRACT_20251226.md`

- **关键 breaking：Candles（OHLCV）目前未接入**
  - 合同明确：candles “not yet wired in current connector”
  - 因此 legacy 向量里若仍期待 `open/high/low/close/volume`（OHLCV per bar），在 execution_world 下必须：
    - 标记为 `unavailable`（`input_quality_flags="unavailable"` + `reason_code`）
    - **禁止**用 ticker 字段“伪造 OHLC”
  - 参考：同上（§1, §3.2）

- **价格基准必须冻结（mark vs last）**
  - `E_price_ref` 允许选择 `last` 或 `markPx`，但一旦选择必须冻结；切换视为口径变更（需要版本提升）。
  - 参考：同上（§3.1）

结论：V11 baseline 下，E 维度必须以“映射契约 + provenance”作为可测前提；否则存在“静默市场/默认值”导致决策链失真风险。

### 2.2 订单主键与归因锚点（防孤儿）

- 订单主键：`ordId`（交易所）
- 本地绑定键：`clOrdId`（绑定 agent）
- **孤儿订单 hard 定义**：交易所可回查订单/成交事实，但本地入册无法找到归因锚点（`agent_id_hash` 或 `lifecycle_scope`）→ orphan。
- 结论：即使不能逐 agent 强平，只要 `system_flatten` 订单也带 `lifecycle_scope`，就不会产生“不可归因孤儿”。

### 2.3 生命周期强平（system_flatten）纳入统一入册

- LifecycleJudge 需要强平时，不直接交易；runner 只能调用 BrokerTrader 的生命周期强平入口：
  - `lifecycle_scope=system_flatten`
  - `lifecycle_reason=death_or_reproduce_settlement`
- 强平动作必须像普通订单一样走 P0–P5，并写入入册证据。

### 2.4 执行时 L1 一级分类（taxonomy）+ 推荐动作

- BrokerTrader 必须对执行过程中异常做 **L1 一级分类**（冻结词表）并入册：
  - `L1_OK / L1_RETRYABLE_TRANSPORT / L1_ACCOUNT_RESTRICTED / L1_EXCHANGE_REJECTED / L1_TRUTH_INCOMPLETE / L1_LIQUIDITY_UNAVAILABLE`
- 本版本策略：**交易员不直接 STOP**，而是落盘 `recommended_action`（runner 决定 stop/freeze）。
- 同步冻结了最小 `reason_code → L1` 映射表（additive-only）。

---

## 3) V11 推荐编排顺序（生命周期周期）

本版本默认（先不把审计模块加入主编排控制）：

1) 周期内：BrokerTrader 获取交易所实时信息并落盘（至少价格；其他可选）
2) 计算阶段：基于交易员账簿/ledger 生成 `metrics_snapshot`（带 truth_quality）
3) 结算阶段：强平（system_flatten）+ 系统钱包吸收/调整（system_reserve absorb），并落盘证据
4) 审判阶段：LifecycleJudge 输出死亡/繁殖裁决清单（append-only）
5) 执行阶段：runner/SystemManager 执行裁决（死亡 agent 不再接受委托；繁殖 agent 初始化资金=分裂后资金）

可选（未来扩展）：周期末运行 ExchangeAuditor 做交叉核验并落盘，但不改变模块功能。

---

## 4) Gate/验收口径变更（对外裁判尺度）

- Gate4 增补：
  - 订单确认协议（G4.3e）
  - run-end 只读审计条款（G4.3f，作为锁版前审查工具；本版本可不纳入主编排控制）
  - 唯一交易入口（禁止绕过 BrokerTrader）已作为 hard rule 写入。

参考：`docs/v10/V10_ACCEPTANCE_CRITERIA.md`

---

## 5) 对实现仓库（Prometheus-Quant）的迁移检查表（最小）

- **接口层**
  - [ ] runner 不得直接调用 connector 下单/撤单/回查
  - [ ] 所有写操作走 BrokerTrader，并写入 `intent_source` 与归因锚点

- **证据层**
  - [ ] `order_attempts.jsonl` 每条包含：`l1_classification`、`reason_code`、`recommended_action`、归因锚点（二选一：`agent_id_hash` 或 `lifecycle_scope`）
  - [ ] `order_status_samples.jsonl` append-only（不得只写最终态）

- **生命周期层**
  - [ ] 周期末强平走 `system_flatten`，并能回指入册证据（refs）
  - [ ] `lifecycle_events.jsonl`（死亡/繁殖清单）append-only 落盘

- **审计层（工具化）**
 - **特征/版本标识（避免口径混用）**
  - [ ] `run_manifest`/summary 必须记录：`truth_profile`、`impedance_fidelity`
  - [ ] 预留并逐步落地：`feature_contract_version`、`genome_schema_version`、`pool_namespace`（v2/v11 基线口径）
  - [ ] E probes 的 provenance 字段必须落盘（`inst_id_used/source_endpoint_used/source_ts_used/input_quality_flags/reason_code`），且缺失不得伪造为 0（需 unknown/mask）

  - [ ] ExchangeAuditor 可离线运行并落盘 `auditor_report.json` + `auditor_discrepancies.jsonl`

---

## 6) 版本纪律（V11 基线）

- 本文件与相关契约：**只允许新增条目/字段（additive-only）**。
- 任何破坏性变更必须：
  - 提升 major（V12…）
  - 重跑最小 PROBE 证据包


