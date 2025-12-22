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
- 执行接口差异落盘（CCXT vs OKX官方库）：`docs/v10/V10_EXECUTION_INTERFACE_DIFF_LOG_OKX_CCXT.md`
- C2.0 事故处置手册（Incident Runbook + 证据包标准）：`docs/v10/V10_INCIDENT_RUNBOOK_C2_0_20251222.md`
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
- C阶段总览（人话版，C0.1→C1.2）：`docs/v10/V10_C_STAGE_OVERVIEW_C0_TO_C1_20251222.md`
- 隐含围栏审计协议（Fence Inventory + Gating Telemetry；**原则4：演化遵从自然选择**的硬核检验）：`docs/v10/V10_HIDDEN_FENCE_AUDIT_PROTOCOL_20251222.md`
- 围栏审计核对表（逐条 Pass/Fail，防“围栏偷偷变策略”）：`docs/v10/V10_FENCE_AUDIT_CHECKLIST_PRINCIPLE4_20251222.md`


