# V11 Step 53 — Ablation Compare Report (ablation_compare.json, fact-only) — 2025-12-30

目的：在 Step 51 已产出每次 run 的 `ablation_summary.json` 基础上，新增一个**跨 run 的对照聚合产物**：
- `ablation_compare.json`
- 仅做“事实差异统计”（counts / ranges /一致性检查），不做解释与结论
- 必须 evidence_refs 可复核，符合 Step 46 Evidence Gate Bundle

前置：
- Step 46：Evidence Gate Bundle（evidence_refs 可复核）
- Step 50：ablation_experiment 模板（对照实验控制变量）
- Step 51：ablation_summary.json（单 run 事实统计）

---

## 1) 输入/输出（冻结）

输入：
- run_dir_A/ablation_summary.json（通常 C_off）
- run_dir_B/ablation_summary.json（通常 C_on）

输出（写入一个新目录或其中一个 run_dir；推荐新目录）：
- `ablation_compare.json`

---

## 2) ablation_compare.json schema（冻结，最小）

必含字段：
- `generated_at_utc`: string
- `compare_id`: string（建议短 hash）
- `left`: object
  - `run_id`
  - `variant`
  - `summary_path`
  - `sha256_16`（summary 文件 hash 前16）
- `right`: object（同 left）
- `comparability`: object
  - `passed`: bool
  - `reason`: string|null
  - `checked_fields`: list[string]
- `diff`: object（事实差异）
  - `decision_intent_counts_total_diff`: object
    - `open_delta`: int
    - `close_delta`: int
    - `hold_delta`: int
    - `total_delta`: int
  - `c_probe_stats`: object
    - `left_mode`: string
    - `right_mode`: string
    - `mask_1_count_left`: int
    - `mask_1_count_right`: int
    - `mask_1_count_delta`: int
    - `value_min_left`: float|null
    - `value_min_right`: float|null
    - `value_max_left`: float|null
    - `value_max_right`: float|null
- `evidence_refs`: list[object]
  - 至少回指两份 `ablation_summary.json`

禁止：
- ROI/收益解释、因果推断、策略好坏判断
- 任何“结论性文本”

---

## 3) 可比性规则（硬，必须 fail-closed）

必须检查两份 summary 的 `ablation_experiment`：
- 除 `variant` 外，字段必须完全一致（Step 50 的“控制变量法”）
- `feature_contract_version` 必须一致
- `evidence_gate_bundle.bundle_name/bundle_version/steps_included` 必须一致

不满足：
- `comparability.passed=false`
- 必须给出 `reason`
- 产物仍可生成，但必须明确标记不可比（用于 CI 可选；若作为 gate，可直接 FAIL）

---

## 4) 最小验收（Quant 落地必须达成）

必须提供脚本与断言：
- 输入：Step 51 产生的两次 run_dir（C_off/C_on）
- 输出：`ablation_compare.json`
- 验证：
  - schema 字段齐全
  - `comparability.passed == true`
  - `evidence_refs` 可通过 Step 46 bundle 复核


