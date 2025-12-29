# V11 Design (execution_world) — Architecture Spec — 2025-12-27

目的：把 V11 baseline 的“合同/协议/验收条款”汇总为一份**可实现、可审计、可锁版**的架构说明（Design），用于约束实现仓库（Prometheus-Quant）后续迭代。  

关系声明（重要）：
- **SSOT（变更口径）**：`docs/v10/V11_BASELINE_CHANGELOG_20251226.md`（只增不改）
- **Contracts（模块契约）**：`docs/v10/` 下若干 `...CONTRACT_*.md`
- **本文件（Design）**：解释“模块如何组合成执行世界”，并定义 V11 的**运行闭包（closure）与防旧代码污染策略**。

本文件只允许追加（additive-only）；破坏性变更必须提升 major（V12…）并重跑最小 PROBE。

相关附录：
- **V11 execution_world 运行闭包白名单（closure allowlist）**：`docs/v10/V11_EXECUTION_WORLD_CLOSURE_ALLOWLIST_20251227.md`

---

## 0) V11 一句话

V11 的 execution_world 是：**core 只产 intent；交易员（BrokerTrader）是唯一写入口；Ledger 只归档交易所真值；缺真值就降级为 unknown 或 STOP；所有结论必须能用交易所 JSON 复现。**

---

## 1) 设计约束（来自“骑士事故”的系统性防线）

我们不把安全寄托在“某段 if/封锁代码不会被人剪掉”。V11 的防线必须落在更难被误改的结构上：

- **运行闭包白名单（closure allowlist）**：execution_world 的可执行入口只允许依赖 v11 闭包模块；任何 `v10`/legacy 路径必须在闭包外（物理不可达）。
- **能力隔离（write capability）**：只有 BrokerTrader 拥有交易所写能力；core/runner 不得直接接触 connector 的写接口。
- **Fail closed**：证据链缺口宁可 STOP/冻结，也不允许“默认值继续跑”污染后续裁决与演化结论。
- **版本化口径**：`contract_version` 进入 `run_manifest`；版本不匹配必须 STOP（拒绝“兼容猜测”）。

> 解释：这不是“更复杂的封锁”，而是把风险从“可被 CTRL+X 的代码块”迁移到“依赖闭包与能力边界”。

---

## 2) 世界类型与语义边界（hard）

V11 明确区分两种世界：

- **`execution_world`**（OKX demo/live）：交易所是真值，所有资金/仓位/成交/费用必须来自可回查 JSON（或 unknown）。
- **`offline_sim`**：允许内部模拟，但其结论不得冒充 execution_world 的真值链（只能用于研究对照）。

核心规则（hard）：
- execution_world 下，**Agent/DecisionEngine 不得内部模拟成交/仓位/资金变化为真值**。  
- core 的职责：计算并输出 intent（open/close/hold），并把决策链证据化（append-only）。

参考：
- `docs/v10/V11_BASELINE_CHANGELOG_20251226.md`（§2.1）
- `docs/v10/V10_MODULE_PROBE_AND_INTERFACE_FREEZE_PROTOCOL_20251225.md`（CoreWorldLock）

---

## 3) 模块分层（唯一正确的依赖方向）

### 3.1 Core 层（无 IO，纯意图）

包含：
- `Genome` / `DecisionEngine` / `Agent` / `SystemManager`（只做调度，不做交易所 IO）

输出：
- `intent_action ∈ {open, close, hold}`
- `intent_desired_state ∈ {IN_MARKET, OUT_MARKET}`（语义上是“想要的状态”，不是成交）
- `decision_trace.jsonl`（append-only：tick_summary + agent_detail +（可选）order_execution记录）

### 3.2 World 层（IO + 真值 + 入册）

包含：
- **BrokerTrader**（唯一交易入口，执行 + 入册）
- **Ledger**（真值快照聚合，Tier-1 evidence）
- **ProbeGating**（真值画像 + 探针激活/禁用 + STOP/continue）
- ExecutionFreeze / Reconciliation / RunArtifacts（运行安全与证据包）
- **ExchangeAuditor**（只读交叉核验，evidence-only）

依赖方向（hard）：
- Core →（intent）→ BrokerTrader  
- BrokerTrader/Connector → Exchange（读写）  
- Ledger/ProbeGating → Core（只提供探针向量与质量，不提供“伪真值”）  
- ExchangeAuditor 只读，不得干预执行

参考：
- `docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`
- `docs/v10/V10_TRUTH_PROFILE_AND_PROBE_GATING_CONTRACT_20251226.md`
- `docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`

---

## 4) 真值画像（truth_profile）与 ProbeGating（hard）

### 4.1 truth_profile 的意义

`truth_profile` 是“结论有效性门槛”的契约级开关，不是普通 runtime flag。

允许值（baseline）：
- `degraded_truth`：demo 观察模式；缺 probe 必须标注 unknown；对真实 PnL/费用的结论通常 NOT_MEASURABLE
- `full_truth_pnl`：live 结论模式；关键真值缺失必须 STOP + IEB

### 4.2 ProbeGating 输出（必须固定维度）

ProbeGating 必须输出：
- 固定维度 probe 向量（Core 不得因 demo/live 改维度）
- 每个 probe 的 `mask/quality` 与 `reason_code`
- `gating_decision`: continue 或 stop

hard rules：
- **unknown 不得伪造为 0**；若用数值占位，必须同时提供 mask/quality/reason 且可审计。
- 只允许最小“历史投影”类 derived probes（如 `capital_health_ratio`、`position_exposure_ratio`），禁止复杂二次推断。

参考：`docs/v10/V10_TRUTH_PROFILE_AND_PROBE_GATING_CONTRACT_20251226.md`

### 4.3 World-level “执行摩擦”探针作为输入（观测不执法）

在 V11 baseline 中，除市场外显（E probes）外，允许把 world-level 的执行摩擦事实统计/投影作为 DecisionEngine 输入维度，以支持演化与消融对照：

- **MFStats（事实统计）**：来自 BrokerTrader 的 tick 级 order samples，经 `MFStatsWindow` 形成固定维度统计（例如 P2 闭合率、L1 拒绝率、ack→P2 延迟 p95）。
- **Comfort（投影）**：由 MFStats 投影得到的单值 `comfort_value ∈ [-1, +1]`，定位为“世界舒适度传感器”，不是 gate。

硬边界（hard）：
- **不改变 hard gate**：交易冻结/STOP 仍由证据链失败（P2 逾期、账号受限、真值缺失等）与 ProbeGating 的 `gating_decision` 决定；不得把 comfort/MFStats 写成阈值电闸。
- **fixed-dim per run**：一旦在某个 run 的输入向量中引入 MFStats/Comfort，必须在 `run_manifest.json` 里冻结 `feature_contract_version` 与 `PROBE_ORDER`（同 run 内不得改顺序/维度）。
- **mask 纪律**：MFStats/Comfort 不可测时必须 `mask=0 + reason_code`；DecisionEngine 必须尊重 mask（mask=0 维度不参与）。

---

## 5) BrokerTrader：唯一交易入口（hard）

BrokerTrader 只做两件事：
1) 执行：接收 intent，向交易所提交请求（place/cancel/confirm）
2) 入册：把交易所返回 JSON 事实 append-only 落盘（可回查）

关键点：
- `clOrdId` 绑定 `agent_id`（归因锚点）；订单主键以 `ordId` 为准（可脱敏 hash）
- 遵守 **订单确认协议 P0–P5**：ack≠成交；所有 ack 必须 P2 可回查终态；否则冻结/STOP
- 执行异常必须做 L1 分类并写 `recommended_action`（runner 决定 STOP）

参考：
- `docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`
- `docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`

---

## 6) Ledger：真值聚合与最小注入（truth-backed）

Ledger 的定位是“真值记录/归档 + 最小聚合”，不是“内部记账发明者”。  

核心原则：
- 真值来源仅为交易所 JSON（orders/fills/bills/positions/equity）
- 对无法证明的字段输出 `null + truth_quality + reason_code`

输出示例（概念层）：
- `capital_health_ratio`（derived-only）
- `position_exposure_ratio`（derived-only，且受 `positions_truth_quality` gating）

与 Reconciliation 的关系：
- “账不平”在 V11 中应表达为：`evidence_incomplete / join_broken / truth_degraded`，触发 freeze/STOP，而不是内部补账。

参考：
- `docs/v10/V10_POST_RUN_LEDGER_AUDIT_CONTRACT_20251226.md`
- `docs/v10/V10_EXECUTION_FREEZE_ON_RECONCILIATION_FAILURE_CONTRACT_20251226.md`

---

## 7) LifecycleJudge：死亡/繁殖审判（不交易）

职责：
- 基于结算后的 metrics_snapshot（带 truth_quality）给出 `KEEP/DEATH/REPRODUCE`
- 输出 append-only 的 `lifecycle_events.jsonl`
- 不连接交易所写接口；需要强平时通过 BrokerTrader 的 lifecycle flatten 入口

编排顺序（baseline）：
1) 计算：生成 metrics_snapshot（truth-backed）
2) 结算：system_flatten + absorb（证据化）
3) 审判：LifecycleJudge 输出裁决清单（append-only）
4) 执行：runner 执行死亡/繁殖（不直接交易）

参考：`docs/v10/V10_LIFECYCLE_JUDGE_MODULE_CONTRACT_20251226.md`

---

## 8) ExchangeAuditor：只读交叉核验（evidence-only）

职责：
- 独立只读连接交易所，对 BrokerTrader 入册证据做交叉核验
- 输出 `auditor_report.json` 与 `auditor_discrepancies.jsonl`
- baseline：只落盘，不干预（未来若要干预需要单独契约与验收 gate）

### 8.1 审计结论（verdict）与退出码（exit_code）冻结

ExchangeAuditor 的结论分为三类：`PASS / NOT_MEASURABLE / FAIL`。为保证 CI/CD 与批量回放行为稳定，V11 baseline 冻结 verdict → exit_code 映射：

- `PASS` → `exit_code=0`
- `NOT_MEASURABLE` → `exit_code=0`（必须打印 WARNING；表示审计范围不完整，不阻塞 pipeline）
- `FAIL` → `exit_code=2`（critical）

注意：`NOT_MEASURABLE` 不是“通过”，而是“无法证明”。当存在必做检查项尚未实现（例如 orphan detection / 分页未闭合）时，必须降级为 NOT_MEASURABLE，并在 report 内自包含原因。

### 8.2 contract_versions 字段拆分（写实、可追溯）

`auditor_report.json` 必须把版本信息拆分为可追溯字段（避免 “evidence_schema_version” 语义混用）：

- `auditor_contract_version`（模块契约版本）
- `auditor_schema_version`（审计报告输出 schema）
- `broker_trader_evidence_schema_version`（证据生产者：BrokerTrader）
- `ledger_schema_version`（证据生产者：Ledger）
- `probe_gating_schema_version`（证据生产者：ProbeGating）
- `order_confirmation_protocol_version`（P0/P1/P2…协议版本）

参考：`docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`

---

## 9) C 维度（Collective）：群体现象（t-1 intent），作为“演化规则”消融点

我们不把“从众性”做成不可观测基因；我们把它做成可开关的“规则/机制”，用消融验证是否产生可观测差异。

### 9.1 定义（baseline）

数据源：上一 tick（t-1）的 intent 分布（open/close/hold），来自 `decision_trace.jsonl` 的 `agent_detail.intent_action`。  

最小 probe（单探针）：
- `C_prev_net_intent = open_ratio(t-1) - close_ratio(t-1)`，范围 \([-1, +1]\)

tick=1 规则（hard）：
- 无 \(t-1\) → C 为 unknown（不得伪造 0）；若需要固定维度，可通过 `mask/reason_code` 表达不可用。

### 9.2 消融协议（验证规则成立性）

- A：`C_off`（C 探针禁用/置 unknown + mask=0）
- B：`C_on`（启用 t-1 intent C probe）

保持其他条件一致（seed/初始化分布/mutation_rate/truth_profile/市场输入），对比可复现差异：
- 生存率、死亡原因分布
- intent_entropy 的时间曲线（群体同步性）
- 群体耦合度指标（agent intent 与 C 的相关性，仅用于分析，不进入交易真值链）

该设计的价值是：无论差异正负，只要“可复现可观测”，实验即成功。

> 该 C 定位为 social/internal signal：不得用成交/收益/ROI 作为 C 输入（避免隐性策略与 truth_profile 混用）。

---

## 10) 证据链与产物（run_dir 必备）

最低证据集合（append-only 为主）：
- `run_manifest.json`（包含 truth_profile、contract_version 等）
- `decision_trace.jsonl`
- `ledger_ticks.jsonl`
- `order_attempts.jsonl`、`order_status_samples.jsonl`（若发生下单或 ack）
- `errors.jsonl`（任何降级/冻结/STOP 原因）
- `FILELIST.ls.txt`、`SHA256SUMS.txt`（证据包可验）

Step 26 的最小可复核清单（DecisionEngine inputs: E + MFStats + Comfort）：
- `docs/v10/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
Step 28（run-end 证据包打包 + Gate，fail-closed）：
- `docs/v10/V11_STEP28_EVIDENCE_PACKAGING_GATE_20251229.md`
Step 29（CI Evidence Gate：fixture-based，fail-closed，防未来改动破坏 Step26 可复核性）：
- `docs/v10/V11_STEP29_CI_EVIDENCE_GATE_STEP26_20251229.md`
Step 30（Quant runner 已强制接入 run-end evidence gate：不可绕过，FAIL/ERROR=exit 2）：
- `docs/v10/V11_STEP30_RUN_END_EVIDENCE_GATE_IMPLEMENTED_20251229.md`
Step 31（扩展 verifier 到 Tier-1：Ledger + ProbeGating + Errors 的最小一致性）：
- `docs/v10/V11_STEP31_EXTEND_EVIDENCE_VERIFIER_TIER1_20251229.md`
Step 31（Quant 落地记录：CI gate 与 run-end gate 自动升级覆盖 Tier-1）：
- `docs/v10/V11_STEP31_TIER1_VERIFIER_IMPLEMENTED_IN_QUANT_20251229.md`
Step 32（Orphan Detection 最小可测：orders-level，分页闭合 + clOrdId 命名空间）：
- `docs/v10/V11_STEP32_ORPHAN_DETECTION_MIN_MEASURABLE_20251229.md`
Step 32（Quant 落地记录）：
- `docs/v10/V11_STEP32_ORPHAN_DETECTION_IMPLEMENTED_IN_QUANT_20251229.md`
Step 33（P3/P4 最小可测：fills/bills 分页闭合 + join + 幂等）：
- `docs/v10/V11_STEP33_FILLS_BILLS_JOIN_MIN_MEASURABLE_20251229.md`
Step 33（Quant 落地记录）：
- `docs/v10/V11_STEP33_FILLS_BILLS_JOIN_IMPLEMENTED_IN_QUANT_20251229.md`
Step 34（分页闭合证据：paging_traces.jsonl append-only，作为 closure proof）：
- `docs/v10/V11_STEP34_PAGING_TRACES_APPEND_ONLY_20251229.md`
Step 34（Quant 落地记录）：
- `docs/v10/V11_STEP34_PAGING_TRACES_IMPLEMENTED_IN_QUANT_20251229.md`
Step 35（gates 强制要求 paging_traces：verifier/run-end/CI，不可绕过）：
- `docs/v10/V11_STEP35_REQUIRE_PAGING_TRACES_IN_GATES_20251229.md`
Step 35（Quant 落地记录）：
- `docs/v10/V11_STEP35_REQUIRE_PAGING_TRACES_IMPLEMENTED_IN_QUANT_20251229.md`
Step 36（冻结 auditor_report 的 paging coverage 字段：page_count/closure_proved/trace_range）：
- `docs/v10/V11_STEP36_AUDITOR_PAGING_COVERAGE_FIELDS_20251229.md`
Step 36（Quant 落地记录）：
- `docs/v10/V11_STEP36_AUDITOR_PAGING_COVERAGE_IMPLEMENTED_IN_QUANT_20251229.md`
Step 37（paging query_chain_id/scope_id：防 paging_traces 混链歧义）：
- `docs/v10/V11_STEP37_PAGING_QUERY_CHAIN_ID_20251229.md`
Step 37（Quant 落地记录）：
- `docs/v10/V11_STEP37_PAGING_QUERY_CHAIN_ID_IMPLEMENTED_IN_QUANT_20251229.md`
Step 38（run_manifest 冻结 audit scope anchors，防审计范围漂移）：
- `docs/v10/V11_STEP38_AUDIT_SCOPE_ANCHORS_IN_MANIFEST_20251229.md`
Step 38（Quant 落地记录）：
- `docs/v10/V11_STEP38_AUDIT_SCOPE_ANCHORS_IMPLEMENTED_IN_QUANT_20251229.md`
Step 39（audit_scope_id 作为全局主锚点：跨文件 join 与 verifier fail-closed）：
- `docs/v10/V11_STEP39_AUDIT_SCOPE_ID_AS_GLOBAL_ANCHOR_20251229.md`
Step 39（Quant 落地记录）：
- `docs/v10/V11_STEP39_AUDIT_SCOPE_ID_GLOBAL_ANCHOR_IMPLEMENTED_IN_QUANT_20251229.md`
Step 40（run_manifest.audit_scopes[]：多次审计 append-only，不覆盖）：
- `docs/v10/V11_STEP40_MANIFEST_AUDIT_SCOPES_APPEND_ONLY_20251229.md`
Step 40（Quant 落地记录）：
- `docs/v10/V11_STEP40_MANIFEST_AUDIT_SCOPES_IMPLEMENTED_IN_QUANT_20251229.md`
Step 41（审计链 evidence_refs 统一协议：可机器追踪 + SHA256 覆盖）：
- `docs/v10/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`
Step 41（Quant 落地记录）：
- `docs/v10/V11_STEP41_EVIDENCE_REFS_STANDARD_IMPLEMENTED_IN_QUANT_20251229.md`
Step 42（审计链 evidence_refs 强约束升级：gate-on 时 sha256_16 强制，jsonl 行号强制）：
- `docs/v10/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`
Step 42（Quant 落地记录）：
- `docs/v10/V11_STEP42_EVIDENCE_REFS_HARDENING_IMPLEMENTED_IN_QUANT_20251229.md`
Step 43（evidence_ref_index：把 hash/行号复算成本从 verifier 挪到 run-end gate）：
- `docs/v10/V11_STEP43_EVIDENCE_REF_INDEX_20251229.md`
Step 43（Quant 落地记录）：
- `docs/v10/V11_STEP43_EVIDENCE_REF_INDEX_IMPLEMENTED_IN_QUANT_20251229.md`
Step 44（evidence_refs 可解引用校验：防止“形式正确但指向无关行”）：
- `docs/v10/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_20251229.md`
Step 44（Quant 落地记录）：
- `docs/v10/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_IMPLEMENTED_IN_QUANT_20251229.md`
Step 45（evidence_refs 语义 join 校验：防止同 run 内“指向无关行”）：
- `docs/v10/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_20251229.md`
Step 45（Quant 落地记录）：
- `docs/v10/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_IMPLEMENTED_IN_QUANT_20251229.md`
Step 46（Evidence Gate Bundle 冻结：contract_version/fixtures/exit codes/artifacts）：
- `docs/v10/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_20251229.md`
Step 46（Quant 落地记录）：
- `docs/v10/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_IMPLEMENTED_IN_QUANT_20251229.md`
Step 47（基因/特征/账簿 SSOT 总审计：has_position 退役，I/C 口径冻结）：
- `docs/v10/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`
Step 47（Quant 落地记录）：
- `docs/v10/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`
Step 48（I/C 注入 SSOT：Ledger triad → I probes；C_prev_net_intent(t-1)）：
- `docs/v10/V11_STEP48_I_C_PROBES_INJECTION_SSOT_20251230.md`
Step 48（Quant 落地记录）：
- `docs/v10/V11_STEP48_I_C_PROBES_INJECTION_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`

### 10.1 世界参数变更协议（World Parameters Change Protocol）

execution_world 的“世界参数”（例如 `tick_seconds`、API 请求预算、舒适度/摩擦的 `half_life_seconds` 等）属于 **外部世界条件**，不是策略围栏；但它们一旦变动，就会改变观测与执行条件，因此必须证据化与可追溯。

硬规则（V11 baseline）：
- **只允许在 run 边界变更**：同一个 run 内不得悄悄修改世界参数（避免不可复现）。
- **必须写入 `run_manifest.json`**（additive-only）：记录参数值 + `change_reason_code`（若为变更 run）+ 证据引用（例如 VPS 网络画像/交易所规则摘要/历史对比报告）。
- **环境变化允许参数变化**：例如 VPS 升级、网络路径变化、交易所规则变化；但每次变化都必须作为“环境变更”被记录并用于后续分析分组（避免误归因到策略差异）。

参考：
- `docs/v10/V10_ACCEPTANCE_CRITERIA.md`
- `docs/v10/V10_MODULE_PROBE_AND_INTERFACE_FREEZE_PROTOCOL_20251225.md`

---

## 11) V10 锁版与 V11 “零继承语义”的落地方式（建议）

我们不做“全零继承重写”，而是做：
- **零继承执行链路与语义**：V11 execution_world 入口只依赖 v11 闭包（allowlist），v10/legacy 物理不可达。
- **允许复用纯组件**：纯函数/纯数学（例如网络前向、序列化、hash、统计）可复用，但必须在 v11 namespace 下重新冻结 contract_version。

目标：把“误调用旧代码”的风险从“人为纪律”转为“结构不可达”。

---

## 12) Freeze 策略（接口冻结纪律）

通过 Gate/PROBE 后冻结：
- module public API（方法签名 + 语义）
- evidence schema（json/jsonl 字段含义）
- reason_code / taxonomy（additive-only）

破坏性变更必须：
- bump `contract_version`
- 重跑最小 PROBE
- 更新 SSOT（`V11_BASELINE_CHANGELOG`）与本 design 的追加条目


