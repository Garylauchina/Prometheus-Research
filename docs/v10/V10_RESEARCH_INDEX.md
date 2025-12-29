# V10 Research Index（研究索引页）

目的：让 `Prometheus-Research` 真正成为“研究项目仓库”，而不是文档堆。  
原则：每条结论都必须能指回**可复核证据路径**（实验结果目录、summary JSON、落盘的 behaviors/genomes）。

---

## 1) 当前结论（最短版）

- **结论A（时间结构）**：A（真实时间结构）在多个窗口中稳定优于 B2（破坏时间结构的零假设）——体现在 `system_roi` 与/或 `extinction_rate`。
- **结论B（机制承载）**：差异可以被追溯到 Agent 行为簇与基因表达通道（IN/OUT 网络），而不是“故事”。
- **结论C（硬化审计）**：赢家口径（abs+anchor）、IN/OUT同向性（v2）、赢家人群分层稳定性（v3）已被纳入正式验收标准。

---

## 2) 验收标准（项目宪法）

- **验收标准**：`docs/v10/V10_ACCEPTANCE_CRITERIA.md`
  - Gate 0：可复现/可审计/对照物理合理/无数值爆炸/资金闭合
  - Gate 1：A vs B2 的主指标裁决
  - Gate 2：窗口迁移与赢家口径固定（v2）
  - Gate 3：消融 + IN/OUT同向性（v2）+ 分层稳定性（v3）
  - Hidden fences：围栏清单 + 触发率遥测（防异常收敛）
  - **方法论（如何“测量”复杂系统）**：`docs/v10/V10_METHOD_MEASURING_COMPLEX_SYSTEMS.md`
- **V11 基线变更记录（execution_world 大版本重构 SSOT）**：`docs/v10/V11_BASELINE_CHANGELOG_20251226.md`
- **V11 设计文档（execution_world 架构说明，闭包白名单 + 模块编排）**：`docs/v10/V11_DESIGN_EXECUTION_WORLD_20251227.md`
- **V11 运行闭包白名单（closure allowlist，防 legacy/v10 误接回执行链路）**：`docs/v10/V11_EXECUTION_WORLD_CLOSURE_ALLOWLIST_20251227.md`
- **V11 程序员AI操作规则（简洁版，一页规程）**：`docs/v10/V11_PROGRAMMER_AI_OPERATING_RULES_20251227.md`
- **V11 Step 26（DecisionEngine 输入接入 MFStats/Comfort，观测不执法，mask=0 不参与）**：
  - SSOT：`docs/v10/V11_BASELINE_CHANGELOG_20251226.md`（§2.5 追加条目）
  - Design：`docs/v10/V11_DESIGN_EXECUTION_WORLD_20251227.md`（§4.3）
- **V11 Step 27（Step26 证据包最小复核清单 + 一键校验脚本）**：
  - Checklist：`docs/v10/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
  - Verifier：`tools/verify_step26_evidence.py`
- **V11 Step 28（run-end 证据包打包 + Gate，fail-closed）**：
  - Spec：`docs/v10/V11_STEP28_EVIDENCE_PACKAGING_GATE_20251229.md`
- **V11 Step 29（CI Evidence Gate：fixture-based，fail-closed）**：
  - Spec：`docs/v10/V11_STEP29_CI_EVIDENCE_GATE_STEP26_20251229.md`
- **V11 Step 30（Quant runner 强制 run-end evidence gate，fail-closed）**：
  - Record：`docs/v10/V11_STEP30_RUN_END_EVIDENCE_GATE_IMPLEMENTED_20251229.md`
- **V11 Step 31（扩展 verifier 到 Tier-1：Ledger + ProbeGating + Errors 一致性）**：
  - Spec：`docs/v10/V11_STEP31_EXTEND_EVIDENCE_VERIFIER_TIER1_20251229.md`
  - Record（Quant 落地）：`docs/v10/V11_STEP31_TIER1_VERIFIER_IMPLEMENTED_IN_QUANT_20251229.md`
- **V11 Step 32（Orphan Detection 最小可测：orders-level）**：
  - Spec：`docs/v10/V11_STEP32_ORPHAN_DETECTION_MIN_MEASURABLE_20251229.md`
  - Record（Quant 落地）：`docs/v10/V11_STEP32_ORPHAN_DETECTION_IMPLEMENTED_IN_QUANT_20251229.md`
- **V11 Step 33（fills/bills join 最小可测：P3/P4）**：
  - Spec：`docs/v10/V11_STEP33_FILLS_BILLS_JOIN_MIN_MEASURABLE_20251229.md`

---

## 3) 关键“判例”（从现象到机制）

### 3.1 A vs B2 的基础裁决

- A vs B2（基线裁决）：`docs/v10/V10_ACCEPTANCE_DECISION_A_vs_B2_20251221.md`

### 3.2 Prior leakage（消融链）

- M消融：`docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_M_A_vs_B2_20251221.md`
- C消融：`docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_C_A_vs_B2_20251221.md`
- E子集（OHLCV only）：`docs/v10/V10_ACCEPTANCE_DECISION_ABLATION_E_OBONLY_A_vs_B2_20251221.md`
- I消融与I子集：`docs/v10/` 下若干 `...ABLATION_I...` 记录

### 3.3 Window migration（Gate 2.3）

- 一致性裁决：`docs/v10/V10_ACCEPTANCE_DECISION_WINDOW_MIGRATION_CONSISTENCY_I_MIN134_20251221.md`
- 里程碑：`docs/v10/V10_MILESTONE_GATE2_3_PASSED_20251221.md`

### 3.4 机制归因（B阶段闭环）

- run级机制线索（W2）：`docs/v10/V10_MECHANISM_ATTRIBUTION_W2_I_MIN134_RUN_CLUSTERS_20251221.md`
- Agent级机制裁决：
  - W2：`docs/v10/V10_ACCEPTANCE_DECISION_MECHANISM_ATTRIBUTION_W2_I_MIN134_20251221.md`
  - W1b：`docs/v10/V10_ACCEPTANCE_DECISION_MECHANISM_ATTRIBUTION_W1B_I_MIN134_20251221.md`
- 基因表达回溯：
  - W2：`docs/v10/V10_ACCEPTANCE_DECISION_GENE_ATTRIBUTION_W2_I_MIN134_20251221.md`
  - W1b：`docs/v10/V10_ACCEPTANCE_DECISION_GENE_ATTRIBUTION_W1B_I_MIN134_20251221.md`

### 3.5 v2/v3 审计硬化（让机制更像机制）

- v2协议：`docs/v10/V10_B_STAGE_V2_PROTOCOL_WINNER_DEFINITION_AND_SIGN_CONSISTENCY.md`
- v2审计补充：
  - W2：`docs/v10/V10_ACCEPTANCE_DECISION_B_STAGE_V2_AUDIT_W2_I_MIN134_20251221.md`
  - W1b：`docs/v10/V10_ACCEPTANCE_DECISION_B_STAGE_V2_AUDIT_W1B_I_MIN134_20251221.md`
- v3分层稳定性审计：
  - W2：`docs/v10/V10_ACCEPTANCE_DECISION_B_STAGE_V3_STRATIFIED_STABILITY_W2_I_MIN134_20251221.md`
  - W1b：`docs/v10/V10_ACCEPTANCE_DECISION_B_STAGE_V3_STRATIFIED_STABILITY_W1B_I_MIN134_20251221.md`
 - W1b vs W2 机制对照综合裁决：
  - `docs/v10/V10_ACCEPTANCE_DECISION_B_STAGE_SYNTHESIS_W1B_VS_W2_I_MIN134_20251221.md`

---

## 4) 下一步（Research队列）

### 4.1 v3.1（已完成：W2 trades 分箱退化修复）

结论与裁决书：

- `docs/v10/V10_ACCEPTANCE_DECISION_B_STAGE_V3_1_TRADES_STRATA_W2_I_MIN134_20251221.md`

### 4.2 进入 C 阶段前的“最后一关”

当 v3.1 完成后，再讨论：

- 虚拟盘执行指纹（滑点/部分成交/延迟/fee）落盘与一致性
- 运行边界、告警（含“三维共振”）与回放链

---

## 5) 阅读路径（给新读者）

1) `V10_ACCEPTANCE_CRITERIA.md`（规则）
2) `...WINDOW_MIGRATION_CONSISTENCY...`（Gate 2.3）
3) `...MECHANISM_ATTRIBUTION...`（B阶段闭环）
4) `...GENE_ATTRIBUTION...` + `...B_STAGE_V2/V3...`（机制硬化）

---

## 6.5) 研究假设备忘（副产品）

- 市场第一类假设 + 演化作为测量（不是目标，只是记录）：`docs/v10/V10_HYPOTHESIS_MARKET_TYPE1_EVOLUTION_AS_MEASUREMENT_20251222.md`

---

## 6) 目录页（更像“研究项目”）

- `docs/README.md`（全仓库 docs 索引）
- `docs/v10/README.md`（V10 文档目录页）

---

## 7) VPS / 产品化开发指导（C阶段入口）

- `docs/v10/V10_VPS_DEVELOPMENT_GUIDE.md`（英主中辅：安全基座、证据链、两级沙盒、火种库只增不改、快照规则）
- **模块封装→审计→锁版协议（PROBE + Interface Freeze）**：`docs/v10/V10_MODULE_PROBE_AND_INTERFACE_FREEZE_PROTOCOL_20251225.md`
- **代理交易员（BrokerTrader：执行+入册唯一入口）契约**：`docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`
- **订单确认协议（P0–P5：以交易所 JSON 为真值）**：`docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`
- **只读审计者（ExchangeAuditor：独立连接交易所审计交易员）契约**：`docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`
- **入册漏洞审计检查表（discrepancy taxonomy，append-only）**：`docs/v10/V10_BROKERTRADER_REGISTRY_AUDIT_CHECKLIST_20251226.md`
- **死亡/繁殖审判（LifecycleJudge）模块契约**：`docs/v10/V10_LIFECYCLE_JUDGE_MODULE_CONTRACT_20251226.md`
- **探针健康校验契约（启动完整校验 + 每tick轻量校验，可STOP）**：`docs/v10/V10_PROBE_HEALTHCHECK_CONTRACT_OKX_NATIVE_20251226.md`
- **真值画像（live开关）+ 探针激活门控（ProbeGating）契约（v2草案）**：`docs/v10/V10_TRUTH_PROFILE_AND_PROBE_GATING_CONTRACT_20251226.md`
- 执行接口差异落盘（CCXT vs OKX官方库）：`docs/v10/V10_EXECUTION_INTERFACE_DIFF_LOG_OKX_CCXT.md`
- **OKX原生 E 探针对齐契约（不做交叉对照、只保证映射+落盘）**：`docs/v10/V10_OKX_NATIVE_E_PROBES_MAPPING_CONTRACT_20251226.md`
- **事后账簿审计契约（实时可吸收、事后必须平账且可溯源）**：`docs/v10/V10_POST_RUN_LEDGER_AUDIT_CONTRACT_20251226.md`
- **实时不平账→冻结交易契约（execution_frozen，不下单，防证据污染）**：`docs/v10/V10_EXECUTION_FREEZE_ON_RECONCILIATION_FAILURE_CONTRACT_20251226.md`
- **Gate 4（VPS）：OKX Demo 演化内核（真实下单、无代理、无人工围栏）**：`docs/v10/V10_GATE4_OKX_DEMO_EVOLUTION_VPS.md`
- Gate 4（Mac）文档已标记为 deprecated：`docs/v10/V10_GATE4_OKX_DEMO_EVOLUTION_MAC.md`
- **交易执行模块合同（Execution Engine，OKX demo/live）**：`docs/v10/V10_EXECUTION_ENGINE_CONTRACT_OKX_DEMO_LIVE.md`
- **对账模块合同（Reconciliation，OKX 执行世界）**：`docs/v10/V10_RECONCILIATION_MODULE_CONTRACT_OKX_EXECUTION_WORLD.md`
- C2.0 事故处置手册（Incident Runbook + 证据包标准）：`docs/v10/V10_INCIDENT_RUNBOOK_C2_0_20251222.md`
- 启动前置契约（撤单/平仓/余额启动资金/按资金算Agent数量）：`docs/v10/V10_STARTUP_PREFLIGHT_AND_BOOTSTRAP_CONTRACT_20251223.md`
- 资金对账验证（交易所权益为真值：reconciliation events 落盘，PASSED）：`docs/v10/incidents/INCIDENT-20251223-C3_0-CAPITAL_RECONCILIATION_PASSED_OKX_DEMO_API.md`
- 启动链验证（Preflight+Bootstrap+1000/agent+floor，demo 执行世界 PASSED）：`docs/v10/incidents/INCIDENT-20251223-C3_1-PREFLIGHT_BOOTSTRAP_AGENT_ALLOCATION_PASSED_OKX_DEMO_API.md`
- C2.1 演练记录（STOP语义：ops-only 故障注入 → interrupted + stop_* + IEB）：`docs/v10/incidents/INCIDENT-20251223-C2_1-STOP_DRILL_OKX_DEMO_API.md`
- C2.2 演练记录（退化注入：网络降级/断连 fallback → IEB；本次退化遥测证据不足，记为 partial pass）：`docs/v10/incidents/INCIDENT-20251223-C2_2-DEGRADATION_NETWORK_DISCONNECT_OKX_DEMO_API.md`
- C2.3 演练记录（退化遥测硬门槛：error_count>0 或 error_events非空；本次 FAILED）：`docs/v10/incidents/INCIDENT-20251223-C2_3-DEGRADATION_TELEMETRY_GATE_FAILED_OKX_DEMO_API.md`
- C2.3 RERUN 记录（ops/证据层增强后：telemetry gate PASSED；本次事件以 api_error 为主）：`docs/v10/incidents/INCIDENT-20251223-C2_3-RERUN_TELEMETRY_GATE_PASSED_OKX_DEMO_API.md`
- C2.4 演练记录（Network-Degradation 专项硬门槛：出现 timeout/connection_error/request_exception；本次 PASSED，捕获 connection_error）：`docs/v10/incidents/INCIDENT-20251223-C2_4-NETWORK_DEGRADATION_GATE_PASSED_OKX_DEMO_API.md`
- C阶段起点里程碑（C0.5/G4.5证据链闭环，OKX REST）：`docs/v10/V10_MILESTONE_C0_5_G4_5_OKX_REST_EVIDENCE_CHAIN_PASSED_20251221.md`
- C0.7 里程碑（positions fallback 证据链通过）：`docs/v10/V10_MILESTONE_C0_7_POSITIONS_FALLBACK_PASSED_20251221.md`
- C0.8 里程碑（positions 重建 raw 证据可追溯）：`docs/v10/V10_MILESTONE_C0_8_POSITIONS_RAW_EVIDENCE_PASSED_20251221.md`
- C0.9 里程碑（M 执行 raw 证据落盘）：`docs/v10/V10_MILESTONE_C0_9_M_EXECUTION_RAW_EVIDENCE_PASSED_20251221.md`
- C1.0 协议（1小时长跑证据链压力测试）：`docs/v10/V10_C_STAGE_C1_0_LONG_RUN_PROTOCOL_20251221.md`
- C1.0 里程碑（阶段性：STOP语义通过，证据链不断）：`docs/v10/V10_MILESTONE_C1_0_STOP_SEMANTICS_PASSED_20251221.md`
- C1.0 里程碑（1小时长跑通过，证据链稳定）：`docs/v10/V10_MILESTONE_C1_0_LONG_RUN_PASSED_20251221.md`
- C1.1 协议（raw证据增长控制：分片+索引+hash）：`docs/v10/V10_C_STAGE_C1_1_RAW_GROWTH_CONTROL_PROTOCOL_20251221.md`
- C1.1 里程碑（raw增长控制通过：分片+索引+hash+manifest引用）：`docs/v10/V10_MILESTONE_C1_1_RAW_GROWTH_CONTROL_PASSED_20251221.md`
- C1.2 协议（过夜长跑 6–8h 压测证据链 + 分片索引）：`docs/v10/V10_C_STAGE_C1_2_OVERNIGHT_LONG_RUN_PROTOCOL_20251221.md`
- C1.2 里程碑（6小时长跑通过）：`docs/v10/V10_MILESTONE_C1_2_OVERNIGHT_LONG_RUN_PASSED_20251221.md`
- C1.3 协议（24小时长跑压测证据链 + 分片索引）：`docs/v10/V10_C_STAGE_C1_3_24H_LONG_RUN_PROTOCOL_20251222.md`
- C1.3 里程碑（24小时长跑通过）：`docs/v10/V10_MILESTONE_C1_3_24H_LONG_RUN_PASSED_20251223.md`
- C阶段总览（人话版，C0.1→C1.2）：`docs/v10/V10_C_STAGE_OVERVIEW_C0_TO_C1_20251222.md`
- 隐含围栏审计协议（Fence Inventory + Gating Telemetry；**原则4：演化遵从自然选择**的硬核检验）：`docs/v10/V10_HIDDEN_FENCE_AUDIT_PROTOCOL_20251222.md`
- 围栏审计核对表（逐条 Pass/Fail，防“围栏偷偷变策略”）：`docs/v10/V10_FENCE_AUDIT_CHECKLIST_PRINCIPLE4_20251222.md`


