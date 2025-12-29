# V11 Step 51 — Minimal Ablation Run + Fact Summary (C_off vs C_on) — 2025-12-30

目的：把 Step 50 的“对照实验模板”推进到真正可复核的最小实验闭环：
- 跑通两次 run：`C_off` vs `C_on`
- 两次 run 除 `variant` 外参数完全一致（由 Step 50 保证）
- 新增一个**事实统计产物**：`ablation_summary.json`（不做解释，只做可复核统计）

前置：
- Step 46：Evidence Gate Bundle
- Step 49：C ablation switch
- Step 50：run_manifest.ablation_experiment

---

## 1) 运行要求（冻结）

必须产生两份 run_dir（建议命名规则）：
- `runs/<timestamp>_C_off/`
- `runs/<timestamp>_C_on/`

两次 run 的 `run_manifest.ablation_experiment` 必须满足：
- 除 `variant` 外字段完全一致（Step 50）
- `variant` 分别为 `C_off` / `C_on`

---

## 2) ablation_summary.json（冻结 schema，事实统计）

每个 run_dir 内新增：
- `ablation_summary.json`

字段（最小必含）：
- `run_id`: string
- `generated_at_utc`: string
- `ablation_experiment`: object（从 manifest 原样复制，至少含必填字段）
- `feature_contract_version`: string
- `evidence_gate_bundle`: object
  - `bundle_name`
  - `bundle_version`
  - `steps_included`
- `tick_range`: object
  - `tick_start`: int（通常 1）
  - `tick_end`: int
  - `tick_count`: int

事实统计（最小）：
- `decision_intent_counts_total`: object
  - `open`: int
  - `close`: int
  - `hold`: int
  - `total`: int
- `c_probe_stats`: object
  - `c_feature_mode`: "C_off"|"C_on"
  - `c_prev_net_intent_mask_1_count`: int
  - `c_prev_net_intent_mask_0_count`: int
  - `c_prev_net_intent_value_min`: float|null
  - `c_prev_net_intent_value_max`: float|null

来源（证据化，必须有 evidence_refs）：
- `evidence_refs`: list[object]（遵循 Step 41-46 的标准）
  - 至少回指：
    - `run_manifest.json`
    - `decision_trace.jsonl`（用于 intent_counts 与 C 统计）

禁止：
- 在 summary 中加入“收益好/坏”“因果解释”等主观结论

---

## 3) 最小验收（Quant 落地必须达成）

必须提供脚本或 CI 检查：
- 两个 run_dir 都存在 `ablation_summary.json`
- 两份 summary 的 `ablation_experiment` 除 `variant` 外一致
- `C_off` 的 `c_prev_net_intent_mask_1_count == 0`（全部 mask=0）
- `C_on` 的 `c_prev_net_intent_mask_1_count >= 1`（至少从 tick=2 起有有效值）
- summary 的 `evidence_refs` 可通过 Evidence Gate Bundle（Step 46）复核


