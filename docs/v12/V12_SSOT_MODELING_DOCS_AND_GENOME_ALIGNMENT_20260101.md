# V12 SSOT — Modeling Docs Pipeline + Genome Alignment Table — 2026-01-01

目标：把 “scanner 结果 → 建模文档（SSOT）→ 基因维度重构” 的链路冻结为可验收、可复核的产物结构，避免基因设计变成主观叙事。

本文件 additive-only。

---

## 1) Pipeline definition（冻结）

V12 的建模链路分三层产物：

1) **事实层（Scanner evidence）**：run_dir 内的可回放证据  
2) **建模层（Modeling SSOT）**：把事实转写为“参数空间/枚举/限制/NOT_MEASURABLE 规则”的冻结文档  
3) **对齐层（Genome Alignment Table）**：把“接口参数空间”切分为：Agent 可表达、系统默认、gate 决策三类，并形成可机读表

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

硬规则（hard）：
- **禁止发明字段**：Genome/Decision 维度若声称可输出某下单参数，必须能在该表中找到同名/等价语义字段。
- **mask 纪律**：对不可测/不可用字段，必须提供 mask/NOT_MEASURABLE 规则；不得用 0 伪装。

---

## 3) Acceptance (M1)（冻结）

PASS 条件：
- 能从 Scanner run_dir 推导出一份 `genome_alignment_table.json`（或等价文件）且内容自洽
- 表中每个字段都能回指证据来源（endpoint 或 SSOT）
- 对“接口不可用/限速/模式差异”的情况，有明确 NOT_MEASURABLE 规则与 reason_code vocabulary

FAIL 条件：
- Genome/Decision 输出维度中出现无法在 alignment table 映射的“悬空旋钮”
- 关键字段被系统静默默认且无法审计（例如 leverage 等）

---

## 4) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- Scanner E schema: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- V11 Agent probing model: `docs/v11/V11_SSOT_AGENT_PROBING_AND_PROXY_TRADER_MODEL_20260101.md`
- V11 OKX order parameter anchor: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`（§12）


