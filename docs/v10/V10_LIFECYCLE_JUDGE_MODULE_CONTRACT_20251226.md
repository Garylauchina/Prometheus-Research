# V10 LifecycleJudge Module Contract (Death/Reproduction adjudication) — 2025-12-26

目的：把“死亡/繁殖审判”从 runner/主程序中剥离出来，形成可审计、可复现、可锁版的模块。  
定位：LifecycleJudge 属于 **生命周期层（生态围栏）**，它可以使用阈值/淘汰比例等规则，但这些规则不得渗入决策链路（Genome+Features→Intent）。

---

## 0) 第一性原则（hard）

1) **不碰交易所写接口**
- LifecycleJudge 不下单、不撤单、不平仓，不直接连接交易所的写端点。

2) **真值只来自证据链**
- 在 `execution_world` 中，任何涉及资金/仓位/成交/费用的输入必须来自交易所可回查 JSON 的证据聚合（Ledger/Registry/Audit），或标注 `null + reason_code`。
- 不允许用“内部模拟资金/仓位”替代真值。

3) **append-only**
- 所有生命周期裁决必须 append-only 落盘。不得改写既有裁决记录。

4) **裁决与执行解耦**
- LifecycleJudge 只产出“裁决”（death/reproduce/keep），不负责“执行”（创建新 agent、迁移基因、重置状态等）。
- 执行由上层编排器（runner/SystemManager）完成，但必须可回指到裁决证据。
- 若裁决需要“强平/归零风险敞口”，该写操作必须由 BrokerTrader 执行并正常入册（本模块只发出执行请求，不直接交易）。

---

## 0.5) 周期内必备的“交易所实时输入”（execution_world）

LifecycleJudge 的 ROI/结算裁决依赖交易员账簿（registry/ledger）为主，但周期内仍需要交易所实时信息由 BrokerTrader 获取并落盘（至少一次/周期）：

- **价格（必须）**：用于 mark-to-market（若周期末未能完全强平或需要评估未实现 PnL 口径）
- **其他（可选，但建议）**：合约规则/最小下单量/lot size、资金费相关字段（若要把资金费纳入账务闭环）

说明：本模块不定义“如何取价/取哪些字段”；只要求这些输入必须可回查、可落盘，并具备 `truth_quality/reason_code`。

---

## 1) 输入（Inputs）

LifecycleJudge 不读内存“感觉”，只接受明确输入：

- `run_id`
- `review_window`：
  - `review_index`（第几个轮回）
  - `tick_start` / `tick_end`
  - `ts_start_utc` / `ts_end_utc`（可选）
- `population_snapshot`（只读输入，来自系统当前活体列表 + 基因 ID 绑定）：
  - `agent_id_hash`
  - `genome_id_hash`（或等价标识）
  - `alive_flag`
- `metrics_snapshot`（关键：来自 Ledger/证据聚合后的输入）：
  - 每 agent 的最小指标集合（例如 ROI、max_drawdown、turnover、fees_paid、position_exposure_stats）
  - 以及每个指标的 `truth_quality` 与 `reason_code`（可全局也可逐字段）

> 说明：指标“怎么计算”不属于本模块职责；本模块只规定“必须有证据口径/真值质量标注”。

---

## 2) 输出（Evidence artifacts，append-only）

### 2.1 `lifecycle_events.jsonl`（必须，append-only）

每条记录代表一次对某个 agent 的裁决事件：

- `ts_utc`
- `run_id`
- `review_index`
- `tick_end`
- `record_type`: `lifecycle_event`
- `agent_id_hash`
- `genome_id_hash`
- `decision`: `KEEP | DEATH | REPRODUCE`
- `decision_reason_codes`: `[ ... ]`（词表冻结，additive-only）
- `metrics_used`: `{ ... }`（只包含本次裁决实际读取的指标子集）
- `metrics_truth_quality`: `ok | degraded | unknown`
- `metrics_truth_reasons`: `[ ... ]`
- `pre_settlement_action`（可选）：当周期末需要强平时，记录请求的动作摘要（例如 `{"type":"flatten","scope":"system_flatten","reason":"death_or_reproduce_settlement"}`）
- `pre_settlement_evidence_refs`（可选）：强平入册证据引用（例如指向 `order_attempts.jsonl` / `order_status_samples.jsonl` 的路径与行号范围）

### 2.2 `lifecycle_judge_report.json`（必须）

用于 run-end 审查：

- `run_id`
- `review_index`
- `contract_version`
- `verdict`: `PASS | NOT_MEASURABLE | FAIL`
- `summary_counts`：
  - `alive_before`
  - `death_count`
  - `reproduce_count`
  - `keep_count`
  - `not_measurable_count`
- `notes`（可选）

---

## 3) 规则与可配置项（Rules）

本模块允许存在“生态围栏参数”，但必须显式配置并落盘（不可隐式硬编码）：

- `death_policy`（示例）：
  - `bottom_k_percent`（周期末淘汰比例）
  - `min_roi_threshold`（可选：资金耗尽/破产线）
- `reproduction_policy`（示例）：
  - `top_k_percent`
  - `min_roi_threshold`
  - `offspring_count_per_parent`（可选）

> 关键：这些参数属于生命周期层，允许阈值存在；但不得被决策链路引用。

---

## 3.5) 推荐编排顺序（runner orchestration, recommended）

你提出的顺序可以冻结为默认编排（本版本先不引入审计模块介入）：

1) **周期内信息获取**：BrokerTrader 在每周期开始/每 tick 获取交易所实时信息并落盘（价格等）
2) **计算阶段（pre-settlement metrics）**：基于 BrokerTrader/ledger 的可回查事实生成 `metrics_snapshot`
3) **结算/归零阶段（system-level）**：
   - BrokerTrader 执行 `system_flatten`（强平/归零风险敞口，正常入册）
   - 系统钱包吸收/调整资金（system_reserve absorb），并落盘可回查证据
4) **审判阶段（LifecycleJudge）**：基于结算后的指标做 death/reproduce/keep 裁决，并落盘死亡清单（`lifecycle_events.jsonl`）
5) **执行阶段（runner/SystemManager）**：
   - 死亡 Agent：不再接受其委托（由交易员拒绝/忽略，且可审计）
   - 繁殖 Agent：初始化资金必须等于“分裂后资金”（本地分配视图），并在 population snapshot 中更新

说明：如果未来要加“周期末审计”，只需在 runner 编排中插入 ExchangeAuditor.run()，不需要修改本模块功能。

---

## 4) execution_world 的 NOT_MEASURABLE 策略（hard）

当指标真值不足以支持裁决时（例如 bills/fills 不可用且无法证明完整性）：

- 允许输出 `metrics_truth_quality=degraded/unknown`
- 对该 review_window 的裁决必须降级为：
  - `decision=KEEP`（保守，不做繁殖/淘汰），并在 `lifecycle_judge_report.json` 给出 `verdict=NOT_MEASURABLE`
  - 或者按项目策略：直接 `FAIL`（若该阶段必须做生命周期裁决）

本合同不强制选择哪种策略，但要求**策略必须在 runner 侧显式配置并落盘**，不得默默发生。

---

## 5) 最小 PROBE（用于锁版前验收）

目标：证明该模块的“输入依赖、输出落盘、append-only、裁决可复核”。

最小要求：
- 给定一个小的 `population_snapshot + metrics_snapshot`（可脱敏、可 mock，但必须带 truth_quality）
- 产出：
  - `lifecycle_events.jsonl`
  - `lifecycle_judge_report.json`
  - `FILELIST.ls.txt` + `SHA256SUMS.txt`

---

## 6) Freeze（接口冻结）

通过验收后冻结：
- `lifecycle_events.jsonl` 与 `lifecycle_judge_report.json` schema
- `decision_reason_codes` 词表（additive-only）
- `contract_version`

破坏性变更必须：
- 升级 `contract_version`
- 重跑最小 PROBE 并更新 Research 文档索引


