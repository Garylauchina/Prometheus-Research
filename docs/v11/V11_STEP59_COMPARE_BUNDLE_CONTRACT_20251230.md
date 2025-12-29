# V11 Step 59 — Compare Bundle Contract (fact-only) — SSOT — 2025-12-30

目的：把 Step53 的 `ablation_compare.json` 从“散落的对照产物”提升为**研究侧可消费的标准入口**：生成一个轻量、fact-only 的 `compare_bundle.json`（或等价命名），用于汇总/归档/索引，而不引入任何解释或结论。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 46：Evidence Gate Bundle（evidence_refs 可复核）
- Step 53：`docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_20251230.md`
- Step 54：compare 进入 run-end evidence gate
- Step 58：fixtures verifier + CI gate

---

## 1) 输入/输出（冻结）

输入：
- 一个 compare 目录（包含 `ablation_compare.json`）

输出（写入同目录或指定输出目录）：
- `compare_bundle.json`（fact-only）

---

## 2) compare_bundle.json schema（冻结，最小）

必含字段：
- `generated_at_utc`: string
- `bundle_id`: string（建议短 hash）
- `source`: object
  - `ablation_compare_path`: string
  - `ablation_compare_sha256_16`: string
- `left`: object
  - `run_id`: string
  - `variant`: string
- `right`: object（同 left）
- `comparability`: object
  - `passed`: bool
  - `reason`: string|null
- `diff_summary`: object（fact-only 摘要，不新增指标）
  - `decision_intent_counts_total_diff`: object
    - `open_delta`: int
    - `close_delta`: int
    - `hold_delta`: int
    - `total_delta`: int
  - `c_probe_stats`: object
    - `mask_1_count_left`: int
    - `mask_1_count_right`: int
    - `mask_1_count_delta`: int
    - `value_min_left`: float|null
    - `value_min_right`: float|null
    - `value_max_left`: float|null
    - `value_max_right`: float|null
- `evidence_refs`: list[object]
  - 至少回指：
    - `ablation_compare.json`
    - 两份 `ablation_summary.json`

禁止：
- ROI/收益解释、因果推断、策略好坏判断
- 任何“结论性文本”
- 新增与 Step53 不一致的 diff 指标（Step59 只能“摘录/汇总”，不能“扩展口径”）

---

## 3) evidence_refs（硬）

`evidence_refs` 必须符合 Step46 的可复核规则（在 gate-on 环境中）：
- 至少包含 file + sha256_16 + purpose
- 若引用 `.jsonl` 文件，需要 line_range 的场景由 Step46 bundle 规则决定（本 Step 不新增要求）

---

## 4) Exit codes（建议）

建议工具语义（面向批处理/CI）：
- PASS → exit 0（bundle 生成成功，且 schema 完整）
- FAIL → exit 2（输入缺失/解析失败/schema 缺失/hash 失败）

注意：`comparability.passed=false` 不应导致 bundle 生成失败；bundle 仍应生成并写实 reason（NOT_MEASURABLE 风格）。

---

## 5) Quant 最小验收（必须）

Quant 必须提供：
- 生成脚本（例如 `tools/generate_step59_compare_bundle.py`）
- 最小校验脚本（可选，但推荐）：`tools/verify_step59_compare_bundle.py`
- CI/本地 fixture 验收：能从 Step53/54 产物生成 bundle，并验证 schema 与 evidence_refs 存在性


