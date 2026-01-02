# V12 SSOT — Modeling Docs Pipeline + Genome Alignment Table — 2026-01-01

目标：把 “scanner 结果 → tools 验证（含可选交易验证）→ 确认可作为对齐维度 → 写入建模文档（SSOT）→ 基因维度重构” 的链路冻结为可验收、可复核的产物结构，避免基因设计变成主观叙事。

本文件 additive-only。

---

## 1) Pipeline definition（冻结）

V12 的建模链路按顺序冻结为四段：

1) **事实层（Scanner evidence）**：run_dir 内的可回放证据  
2) **验证层（Tools verification）**：对事实层证据做 fail-closed 验证（含可选交易验证）  
3) **对齐层（Genome Alignment Table）**：确认“哪些字段/维度可作为对齐维度”，并形成可机读表  
4) **建模层（Modeling SSOT）**：把通过验证且可对齐的内容转写为“参数空间/枚举/限制/NOT_MEASURABLE 规则”的冻结文档  

说明（冻结）：
- **没有通过 tools 验证的 schema/字段，不得进入建模文档**（只能记录为候选/NOT_MEASURABLE）。
- “交易验证”不是 v0 的硬要求，但必须预留为 v1/v2 的验证方式（例如通过最小 one-shot 写探针验证某些字段的真实可用性/约束）。

基因后置原则（冻结）：
- **基因维度设计/重构必须后置**：只有当世界扫描器按阶段分批实现、并且相关证据通过 tools 验证、建模文档（SSOT）完成并验收后，才允许开始基因维度设计/重构。
- 任何早于上述门槛的“基因维度扩张”，都必须被视为 NOT_READY（避免在未被世界事实约束前引入主观旋钮）。

新维度准入 gate（必须可消融验证，冻结）：
- 原则：任何“新维度/新维度集”（包括你说的未知扰动/乌云类参数）若要进入决策输入合同，必须先证明它是**可审计、可测、可消融**的；否则默认判定为建模缺陷或无效维度。
- 最小准入条件（必须全部满足）：
  - **Evidence**：该维度在证据中可定位（字段来源、单位/类型、mask/quality/reason_code）且可回放
  - **Measurability**：在目标 truth_profile 下有稳定的可测比例（长期 mask=0 需要解释并可能拒绝准入）
  - **Ablation**：至少完成一次可复现的消融对照（dimension_on vs dimension_off），并能给出统计上可检出的差异或明确判定“无效”
  - **Fail-closed**：若 ablation 不可执行/不可测，必须 NOT_MEASURABLE，并禁止把该维度加入决策合同

### 1.1 Candidate dim: “Cloud intensity” (unknown semantics, measurable strength)（冻结，v0）

动机（冻结）：
- 我们允许引入一个“语义未知”的候选维度（比喻为“一朵乌云”），但它**只能**作为“扰动强度可测”的可控旋钮进入实验；它不得成为万能解释，也不得破坏可审计性。

定义（冻结，candidate-only，不等价于 genome schema）：
- 维度名：`cloud_intensity`
- 语义：**未知**（不做因果解释）；仅代表“外生扰动/不可解释因素”的强度标量
- 类型：`float`
- 范围（有界，冻结）：`0.0 <= cloud_intensity <= 1.0`
- 可测性（冻结）：
  - 可测：`cloud_mask = 1` 且 `cloud_reason_codes = []`
  - 不可测：`cloud_mask = 0` 且 `cloud_intensity = null` 且 `cloud_reason_codes` 非空（例如 `not_measurable:cloud_intensity_source_missing`）
- 证据落盘（冻结）：
  - `decision_trace.jsonl` 中必须写入：`cloud_intensity`, `cloud_mask`, `cloud_reason_codes`
  - `run_manifest.json` 中必须写入：`ablation.cloud.enabled` 与 `ablation.cloud.mode`（`on|off`）
- 消融（冻结，必须）：
  - `cloud` 必须支持 `on/off` 对照；`off` 时必须满足：
    - `cloud_mask=0`，`cloud_intensity=null`，并写入 `cloud_reason_codes=["ablation:cloud_off"]`
  - 任何无法进行消融的实现，一律视为 NOT_READY（不得进入决策输入合同）
- 退火/衰减（可选，冻结为可扩展结构）：
  - 允许在 manifest 记录：`ablation.cloud.schedule`（例如 `constant` / `linear_anneal`），但 v0 不强制实现

收敛失败的“硬观测”建议（冻结为观测 vocabulary，具体计算可后置）：
- 目的：防止 `cloud_intensity` 让系统变成“不可收敛噪声机”
- 推荐至少记录以下指标到 `run_manifest.json.observations`（字段可追加，不可删除/改义）：
  - `policy_switch_rate`（策略/行为切换率）
  - `decision_entropy`（决策分布熵的时间均值/趋势）
  - `cluster_stability`（簇稳定度/一致性指标）
  - `effective_rank`（高维表达的有效秩/坍缩度 proxy）
  - `not_measurable_ratio_cloud`（cloud 不可测比例）

补充：REST vs WebSocket 的“对齐语义”（冻结）
- **基因维度/建模维度不直接对齐传输层（REST/WS）**，而是对齐我们冻结的 **canonical schema**（例如 `market_snapshot.jsonl` 的字段与 mask 纪律）。
- REST 与 WS 允许返回不同字段/不同更新频率，但必须映射到同一个 canonical schema：
  - 可得 → 写值
  - 不可得/缺失 → `null + reason_code`（mask=0），不得伪造 0
- 事件驱动（WS）是“采样机制”的升级，不是“维度语义”的升级；维度语义升级必须通过 SSOT additive-only 冻结。

---

## 2) Required outputs（冻结）

### 2.1 Scanner outputs (facts)

必须存在（引用 Scanner SSOT）：
- `okx_api_calls.jsonl`
- `market_snapshot.jsonl`
- `scanner_report.json`
- `errors.jsonl`

前置门槛（冻结）：
- 只有当 Scanner 在对应 run 中产出 **schema verification passed**（见 `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md` 的 §6），该 run 的 `market_snapshot.jsonl` 才允许被采信进入建模层（Modeling SSOT）与基因对齐表生成。
- 若 verification 未通过：必须将该 run 视为 NOT_MEASURABLE（schema_not_verified），不得继续生成“可采信的建模结论”。

### 2.2 Modeling SSOT outputs (docs)

V12 必须产生至少两类 SSOT 文档（additive-only）：

- **Market Feature Contract (E-dims)**：
  - 固定维度（或固定字段集）定义
  - 每个字段的：来源 endpoint、单位、精度、mask/quality/reason_code 规则

- **Exchange API Parameter Spaces**：
  - 至少覆盖：`POST /trade/order`（下单参数空间）
  - 字段：type、required/conditional、enum、语义、与 `BTC-USDT-SWAP` 的适用性
  - 明确：哪些字段是“Agent 表达空间”，哪些是“系统默认/派生”，哪些由 gate 决策

备注：
- OKX 的下单参数空间目前以 V11 SSOT（OKX 合约规则 §12）为参照；V12 可在自身目录补充更严格的冻结版（只追加，不覆盖）。

### 2.3 Genome Alignment Table（可机读产物，冻结）

必须生成一个机器可读文件（由 scanner 或独立生成器输出）：

- 文件名建议：`genome_alignment_table.json`
- 建议同时在 `docs/v12/` 提供一份 **template** 作为冻结格式入口（用于 code review 与 diff）：
  - `docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json`
- 最小字段（语义冻结）：
  - `exchange`（e.g. `okx`）
  - `inst_id`（must be `BTC-USDT-SWAP` for v0）
  - `source_versions`（引用哪些 SSOT/contract 版本）
  - `order_api_parameter_space`（字段列表）
  - `alignment`（array of records），每条至少包含：
    - `field_name`
    - `field_type`
    - `required_rule`（required/conditional/optional + 条件描述）
    - `enum_values`（若有）
    - `agent_expressible`（bool）
    - `system_default_or_derived`（bool）
    - `gate_controlled`（bool）
    - `not_measurable_rules`（array[string]）
    - `evidence_sources`（array[string]，例如 endpoint 名称或 SSOT 引用）

冻结解释（v0）：
- Alignment table **不是 genome 设计**：它只回答“Agent 表达空间/系统默认空间/gate 控制空间”分别有哪些字段，避免出现“悬空旋钮”。
- `order_api_parameter_space` 允许在 v0 先由 SSOT（V11 OKX 合约规则 §12）提供事实锚点；后续可由 scanner/feature scanner 增量验证并补齐生态 fences（限速/上限/禁用）。

硬规则（hard）：
- **禁止发明字段**：Genome/Decision 维度若声称可输出某下单参数，必须能在该表中找到同名/等价语义字段。
- **mask 纪律**：对不可测/不可用字段，必须提供 mask/NOT_MEASURABLE 规则；不得用 0 伪装。

---

## 3) Acceptance (M1)（冻结）

PASS 条件：
- 能从 Scanner run_dir 推导出一份 `genome_alignment_table.json`（或等价文件）且内容自洽
- 表中每个字段都能回指证据来源（endpoint 或 SSOT）
- 对“接口不可用/限速/模式差异”的情况，有明确 NOT_MEASURABLE 规则与 reason_code vocabulary

建议的“悬空旋钮扫描”（冻结入口）：
- 对任意一个 **Phase2+Phase3 verdict=PASS** 的 broker run_dir，运行对齐漂移扫描工具：
  - `python3 tools/v12/scan_alignment_drift_v0.py --run_dir <BROKER_RUN_DIR> --template docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json`
- 输出 `alignment_drift_report.json`（或 stdout）必须可机读，且：
  - `unmapped_attempt_fields` 为空（否则说明存在“悬空旋钮”或 evidence schema 漂移，需先修正对齐表/证据合同）
  - 若发现 `important_non_order_knobs_observed`（例如 leverage_*），必须在下一次 v0+ 里为其补充“非 order 参数空间”的对齐记录（additive-only）

FAIL 条件：
- Genome/Decision 输出维度中出现无法在 alignment table 映射的“悬空旋钮”
- 关键字段被系统静默默认且无法审计（例如 leverage 等）

---

## 4) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- Scanner E schema: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- V11 Agent probing model: `docs/v11/V11_SSOT_AGENT_PROBING_AND_PROXY_TRADER_MODEL_20260101.md`
- V11 OKX order parameter anchor: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`（§12）


