# V11 Step 61 — Compare Bundle Index (fact-only) — Implemented in Quant — 2025-12-30

目的：记录 Step61 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP61_COMPARE_BUNDLE_INDEX_CONTRACT_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step61 index compare_bundle.json (fact-only)`
- **Commit (short)**: `8e97edc`
- **Commit (full)**: `8e97edcfd02913c9a3e81a76f380dc384dbb7c33`

新增脚本（Quant）：
- `tools/index_compare_bundles.py`
- `tools/verify_step61_compare_bundle_index.py`

---

## 2) 行为与口径（事实）

索引脚本：
- 输入：`scan_root`（目录）
- 递归扫描：`scan_root` 下所有 `compare_bundle.json`
- 输出：`compare_bundle_index.json`（fact-only）
- 原则：只摘录 Step59 bundle 字段，不新增指标、不写解释
- `comparability.passed=false` 的 bundle 仍会被收录（NOT_MEASURABLE 风格）

验证脚本：
- 校验 index schema 完整性
- 校验 `bundle_count == len(bundles)`
- 校验 `evidence_refs` 格式与数量约束（至少覆盖所有 bundles）

Exit codes（事实）：
- `index_compare_bundles.py`：PASS=0；FAIL=2
- `verify_step61_compare_bundle_index.py`：PASS=0；FAIL=1

---

## 3) evidence_refs（事实）

索引产物的 `evidence_refs` 至少对每个 bundle 提供一条引用：
- `file`
- `sha256_16`
- `purpose`

---

## 4) 示例复核入口（写实）

示例命令（在 Quant）：

```text
python3 tools/index_compare_bundles.py runs_step53 --output compare_bundle_index.json
python3 tools/verify_step61_compare_bundle_index.py compare_bundle_index.json
```


