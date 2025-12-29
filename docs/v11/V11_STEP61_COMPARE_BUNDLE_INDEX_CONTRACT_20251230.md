# V11 Step 61 — Compare Bundle Index Contract (fact-only) — SSOT — 2025-12-30

目的：把散落在不同 run_dir/compare_dir 下的 `compare_bundle.json` 聚合成一个**可查询的事实索引产物**：`compare_bundle_index.json`。  
该索引用于批量检索与归档，不做解释、不做“好坏排序”，只提供可过滤字段。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 59：`compare_bundle.json` contract（fact-only）
- Step 60：compare_bundle 进入 run-end/CI evidence chain

---

## 1) 输入/输出（冻结）

输入：
- 一个根目录（例如 `runs/`、`runs_step53/`、或任意包含多个 compare_dir 的目录）
- 扫描该目录下所有 `compare_bundle.json`

输出：
- `compare_bundle_index.json`（fact-only）

---

## 2) compare_bundle_index.json schema（冻结，最小）

必含字段：
- `generated_at_utc`: string
- `index_id`: string（建议短 hash）
- `scan_root`: string（被扫描的根目录）
- `bundle_count`: int
- `bundles`: list[object]
  - `bundle_path`: string（相对 scan_root 或工作目录的路径）
  - `bundle_sha256_16`: string
  - `bundle_id`: string
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
  - `diff_summary`: object（摘录 Step59，不新增指标）
    - `decision_intent_counts_total_diff`（同 Step59）
    - `c_probe_stats`（同 Step59）
- `evidence_refs`: list[object]
  - 至少回指每个 `compare_bundle.json`（file + sha256_16 + purpose）

禁止：
- ROI/收益解释、因果推断、策略好坏判断
- 新增与 Step59/Step53 不一致的 diff 指标
- 对 bundles 做“排序结论”（可以按时间排序输出，但不得写解释性结论）

---

## 3) evidence_refs（硬）

`evidence_refs` 至少包含：
- 对每个 bundle 的引用（file + sha256_16 + purpose）

说明：
- Step61 索引本身是“聚合视图”，不强制包含 line_range；如后续需要加速追溯，可 additive-only 扩展。

---

## 4) Exit codes（建议）

- PASS → exit 0（index 生成成功且 schema 完整）
- FAIL → exit 2（扫描根目录不存在、JSON 解析失败、hash 计算失败、schema 缺失）

注意：
- `comparability.passed=false` 不应导致 index 失败（NOT_MEASURABLE 风格，仍应收录并写实 reason）。

---

## 5) Quant 最小验收（必须）

Quant 必须提供：
- 生成脚本：`tools/index_compare_bundles.py`（或等价命名）
- （推荐）校验脚本：`tools/verify_step61_compare_bundle_index.py`
- 最小验收：在 CI fixtures 或本地 runs 上运行 index 与 verify，通过 PASS


