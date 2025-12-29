# V11 Step 52 — Feature Dim ↔ DecisionEngine ↔ Genome Schema Alignment (Fail-Closed) — 2025-12-30

目的：冻结 **Feature/Probe Contract（维度与顺序）**、**DecisionEngine 输入维度**、**Genome 权重布局** 的一致性，避免出现“代码能跑但输入错位”的隐性灾难。

背景：Step 48 将 feature contract 扩展到 13 维；如果 DecisionEngine 或 Genome 仍按旧维度/旧布局工作，会导致：
- 输入向量截断/补零造成伪结论
- 维度错位导致策略失真且难以审计

---

## 1) 一致性三元组（冻结）

必须同时满足：
- `feature_contract_version`（例如 `V11_FEATURE_PROBE_CONTRACT_20251230.2`）
- `feature_dimension`（例如 13）
- `decision_input_dim`（必须 == feature_dimension）
- `genome_schema_version`（必须声明其权重布局与 input_dim 匹配）

---

## 2) Fail-Closed 校验点（Quant 落地必须达成）

在 runner 启动 preflight（建议在生成 run_dir / manifest 之后、进入 tick loop 之前）执行硬校验：
- 从 `features_contract` 读取 `FEATURE_DIMENSION` 与 `feature_contract_version`
- 从 DecisionEngine/模型构造处读取其期望 `input_dim`
- 从 Genome schema 读取其权重形状/输入维度（或显式字段）

硬规则：
- 若 `decision_input_dim != feature_dimension` → **FAIL（exit 非0）**
- 若 Genome 权重与 `feature_dimension` 不匹配 → **FAIL**
- 必须写入 `errors.jsonl`（error_type 建议：`feature_dim_mismatch`）并在 manifest 标记 stopped/fail

---

## 3) Manifest 记录（冻结）

`run_manifest.json` 必须记录（machine-readable）：
- `feature_contract_version`
- `feature_dimension`
- `decision_input_dim`
- `genome_schema_version`
- `alignment_check`：
  - `passed`: bool
  - `reason`: string|null

---

## 4) 最小验收（fixture/CI）

必须新增一个负例（必须 FAIL）：
- 人为制造 `decision_input_dim != feature_dimension`（例如在测试构造一个 fake engine，或临时切换一个旧 contract）
- 预期：preflight 直接 FAIL，并写入 errors.jsonl + manifest 标记

必须保留一个正例（必须 PASS）：
- `decision_input_dim == feature_dimension == 13`
- Genome 权重形状匹配

---

## 5) 版本纪律（提醒）

任何 feature 维度变更（例如 13 → 14）都必须同步：
- bump `feature_contract_version`
- bump `genome_schema_version`
- bump pool namespace（如果涉及演化池兼容性）
- 并让 Step 52 的 alignment check 与 fixtures 更新后通过


