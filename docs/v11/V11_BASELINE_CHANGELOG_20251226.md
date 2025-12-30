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

- **Step 26：DecisionEngine 输入接入 world-level 执行摩擦（MFStats / Comfort），仅作为观测特征（不执法）**
  - 背景：在 execution_world 中，“执行摩擦”是可观测的世界现象（事实统计/投影），应进入决策输入以支持演化与对照，而不是被写成阈值电闸（硬门仍由证据链失败与 ProbeGating 决定）。
  - feature contract 版本提升（示例实现仓库口径）：`V11_FEATURE_PROBE_CONTRACT_20251228.1`
  - 维度扩展：在既有市场 E probes 基础上 **additive-only** 新增：
    - `MF_stats`：3 维（事实统计，例如 P2 闭合率、L1 拒绝率、ack→P2 延迟 p95）
    - `comfort_value`：1 维（由 MF_stats 投影而来，范围 \([-1, +1]\)）
  - mask 纪律（hard）：当 `MF_stats/comfort` 不可测时必须 `mask=0 + reason_code`；DecisionEngine 必须尊重 mask（mask=0 维度不参与）。
  - hard boundary：**禁止**在 DecisionEngine 内引入 `comfort`/`MF_stats` 的阈值执法（不得替代 ProbeGating/证据链硬门）。

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
  - Step 28：run-end 证据包打包 + Gate（生成 `FILELIST/SHA256SUMS` 后运行最小复核 verifier；FAIL 必须以 exit 2 失败退出，避免“证据不可复核但误判正常结束”）。
  - Step 29：CI Evidence Gate（fixture-based + verifier + workflow，FAIL=阻断合并），防止未来改动破坏 Step 26 证据链闭合与 contract/mask 纪律。
  - Step 30：Quant runner 已强制接入 Step 28 gate（run-end 必跑 + fail-closed），并写实 `run_manifest.evidence_gate` 与 `errors.jsonl`（实现锚点见：`docs/v11/V11_STEP30_RUN_END_EVIDENCE_GATE_IMPLEMENTED_20251229.md`）。
  - Step 31：扩展 evidence verifier 覆盖 Tier-1（`ledger_ticks.jsonl` + `probe_gating_ticks.jsonl` + `errors.jsonl`）的最小一致性，形成“输入链 + 真值链 + 失败链”的可复核闭环（规格见：`docs/v11/V11_STEP31_EXTEND_EVIDENCE_VERIFIER_TIER1_20251229.md`）。
  - Step 31（落地）：Quant 已实现并推送 Tier-1 verifier 扩展，并同步升级 CI gate（Step 29）与 run-end gate（Step 30）的覆盖范围（实现锚点见：`docs/v11/V11_STEP31_TIER1_VERIFIER_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 32：Orphan Detection 最小可测（orders-level）——以 `clOrdId` 命名空间界定 in-scope，要求分页闭合；闭合后发现 orphan → FAIL；前提不满足 → NOT_MEASURABLE（规格见：`docs/v11/V11_STEP32_ORPHAN_DETECTION_MIN_MEASURABLE_20251229.md`）。
  - Step 32（落地）：Quant 已实现 orphan detection（orders-level，`clOrdId` 前缀 `v11_` + 分页闭合），并提升审计契约版本 `V11_EXCHANGE_AUDITOR_20251229`，推送至 `main`（实现锚点见：`docs/v11/V11_STEP32_ORPHAN_DETECTION_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 33：fills/bills（P3/P4）最小可测（分页闭合 + join + 幂等），把成交/费用相关断言从 NOT_MEASURABLE 推进为可机械复核（规格见：`docs/v11/V11_STEP33_FILLS_BILLS_JOIN_MIN_MEASURABLE_20251229.md`）。
  - Step 33（落地）：Quant 已实现 P3/P4 fills/bills join（分页闭合 + ordId join + tradeId/billId 幂等），并推送至 `main`（实现锚点见：`docs/v11/V11_STEP33_FILLS_BILLS_JOIN_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 34：分页闭合证据落盘（`paging_traces.jsonl`，append-only）——把“分页闭合”升级为可复核 proof；缺失或未闭合则相关结论必须 NOT_MEASURABLE（规格见：`docs/v11/V11_STEP34_PAGING_TRACES_APPEND_ONLY_20251229.md`）。
  - Step 34（落地）：Quant 已实现 `paging_traces.jsonl`（orders/fills/bills，append-only）作为分页闭合 proof，并推送至 `main`（实现锚点见：`docs/v11/V11_STEP34_PAGING_TRACES_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 35：gates 强制要求 `paging_traces.jsonl`（verifier/run-end/CI）——当 run 声称 P3/P4 可测（fills/bills）时，缺失 paging_traces 或无法证明闭合 → 相关结论必须 NOT_MEASURABLE（不得 PASS）（规格见：`docs/v11/V11_STEP35_REQUIRE_PAGING_TRACES_IN_GATES_20251229.md`）。
  - Step 35（落地）：Quant 已把 `paging_traces.jsonl` 纳入 evidence verifier 与 CI fixture 的硬要求（实现锚点见：`docs/v11/V11_STEP35_REQUIRE_PAGING_TRACES_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 36：冻结 auditor_report 的分页闭合覆盖率字段（page_count/closure_proved/trace_line_range 等），把“闭合证明”变成可审计的量化口径（规格见：`docs/v11/V11_STEP36_AUDITOR_PAGING_COVERAGE_FIELDS_20251229.md`）。
  - Step 36（落地）：Quant 已实现 `paging_coverage` 字段与 verifier 一致性校验，并完成审计契约/Schema 版本 bump（实现锚点见：`docs/v11/V11_STEP36_AUDITOR_PAGING_COVERAGE_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 37：paging_traces 增加 `scope_id/query_chain_id` 并与 paging_coverage 的 line_range 绑定，防止同一 run 内多次查询造成“混链歧义”；verifier 必须对混链 FAIL（规格见：`docs/v11/V11_STEP37_PAGING_QUERY_CHAIN_ID_20251229.md`）。
  - Step 37（落地）：Quant 已实现 scope_id/query_chain_id 并在 verifier 中对混链 fail-closed（实现锚点见：`docs/v11/V11_STEP37_PAGING_QUERY_CHAIN_ID_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 38：run_manifest 写入审计 scope anchors（audit_scope_id/inst_id/time_window_ms/prefix），并与 auditor_report/paging_traces 对齐，防止“同名审计但范围漂移”（规格见：`docs/v11/V11_STEP38_AUDIT_SCOPE_ANCHORS_IN_MANIFEST_20251229.md`）。
  - Step 38（落地）：Quant 已实现 run_manifest.audit_scope anchors + 一致性校验，并推送至 `main`（实现锚点见：`docs/v11/V11_STEP38_AUDIT_SCOPE_ANCHORS_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 39：把 `audit_scope_id` 作为全链路全局主锚点（auditor_report/discrepancies/paging_traces/errors/manifest），并由 verifier 对缺失/不一致 fail-closed（规格见：`docs/v11/V11_STEP39_AUDIT_SCOPE_ID_AS_GLOBAL_ANCHOR_20251229.md`）。
  - Step 39（落地）：Quant 已实现 `audit_scope_id` 全链路 join + verifier fail-closed，并推送至 `main`（实现锚点见：`docs/v11/V11_STEP39_AUDIT_SCOPE_ID_GLOBAL_ANCHOR_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 40：run_manifest 增加 `audit_scopes[]`（append-only）记录多次审计 scope，禁止覆盖，避免证据丢失与不可复核（规格见：`docs/v11/V11_STEP40_MANIFEST_AUDIT_SCOPES_APPEND_ONLY_20251229.md`）。
  - Step 40（落地）：Quant 已实现 `audit_scopes[]`（append-only）+ 一致性校验，并推送至 `main`（实现锚点见：`docs/v11/V11_STEP40_MANIFEST_AUDIT_SCOPES_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 41：审计链 evidence_refs 统一协议（file+line_range+sha256_16+audit_scope_id），并由 verifier/gates fail-closed 校验引用可回查且被 SHA256 覆盖（规格见：`docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`）。
  - Step 41（落地）：Quant 已实现 evidence_refs 协议并在 verifier 中强制校验 hash/行号/FILELIST 覆盖（实现锚点见：`docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 42：审计链 evidence_refs 强约束升级：gate-on 时 `sha256_16` 强制非空且可复算匹配；对 `.jsonl` 引用强制 `line_start/line_end` 非空并校验范围合法；并强制 FILELIST 覆盖与 audit_scope_id join（规格见：`docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`）。
  - Step 42（落地）：Quant 已实现 gate-on 下 evidence_refs 的 hash/行号/FILELIST/audit_scope_id 强约束，并由 verifier fail-closed 执行（实现锚点见：`docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 43：新增 `evidence_ref_index.json`（hash+line_count 索引）由 run-end gate 生成，verifier gate-on 时优先用 index 校验 `sha256_16` 与 `.jsonl` 的行号上界，避免重复复算导致慢/漂移（规格见：`docs/v11/V11_STEP43_EVIDENCE_REF_INDEX_20251229.md`）。
  - Step 43（落地）：Quant 已实现生成 `evidence_ref_index.json` 并在 verifier gate-on 校验中优先使用（实现锚点见：`docs/v11/V11_STEP43_EVIDENCE_REF_INDEX_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 44：evidence_refs 可解引用校验（dereference validation）：verifier gate-on 时按 `file+line_range` 读取 `.jsonl` 行并 parse JSON，强制校验 `run_id` 与 `audit_scope_id` 语义自洽，防止“形式正确但指向无关行”的投机（规格见：`docs/v11/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_20251229.md`）。
  - Step 44（落地）：Quant 已在 verifier 中实现 dereference 校验，并增加 run_id 不匹配的投机负例 fixture（实现锚点见：`docs/v11/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 45：evidence_refs 语义 join 校验：在 Step 44 的基础上，要求引用到 `paging_traces.jsonl` 的行范围内 `scope_id/query_chain_id/endpoint_family` 不混且与 audit_scope 锚点一致，防止同 run 内“指向无关行”（规格见：`docs/v11/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_20251229.md`）。
  - Step 45（落地）：Quant 已实现语义 join 校验与两类投机负例 fixtures（mixed query_chain / mixed endpoint），并在 CI 中验证 fail-closed（实现锚点见：`docs/v11/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 46：Evidence Gate Bundle 冻结：把 Step41–45 收口为可版本化 bundle（bundle_version 写入产物与 manifest），并冻结必需 fixtures 套件与 exit code 语义（规格见：`docs/v11/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_20251229.md`）。
  - Step 46（落地）：Quant 已实现 bundle 常量/输出、manifest.evidence_gate 写入 bundle 信息、以及冻结 fixtures 的 CI 套件（实现锚点见：`docs/v11/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_IMPLEMENTED_IN_QUANT_20251229.md`）。
  - Step 47：基因/特征/账簿 SSOT 总审计：execution_world 下退役 `has_position`，以 `position_exposure_ratio + pos_side_sign + positions_truth_quality` 作为持仓真值三元组；冻结 E/I/M/C 口径与 C 最小探针（规格见：`docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`）。
  - Step 47（落地）：Quant 已在 LedgerModuleV11 中引入持仓真值三元组与强制规则，并升级 ledger contract/schema 版本（实现锚点见：`docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 48：I/C 注入 SSOT：execution_world 下 I 维度必须由 Ledger triad 注入（mask/unknown 纪律），C 维度基线采用 `C_prev_net_intent(t-1)`，tick=1 必须 null/unknown（规格见：`docs/v11/V11_STEP48_I_C_PROBES_INJECTION_SSOT_20251230.md`）。
  - Step 48（落地）：Quant 已扩展 feature/probe contract，引入 I triad probes + `C_prev_net_intent`，并提供 Step48 验收脚本验证 null/mask 纪律（实现锚点见：`docs/v11/V11_STEP48_I_C_PROBES_INJECTION_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 49：C 消融开关（`C_off` vs `C_on`）：固定维度不变，通过 mask 控制 C 探针是否生效，并强制把开关状态写入 run_manifest + contract info（规格见：`docs/v11/V11_STEP49_C_ABLATION_SWITCH_20251230.md`）。
  - Step 49（落地）：Quant 已实现 `c_feature_mode`（C_off/C_on）与 contract 证据化输出，并提供 Step49 验收脚本验证维度保持与 mask 策略（实现锚点见：`docs/v11/V11_STEP49_C_ABLATION_SWITCH_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 50：C_off vs C_on 最小对照实验模板：要求 `run_manifest.ablation_experiment` 记录对照实验必含字段（seed/ticks/agents/truth_profile/mode/feature_contract/bundle_*），且对照实验除 variant 外必须一致（规格见：`docs/v11/V11_STEP50_MIN_ABLATION_EXPERIMENT_TEMPLATE_20251230.md`）。
  - Step 50（落地）：Quant 已在 runner 写入 `run_manifest.ablation_experiment`（含 C_off/C_on variant 与控制变量字段），并提供 Step50 验收脚本验证一致性（实现锚点见：`docs/v11/V11_STEP50_MIN_ABLATION_EXPERIMENT_TEMPLATE_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 51：最小对照实验跑通：要求在 C_off/C_on 两次 run 中生成 `ablation_summary.json`（事实统计、无解释）并通过 evidence_refs 可复核（规格见：`docs/v11/V11_STEP51_MIN_ABLATION_RUN_AND_SUMMARY_20251230.md`）。
  - Step 51（落地）：Quant 已实现 `ablation_summary.json` 生成、对照 run 脚本与验收脚本，并提供 C_off/C_on 两次 run 的完整输出（实现锚点见：`docs/v11/V11_STEP51_MIN_ABLATION_RUN_AND_SUMMARY_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 52：冻结 feature contract 维度 ↔ DecisionEngine 输入维度 ↔ Genome schema 权重布局一致性，并在 runner preflight fail-closed 校验与 manifest 证据化记录（规格见：`docs/v11/V11_STEP52_FEATURE_DIM_DECISION_ENGINE_GENOME_ALIGNMENT_20251230.md`）。
  - Step 52（落地）：Quant 已新增 alignment_check 模块并在 runner preflight 执行 fail-closed 校验，manifest 记录对齐结果（实现锚点见：`docs/v11/V11_STEP52_FEATURE_DIM_DECISION_ENGINE_GENOME_ALIGNMENT_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 53：跨 run 对照聚合报告：生成 `ablation_compare.json`（读取两份 `ablation_summary.json`，做可比性检查 + 事实差异统计 + evidence_refs 可复核）（规格见：`docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 54：把 Step 53 的 `ablation_compare.json` 纳入 run-end evidence gate/CI gate（可选开关，但必须 manifest 写实；不可比=WARNING 不阻塞；工具失败=exit 2），让“跨 run 对照报告”也进入可复核闭环（规格见：`docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 55：冻结 Step54 的验收协议（命令/产物/manifest/exit code/CI 必跑项），把 Step54 的“可复核状态”从口头复述升级为机械可执行清单（规格见：`docs/v11/V11_STEP55_STEP54_ACCEPTANCE_PROTOCOL_20251230.md`）。
  - Step 56：把 Step55 验收升级为 CI 必跑 gate（Quant CI 必须运行 `tools/test_step54_integration.py` 并 PASS），防止后续回归破坏 Step53/54 的证据闭环（规格见：`docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 57：冻结 Step56 CI gate 所依赖的 Step51 最小 fixtures 口径（目录结构 + 最小字段集合 + 可比性硬规则 + 变更纪律），避免 fixture 漂移导致 gate 失真（规格见：`docs/v11/V11_STEP57_STEP51_MIN_FIXTURES_CONTRACT_20251230.md`）。
  - Step 58：为 Step57 fixtures contract 提供机器可执行 verifier，并纳入 Quant CI gate（Step56 链路）作为必跑断言，防止 fixtures 漂移（规格见：`docs/v11/V11_STEP58_FIXTURES_CONTRACT_VERIFIER_20251230.md`）。
  - Step 58（落地）：Quant 已新增 fixtures contract verifier 并接入 CI gate（实现锚点见：`docs/v11/V11_STEP58_FIXTURES_CONTRACT_VERIFIER_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 59：定义 compare_bundle.json（fact-only）作为跨 run 对照的“研究侧消费入口”，从 Step53 的 ablation_compare.json 中摘录/汇总事实字段并写入 evidence_refs（规格见：`docs/v11/V11_STEP59_COMPARE_BUNDLE_CONTRACT_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP59_COMPARE_BUNDLE_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 60：把 Step59 compare_bundle.json 纳入 run-end evidence gate / CI gate（与 Step54 compare 同目录，生成后必须 verify，并纳入 FILELIST/SHA256SUMS/evidence_ref_index；工具/证据失败=exit 2），让研究消费入口也进入可复核闭环（规格见：`docs/v11/V11_STEP60_GATE_COMPARE_BUNDLE_INTEGRATION_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP60_GATE_COMPARE_BUNDLE_INTEGRATION_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 61：生成 compare_bundle_index.json（fact-only 聚合索引），批量聚合 compare_bundle.json 以支持检索/归档（不解释、不新增指标），并保持 evidence_refs 可复核（规格见：`docs/v11/V11_STEP61_COMPARE_BUNDLE_INDEX_CONTRACT_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP61_COMPARE_BUNDLE_INDEX_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 62：CI 必跑生成并验证 compare_bundle_index.json（scan_root 固定为 fixtures-root 或 Step54 测试产物 runs_root），防止索引入口长期不跑而漂移/腐化（规格见：`docs/v11/V11_STEP62_CI_GATE_STEP61_INDEX_20251230.md`；Quant 落地记录：`docs/v11/V11_STEP62_CI_GATE_STEP61_INDEX_IMPLEMENTED_IN_QUANT_20251230.md`）。
  - Step 63：run-end evidence gate 可选生成并验证 compare_bundle_index.json，并纳入 evidence package + manifest 记录（启用时 fail-closed，防空跑 bundle_count>=1）（规格见：`docs/v11/V11_STEP63_RUN_END_GATE_COMPARE_BUNDLE_INDEX_OPTIONAL_20251230.md`）。
  - Step 63（Quant 落地记录）：`docs/v11/V11_STEP63_RUN_END_GATE_COMPARE_BUNDLE_INDEX_OPTIONAL_IMPLEMENTED_IN_QUANT_20251230.md`（commit：07c620c）。
  - Step 64：CI 必跑 Step63 集成测试（`tools/test_step63_integration.py`），任何偏离契约即阻断合并（规格见：`docs/v11/V11_STEP64_CI_GATE_STEP63_ACCEPTANCE_20251230.md`）。
  - Step 64（Quant 落地记录）：`docs/v11/V11_STEP64_CI_GATE_STEP63_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`（commit：11305b2）。
  - Step 65：research_bundle 输出规范（run-end 研究消费入口目录布局与命名，单 run 与多 run 聚合物理隔离，纳入 evidence package + manifest 写实）（规格见：`docs/v11/V11_STEP65_RESEARCH_BUNDLE_OUTPUT_CONTRACT_20251230.md`）。
  - Step 65（Quant 落地记录）：`docs/v11/V11_STEP65_RESEARCH_BUNDLE_OUTPUT_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`（commit：8dab067）。
  - Step 66：CI 必跑 Step65 集成测试（`tools/test_step65_research_bundle.py`），任何偏离 Step65 契约即阻断合并（规格见：`docs/v11/V11_STEP66_CI_GATE_STEP65_ACCEPTANCE_20251230.md`）。
  - Step 66（Quant 落地记录）：`docs/v11/V11_STEP66_CI_GATE_STEP65_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`（commit：fc8d267）。
  - Step 67：research_bundle 单入口文件 entry.json（fact-only）：冻结 schema、sha256_16/byte_size 与 evidence_ref_index 复核规则，并写入 run_manifest 以便研究侧程序一键加载（规格见：`docs/v11/V11_STEP67_RESEARCH_BUNDLE_ENTRYPOINT_CONTRACT_20251230.md`）。
  - Step 68：run-end gate 集成并校验 Step67 entry.json（启用时 fail-closed=exit2），并确保 entry.json 被 evidence package 覆盖且 manifest 写实（规格见：`docs/v11/V11_STEP68_RUN_END_GATE_STEP67_ENTRYPOINT_INTEGRATION_20251230.md`）。
  - Step 68（Quant 落地记录）：`docs/v11/V11_STEP68_RUN_END_GATE_STEP67_ENTRYPOINT_INTEGRATION_IMPLEMENTED_IN_QUANT_20251230.md`（commit：150da05）。
  - Step 69：CI 必跑 Step68 集成测试（`tools/test_step68_entrypoint.py`），任何偏离 Step67+68 契约即阻断合并（规格见：`docs/v11/V11_STEP69_CI_GATE_STEP68_ACCEPTANCE_20251230.md`）。
  - Step 69（Quant 落地记录）：`docs/v11/V11_STEP69_CI_GATE_STEP68_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`（commit：f2a1b41）。
  - Step 70：跨 run 研究入口索引 research_entry_index.json（fact-only）：聚合 runs_root 下每个 run 的 research_bundle/entry.json，用于批量检索/归档，并提供 sha256_16 可复核字段与混扫防护规则（规格见：`docs/v11/V11_STEP70_CROSS_RUN_RESEARCH_ENTRY_INDEX_CONTRACT_20251230.md`）。
  - Step 71：CI 必跑 Step70 跨 run 聚合索引（scan_root 固定为 runs_step54_test），生成并校验 research_entry_index.json，空跑=FAIL 且禁止跳过（规格见：`docs/v11/V11_STEP71_CI_GATE_STEP70_CROSS_RUN_INDEX_20251230.md`）。
  - Step 71（Quant 落地记录）：`docs/v11/V11_STEP71_CI_GATE_STEP70_CROSS_RUN_INDEX_IMPLEMENTED_IN_QUANT_20251230.md`（commit：a313aa6）。

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


